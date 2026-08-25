"use client";

import { useEffect, useRef } from "react";
import { Terminal as XTerm } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";

import { terminalWsUrl } from "@/lib/wsUrl";

const CONTROL_PREFIX = "\x00";

export default function Terminal() {
  const containerRef = useRef<HTMLDivElement>(null);
  const statusRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const term = new XTerm({
      convertEol: true,
      fontSize: 13,
      cursorBlink: true,
      fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
      theme: {
        background: "#0d0f14",
        foreground: "#e6e8ee",
        cursor: "#6366f1",
        selectionBackground: "#3730a3",
      },
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(container);
    fit.fit();

    const setStatus = (text: string, cls: string) => {
      const el = statusRef.current;
      if (!el) return;
      el.textContent = text;
      el.className = cls;
    };

    setStatus("connecting…", "text-text-faint");
    const ws = new WebSocket(terminalWsUrl());
    ws.binaryType = "arraybuffer";

    const sendResize = () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(`${CONTROL_PREFIX}RESIZE:${term.cols},${term.rows}`);
      }
    };

    ws.onopen = () => {
      setStatus("connected", "text-pass");
      sendResize();
    };
    ws.onmessage = (ev) => {
      if (typeof ev.data === "string") {
        term.write(ev.data);
      } else {
        term.write(new Uint8Array(ev.data));
      }
    };
    ws.onclose = () => {
      setStatus("disconnected", "text-fail");
      term.write("\r\n\x1b[31m[connection closed]\x1b[0m\r\n");
    };
    ws.onerror = () => setStatus("connection error", "text-fail");

    const dataDisposable = term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) ws.send(data);
    });

    const resizeObserver = new ResizeObserver(() => {
      fit.fit();
      sendResize();
    });
    resizeObserver.observe(container);

    return () => {
      dataDisposable.dispose();
      resizeObserver.disconnect();
      ws.close();
      term.dispose();
    };
  }, []);

  return (
    <div className="h-full flex flex-col bg-black/40">
      <div className="px-3 py-1.5 border-b border-bg-border text-text-faint text-xs uppercase tracking-wide font-mono flex items-center gap-2">
        <span>Terminal</span>
        <span ref={statusRef} className="normal-case text-text-faint">
          connecting…
        </span>
      </div>
      <div ref={containerRef} className="flex-1 overflow-hidden px-2 py-1" />
    </div>
  );
}
