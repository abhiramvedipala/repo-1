"use client";

export default function Terminal({ lines, cwd }: { lines: string[]; cwd: string }) {
  return (
    <div className="h-full flex flex-col bg-black/40 font-mono text-xs">
      <div className="px-3 py-1.5 border-b border-bg-border text-text-faint uppercase tracking-wide">
        Terminal <span className="text-text-faint/60 normal-case">(mocked — real shell in Phase 1)</span>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-1 text-text-dim">
        {lines.map((l, i) => (
          <div key={i} className="whitespace-pre-wrap">
            {l}
          </div>
        ))}
        <div className="flex items-center gap-1 text-pass">
          <span>{cwd} $</span>
          <span className="inline-block w-1.5 h-3.5 bg-pass/70 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
