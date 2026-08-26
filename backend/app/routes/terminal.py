"""Real per-user terminal over WebSocket, backed by a PTY-attached shell.

Single-host, no container isolation yet (that's Phase 2) — this just spawns
a real shell process via ptyprocess, scoped to the user's own workspace
directory, and streams it to xterm.js on the frontend.
"""
import asyncio
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ptyprocess import PtyProcess

from app import pylabs_bridge as pb
from app.deps import get_current_user_ws

router = APIRouter()

SHELL = os.environ.get("LAB_SHELL", "/bin/bash")

# A raw NUL byte never appears in normal keyboard input from xterm.js, so it's
# a safe marker for out-of-band control messages (currently just resize) on
# the same text-frame channel as keystrokes.
CONTROL_PREFIX = "\x00"
RESIZE_PREFIX = "RESIZE:"


@router.websocket("/ws/terminal")
async def terminal_ws(websocket: WebSocket):
    user = get_current_user_ws(websocket)
    if user is None:
        await websocket.close(code=4401)
        return

    await websocket.accept()

    ws_dir = pb.workspace_dir_for(user.id)
    env = {**os.environ, "TERM": "xterm-256color"}
    proc = PtyProcess.spawn([SHELL], cwd=str(ws_dir), env=env, dimensions=(24, 80))

    loop = asyncio.get_event_loop()

    async def pump_output():
        """Read the PTY (blocking) in a thread, forward bytes to the socket."""
        while True:
            try:
                data = await loop.run_in_executor(None, proc.read, 4096)
            except EOFError:
                break
            if not data:
                break
            try:
                await websocket.send_bytes(data)
            except Exception:
                break

    reader_task = asyncio.create_task(pump_output())

    try:
        while True:
            msg = await websocket.receive()
            if msg["type"] == "websocket.disconnect":
                break

            text = msg.get("text")
            raw = msg.get("bytes")

            if text is not None:
                if text.startswith(CONTROL_PREFIX):
                    body = text[len(CONTROL_PREFIX):]
                    if body.startswith(RESIZE_PREFIX):
                        try:
                            cols_s, rows_s = body[len(RESIZE_PREFIX):].split(",")
                            proc.setwinsize(int(rows_s), int(cols_s))
                        except Exception:
                            pass
                    continue
                proc.write(text.encode())
            elif raw is not None:
                proc.write(raw)
    except WebSocketDisconnect:
        pass
    finally:
        reader_task.cancel()
        if proc.isalive():
            proc.terminate(force=True)
