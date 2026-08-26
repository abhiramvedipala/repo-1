"use client";

import type { TaskSummary } from "@/lib/types";

/** Thin colored bar segments spanning the full width, one per task —
 * matches the reference platform's top-of-panel progress bar rather than
 * a loose row of dots. */
export default function ProgressBar({
  tasks,
  activeTaskId,
  onSelect,
}: {
  tasks: TaskSummary[];
  activeTaskId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex gap-[3px] w-full">
      {tasks.map((t) => {
        const isActive = t.id === activeTaskId;
        let cls = "bg-bg-border hover:bg-text-faint/60"; // not started
        if (t.status === "passed") cls = "bg-pass hover:bg-pass";
        if (isActive) cls = "bg-accent hover:bg-accent";
        return (
          <button
            key={t.id}
            title={`${t.index}. ${t.title}`}
            onClick={() => onSelect(t.id)}
            aria-current={isActive}
            className={`flex-1 h-[5px] rounded-full cursor-pointer transition-all duration-200 ${cls} ${
              isActive ? "h-[7px] shadow-[0_0_6px_rgba(99,102,241,0.7)]" : ""
            }`}
          />
        );
      })}
    </div>
  );
}
