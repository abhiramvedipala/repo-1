"use client";

import type { FileEntry } from "@/lib/types";

export default function FileTree({
  files,
  activePath,
  onSelect,
}: {
  files: FileEntry[];
  activePath: string | null;
  onSelect: (path: string) => void;
}) {
  const onlyFiles = files.filter((f) => f.type === "file");

  return (
    <div className="text-sm">
      <div className="px-3 py-2 text-xs uppercase tracking-wide text-text-faint border-b border-bg-border">
        Explorer
      </div>
      <div className="py-1">
        {onlyFiles.length === 0 && (
          <div className="px-3 py-2 text-text-faint text-xs italic">no files yet</div>
        )}
        {onlyFiles.map((f) => (
          <button
            key={f.path}
            onClick={() => onSelect(f.path)}
            className={`w-full text-left px-3 py-1 flex items-center gap-2 hover:bg-bg-raised transition-colors ${
              f.path === activePath ? "bg-bg-raised text-accent" : "text-text-dim"
            }`}
          >
            <span className="text-text-faint">📄</span>
            <span className="truncate">{f.path}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
