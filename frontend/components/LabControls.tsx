"use client";

import { useEffect, useState } from "react";
import type { LabStatus } from "@/lib/types";

function formatRemaining(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function LabControls({
  lab,
  starting,
  onStart,
  onStop,
}: {
  lab: LabStatus;
  starting: boolean;
  onStart: () => void;
  onStop: () => void;
}) {
  const [remaining, setRemaining] = useState(lab.remainingSeconds ?? 0);

  useEffect(() => {
    setRemaining(lab.remainingSeconds ?? 0);
  }, [lab.remainingSeconds, lab.status]);

  // tick the displayed countdown locally between status polls
  useEffect(() => {
    if (lab.status !== "running") return;
    const t = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
    return () => clearInterval(t);
  }, [lab.status]);

  const isRunning = lab.status === "running";
  const low = isRunning && remaining < 300; // last 5 minutes

  return (
    <div className="h-11 shrink-0 flex items-center justify-between px-3 border-b border-bg-border bg-bg-panel">
      <div className="flex items-center gap-2 text-xs">
        <span
          className={`h-2 w-2 rounded-full ${
            isRunning ? "bg-pass" : lab.status === "starting" ? "bg-accent animate-pulse" : "bg-text-faint"
          }`}
        />
        <span className="text-text-dim">
          {isRunning ? "Lab running" : lab.status === "starting" ? "Starting…" : "No lab session"}
        </span>
        {isRunning && (
          <span className={`font-mono ml-1 ${low ? "text-fail" : "text-text"}`}>{formatRemaining(remaining)}</span>
        )}
      </div>

      {isRunning ? (
        <button
          onClick={onStop}
          className="px-3 py-1 rounded-md border border-bg-border text-xs font-medium hover:border-fail hover:text-fail transition-colors"
        >
          Stop Lab
        </button>
      ) : (
        <button
          onClick={onStart}
          disabled={starting}
          className="px-3 py-1 rounded-md bg-accent hover:bg-accent-hover disabled:opacity-60 text-xs font-medium transition-colors"
        >
          {starting ? "Starting…" : "Start Lab"}
        </button>
      )}
    </div>
  );
}
