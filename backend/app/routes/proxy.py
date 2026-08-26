"""Reverse proxy that fronts a user's code-server container so it's never
exposed on a raw port to the browser — everything goes through our own
authenticated FastAPI route, keyed by an opaque per-session token.

code-server generates all its own asset/API paths relative to the current
request path (verified against a real container before writing this), so a
plain path-stripping proxy works: whatever comes after `/proxy/{token}/`
is forwarded byte-for-byte to the container.
"""
import asyncio

import aiohttp
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session as DbSession

from app.db import SessionLocal, get_db
from app.deps import get_current_user, get_current_user_ws
from app.models import LabSession, User

router = APIRouter()

_HOP_BY_HOP = {"connection", "keep-alive", "transfer-encoding", "content-encoding", "content-length", "date"}


def _resolve_session(token: str, user: User, db: DbSession) -> LabSession:
    sess = (
        db.query(LabSession)
        .filter(LabSession.session_token == token, LabSession.user_id == user.id)
        .first()
    )
    if sess is None or sess.status != "running" or not sess.container_ip:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no running lab session for this token")
    return sess


@router.api_route("/proxy/{token}", methods=["GET", "HEAD"])
async def proxy_root_redirect(token: str):
    # code-server's own relative-path assets assume a trailing slash as the base
    return RedirectResponse(url=f"/proxy/{token}/")


@router.api_route(
    "/proxy/{token}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_http(
    token: str,
    path: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: DbSession = Depends(get_db),
):
    sess = _resolve_session(token, user, db)
    target = f"http://{sess.container_ip}:{sess.container_port}/{path}"

    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", *_HOP_BY_HOP)}
    # Ask the upstream not to compress at all, rather than depend on httpx's
    # optional (not installed) brotli decoder to undo whatever the browser's
    # real Accept-Encoding negotiated — proxy and container are co-located,
    # so skipping compression here costs effectively nothing.
    headers["accept-encoding"] = "identity"
    body = await request.body()

    # We need the upstream status/headers before we can construct the
    # StreamingResponse, so send the request here (not closing the client
    # until the body has actually been streamed out below).
    upstream_client = httpx.AsyncClient(timeout=60.0)
    req = upstream_client.build_request(
        request.method, target, params=request.query_params, headers=headers, content=body
    )
    try:
        resp = await upstream_client.send(req, stream=True)
    except httpx.HTTPError as e:
        await upstream_client.aclose()
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"lab session unreachable: {e}")

    resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in _HOP_BY_HOP}

    async def body_stream():
        try:
            # aiter_bytes (not aiter_raw): httpx transparently decompresses
            # gzip/br here, which is why content-encoding/content-length
            # are stripped from resp_headers above — they'd no longer
            # match this decoded body.
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await resp.aclose()
            await upstream_client.aclose()

    return StreamingResponse(body_stream(), status_code=resp.status_code, headers=resp_headers)


@router.websocket("/proxy/{token}/{path:path}")
async def proxy_ws(websocket: WebSocket, token: str, path: str):
    user = get_current_user_ws(websocket)
    if user is None:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        sess = (
            db.query(LabSession)
            .filter(LabSession.session_token == token, LabSession.user_id == user.id)
            .first()
        )
    finally:
        db.close()

    if sess is None or sess.status != "running" or not sess.container_ip:
        await websocket.close(code=4404)
        return

    query = f"?{websocket.url.query}" if websocket.url.query else ""
    upstream_url = f"ws://{sess.container_ip}:{sess.container_port}/{path}{query}"

    # Accept the client side up front: auth + session are already verified,
    # so a failure connecting to the container from here on is a backend
    # problem, not a reason to reject the browser's handshake outright
    # (surfacing it as a clean close is far easier to debug than a bare
    # HTTP-level handshake rejection).
    await websocket.accept()

    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.ws_connect(upstream_url, timeout=10) as upstream:

                async def client_to_upstream():
                    try:
                        while True:
                            msg = await websocket.receive()
                            if msg["type"] == "websocket.disconnect":
                                break
                            if msg.get("text") is not None:
                                await upstream.send_str(msg["text"])
                            elif msg.get("bytes") is not None:
                                await upstream.send_bytes(msg["bytes"])
                    except WebSocketDisconnect:
                        pass
                    finally:
                        await upstream.close()

                async def upstream_to_client():
                    async for message in upstream:
                        if message.type == aiohttp.WSMsgType.TEXT:
                            await websocket.send_text(message.data)
                        elif message.type == aiohttp.WSMsgType.BINARY:
                            await websocket.send_bytes(message.data)
                        elif message.type in (
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            break

                done, pending = await asyncio.wait(
                    [asyncio.create_task(client_to_upstream()), asyncio.create_task(upstream_to_client())],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
