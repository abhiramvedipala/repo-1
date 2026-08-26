"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function TopBar({ email }: { email: string }) {
  const [infoOpen, setInfoOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (!infoOpen) return;
    function onClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setInfoOpen(false);
      }
    }
    function onEscape(e: KeyboardEvent) {
      if (e.key === "Escape") setInfoOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      document.removeEventListener("keydown", onEscape);
    };
  }, [infoOpen]);

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
        <span className="text-text-faint text-xs ml-1 hidden sm:inline">Python → AI Engineering</span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-text-dim text-xs hidden sm:inline">{email}</span>
        <button
          onClick={onLogout}
          className="text-text-dim hover:text-text text-xs px-2 py-1 rounded hover:bg-bg-raised transition-colors"
        >
          Sign out
        </button>
        <button
          onClick={() => setInfoOpen((v) => !v)}
          aria-label="About this lab"
          aria-expanded={infoOpen}
          className={`h-7 w-7 rounded-full border flex items-center justify-center text-sm transition-colors ${
            infoOpen
              ? "text-accent border-accent bg-accent/10"
              : "text-text-dim border-bg-border hover:text-accent hover:border-accent"
          }`}
        >
          i
        </button>
      </div>

      {infoOpen && (
        <div
          ref={panelRef}
          className="absolute right-4 top-14 w-80 bg-bg-raised border border-bg-border rounded-lg shadow-xl p-4 z-20 text-sm origin-top-right animate-[fadeSlideIn_0.15s_ease-out]"
        >
          <div className="font-semibold mb-2">About this lab</div>
          <p className="text-text-dim leading-relaxed">
            A self-hosted, KodeKloud-style Python lab: 21 tasks across 5 phases, each with
            automated checks. Pick a task on the left, write code on the right, hit{" "}
            <span className="text-text">Check</span> to run real checks against your code.
          </p>
          <p className="text-text-faint text-xs mt-3 leading-relaxed">
            When you start a lab, you get a real, isolated VS Code environment — your own
            container, network-restricted to package registries only, with a countdown timer.
          </p>
        </div>
      )}
    </div>
  );
}
