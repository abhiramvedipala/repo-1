"use client";

import { useState } from "react";

export default function HintBox({ hint }: { hint: string }) {
  const [open, setOpen] = useState(false);
  if (!hint) return null;
  return (
    <div className="mt-4 border border-bg-border rounded-md overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full text-left px-3 py-2 text-xs text-text-dim hover:text-text bg-bg-raised flex items-center justify-between"
      >
        <span>💡 Hint</span>
        <span className="text-text-faint">{open ? "▲" : "▼"}</span>
      </button>
      {open && <div className="px-3 py-2 text-sm text-text-dim leading-relaxed">{hint}</div>}
    </div>
  );
}
