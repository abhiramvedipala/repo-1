"use client";

import type { TaskSummary } from "@/lib/types";

export default function ProgressDots({
  tasks,
  activeTaskId,
  onSelect,
}: {
  tasks: TaskSummary[];
  activeTaskId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5 py-1">
      {tasks.map((t) => {
        const isActive = t.id === activeTaskId;
        const base = "h-2.5 w-2.5 rounded-full transition-all cursor-pointer";
        let cls = "bg-bg-border hover:bg-text-faint"; // not started
        if (t.status === "passed") cls = "bg-pass hover:bg-pass";
        if (isActive) cls += " ring-2 ring-accent scale-125";
        if (isActive && t.status !== "passed") cls = "bg-accent ring-2 ring-accent/40 scale-125";
        return (
          <button
            key={t.id}
            title={`${t.index}. ${t.title}`}
            onClick={() => onSelect(t.id)}
            className={`${base} ${cls}`}
          />
        );
      })}
    </div>
  );
}
