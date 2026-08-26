"use client";

import type { CheckResult } from "@/lib/types";

export type CheckState = "idle" | "checking" | "done";

export default function Checklist({
  state,
  results,
}: {
  state: CheckState;
  results: CheckResult[] | null;
}) {
  if (state === "idle" && !results) {
    return (
      <div className="text-text-faint text-xs italic mt-2 animate-[fadeSlideIn_0.2s_ease-out]">
        Run Check to see results here.
      </div>
    );
  }

  if (state === "checking") {
    return (
      <div className="mt-3 space-y-2">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="h-4 bg-bg-raised rounded animate-pulse animate-[fadeSlideIn_0.2s_ease-out_backwards]"
            style={{ width: `${70 - i * 10}%`, animationDelay: `${i * 60}ms` }}
          />
        ))}
      </div>
    );
  }

  if (!results) return null;

  return (
    <div className="mt-3 space-y-2">
      {results.map((r, i) => (
        <div
          key={i}
          className="text-sm animate-[fadeSlideIn_0.3s_ease-out_backwards]"
          style={{ animationDelay: `${i * 50}ms` }}
        >
          <div className="flex items-start gap-2">
            <span
              className={`inline-block animate-[popIn_0.25s_ease-out_backwards] ${r.passed ? "text-pass" : "text-fail"}`}
              style={{ animationDelay: `${i * 50 + 120}ms` }}
            >
              {r.passed ? "✓" : "✗"}
            </span>
            <span className="text-text">{r.label}</span>
          </div>
          {!r.passed && r.message && (
            <div className="ml-5 text-xs text-fail/80 mt-0.5 font-mono leading-relaxed">{r.message}</div>
          )}
        </div>
      ))}
    </div>
  );
}
