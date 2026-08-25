"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function TopBar({ email }: { email: string }) {
  const [infoOpen, setInfoOpen] = useState(false);
  const router = useRouter();

  async function onLogout() {
    await api.logout();
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="relative h-12 shrink-0 flex items-center justify-between px-4 border-b border-bg-border bg-bg-panel">
      <div className="flex items-center gap-2">
        <div className="h-6 w-6 rounded bg-accent flex items-center justify-center text-xs font-bold">L</div>
        <span className="font-semibold tracking-tight text-sm">Lab Platform</span>
        <span className="text-text-faint text-xs ml-1">Python → AI Engineering</span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-text-dim text-xs">{email}</span>
        <button
          onClick={onLogout}
          className="text-text-dim hover:text-text text-xs px-2 py-1 rounded hover:bg-bg-raised transition-colors"
        >
          Sign out
        </button>
        <button
          onClick={() => setInfoOpen((v) => !v)}
          aria-label="About this lab"
          className="h-7 w-7 rounded-full border border-bg-border flex items-center justify-center text-text-dim hover:text-accent hover:border-accent transition-colors text-sm"
        >
          i
        </button>
      </div>

      {infoOpen && (
        <div className="absolute right-4 top-14 w-80 bg-bg-raised border border-bg-border rounded-lg shadow-xl p-4 z-20 text-sm">
          <div className="font-semibold mb-2">About this lab</div>
          <p className="text-text-dim leading-relaxed">
            A self-hosted, KodeKloud-style Python lab: 21 tasks across 5 phases, each with
            automated checks. Pick a task on the left, write code on the right, hit{" "}
            <span className="text-text">Check</span> to run real checks against your code.
          </p>
        </div>
      )}
    </div>
  );
}
