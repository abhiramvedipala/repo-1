"use client";

import * as monaco from "monaco-editor";
import MonacoEditor, { loader } from "@monaco-editor/react";

// Load Monaco from our own bundle instead of @monaco-editor/react's default
// (a jsdelivr CDN fetch) — this is a self-hosted tool, it shouldn't depend
// on an external CDN just to open the editor. Must run at module-eval time,
// before @monaco-editor/react's own loader.init() call fires on mount.
loader.config({ monaco });

// Monaco spawns a background worker (editorWorkerService) for basic
// services even on plain-text buffers. Point it at our own bundled worker
// so webpack emits it as a real asset, instead of Monaco's default AMD
// worker loader which assumes a CDN layout we don't have.
if (typeof window !== "undefined") {
  (self as unknown as { MonacoEnvironment: unknown }).MonacoEnvironment = {
    getWorker() {
      return new Worker(new URL("monaco-editor/editor/editor.worker.js", import.meta.url));
    },
  };
}

export default function Editor({
  path,
  content,
  onChange,
}: {
  path: string | null;
  content: string;
  onChange: (value: string) => void;
}) {
  if (!path) {
    return (
      <div className="flex-1 flex items-center justify-center text-text-faint text-sm">
        Select a file to start editing
      </div>
    );
  }

  const language = path.endsWith(".py")
    ? "python"
    : path.endsWith(".toml")
      ? "ini"
      : path.endsWith(".md")
        ? "markdown"
        : "plaintext";

  return (
    <MonacoEditor
      key={path}
      height="100%"
      theme="vs-dark"
      language={language}
      value={content}
      onChange={(v) => onChange(v ?? "")}
      options={{
        fontSize: 13,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        padding: { top: 12 },
      }}
    />
  );
}
