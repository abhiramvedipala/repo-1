"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import ReactMarkdown from "react-markdown";

import { api, ApiError } from "@/lib/api";
import type { CheckResult, FileEntry, LabStatus, TaskDetail, TaskSummary, UserOut } from "@/lib/types";

import TopBar from "@/components/TopBar";
import ProgressDots from "@/components/ProgressDots";
import DifficultyStars from "@/components/DifficultyStars";
import Checklist, { CheckState } from "@/components/Checklist";
import HintBox from "@/components/HintBox";
import FileTree from "@/components/FileTree";
import LabControls from "@/components/LabControls";
import LabFrame from "@/components/LabFrame";

// monaco-editor and xterm.js both touch browser globals at module-eval
// time, which breaks Next.js's server-side prerender of this page —
// load both client-only.
const Editor = dynamic(() => import("@/components/Editor"), { ssr: false });
const Terminal = dynamic(() => import("@/components/Terminal"), { ssr: false });

const LAB_POLL_MS = 10_000;

export default function LabPage() {
  const router = useRouter();

  const [user, setUser] = useState<UserOut | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [completed, setCompleted] = useState(0);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [taskDetail, setTaskDetail] = useState<TaskDetail | null>(null);

  const [files, setFiles] = useState<FileEntry[]>([]);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState("");
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  const [checkState, setCheckState] = useState<CheckState>("idle");
  const [checkResults, setCheckResults] = useState<CheckResult[] | null>(null);

  const [lab, setLab] = useState<LabStatus>({ status: "none" });
  const [labStarting, setLabStarting] = useState(false);

  // ── auth bootstrap ─────────────────────────────────────────────
  useEffect(() => {
    api
      .me()
      .then((u) => setUser(u))
      .catch(() => router.push("/login"))
      .finally(() => setAuthChecked(true));
  }, [router]);

  // ── load task list ─────────────────────────────────────────────
  const refreshTasks = useCallback(async () => {
    const data = await api.listTasks();
    setTasks(data.tasks);
    setTotal(data.total);
    setCompleted(data.completed);
    return data;
  }, []);

  useEffect(() => {
    if (!user) return;
    refreshTasks().then((data) => {
      const initial = data.currentTaskId || data.tasks[0]?.id || null;
      if (initial) setActiveTaskId(initial);
    });
  }, [user, refreshTasks]);

  // ── lab session (Phase 2: real per-session container) ──────────
  const refreshLabStatus = useCallback(async () => {
    const s = await api.labStatus();
    setLab(s);
    return s;
  }, []);

  useEffect(() => {
    if (!user) return;
    refreshLabStatus();
    const t = setInterval(refreshLabStatus, LAB_POLL_MS);
    return () => clearInterval(t);
  }, [user, refreshLabStatus]);

  async function onStartLab() {
    setLabStarting(true);
    try {
      const s = await api.labStart();
      setLab(s);
    } catch (err) {
      // surfaced via the "No lab session" state; a real UI would toast this
      console.error(err);
    } finally {
      setLabStarting(false);
    }
  }

  async function onStopLab() {
    await api.labStop();
    await refreshLabStatus();
  }

  // ── select a task ──────────────────────────────────────────────
  const selectTask = useCallback(async (taskId: string) => {
    setActiveTaskId(taskId);
    setCheckState("idle");
    setCheckResults(null);
    await api.selectTask(taskId);
    const detail = await api.getTask(taskId);
    setTaskDetail(detail);

    const filesRes = await api.listFiles(taskId);
    setFiles(filesRes.files);

    const firstFile = detail.editorFiles[0] ?? null;
    setActiveFile(firstFile);
    if (firstFile) {
      const content = await api.readFile(firstFile);
      setFileContent(content.content);
    } else {
      setFileContent("");
    }
    setDirty(false);
  }, []);

  useEffect(() => {
    if (activeTaskId) selectTask(activeTaskId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTaskId]);

  // ── open a different file in the tree ─────────────────────────
  async function openFile(path: string) {
    if (dirty && activeFile) await saveFile();
    setActiveFile(path);
    const content = await api.readFile(path);
    setFileContent(content.content);
    setDirty(false);
  }

  async function saveFile() {
    if (!activeFile) return;
    setSaving(true);
    try {
      await api.writeFile(activeFile, fileContent);
      setDirty(false);
    } finally {
      setSaving(false);
    }
  }

  // autosave, debounced
  useEffect(() => {
    if (!dirty || !activeFile) return;
    const t = setTimeout(saveFile, 800);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fileContent, dirty]);

  async function onCheck() {
    if (!activeTaskId) return;
    if (dirty) await saveFile();
    setCheckState("checking");
    try {
      const res = await api.checkTask(activeTaskId);
      setCheckResults(res.results);
      setCheckState("done");
      await refreshTasks();
      const detail = await api.getTask(activeTaskId);
      setTaskDetail(detail);
      // a terminal task may have created files since we last listed them
      const filesRes = await api.listFiles(activeTaskId);
      setFiles(filesRes.files);
    } catch (err) {
      setCheckState("idle");
    }
  }

  function onNext() {
    const idx = tasks.findIndex((t) => t.id === activeTaskId);
    const next = tasks[idx + 1];
    if (next) setActiveTaskId(next.id);
  }

  const canGoNext = taskDetail?.status === "passed";

  if (!authChecked) {
    return <div className="min-h-screen flex items-center justify-center text-text-dim">Loading…</div>;
  }
  if (!user) return null;

  return (
    <div className="h-screen flex flex-col">
      <TopBar email={user.email} />

      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL */}
        <div className="w-[35%] min-w-[360px] border-r border-bg-border flex flex-col overflow-y-auto bg-bg-panel">
          <div className="p-4 border-b border-bg-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-accent uppercase tracking-wide">
                {taskDetail ? `Phase ${taskDetail.phase} — ${taskDetail.phaseName}` : "Loading"}
              </span>
              <span className="text-xs text-text-faint">
                {completed}/{total} complete
              </span>
            </div>
            <ProgressDots tasks={tasks} activeTaskId={activeTaskId} onSelect={setActiveTaskId} />
          </div>

          {taskDetail && (
            <div className="p-4 flex-1 flex flex-col">
              <div className="flex items-center justify-between mb-1">
                <h1 className="text-lg font-semibold">{taskDetail.title}</h1>
                <DifficultyStars level={taskDetail.difficulty} />
              </div>
              <div className="text-text-faint text-xs mb-3">{taskDetail.concepts}</div>

              <div className="prose-brief text-sm text-text-dim">
                <ReactMarkdown>{taskDetail.brief}</ReactMarkdown>
              </div>

              <HintBox hint={taskDetail.hint} />

              <div className="mt-6 flex items-center gap-2">
                <button
                  onClick={onCheck}
                  disabled={checkState === "checking"}
                  className="px-4 py-2 rounded-md bg-accent hover:bg-accent-hover disabled:opacity-60 text-sm font-medium transition-colors"
                >
                  {checkState === "checking" ? "Checking…" : "Check"}
                </button>
                <button
                  onClick={onNext}
                  disabled={!canGoNext}
                  className="px-4 py-2 rounded-md border border-bg-border text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:border-accent hover:text-accent transition-colors"
                >
                  Next →
                </button>
                {saving && <span className="text-xs text-text-faint">saving…</span>}
              </div>

              <Checklist state={checkState} results={checkResults} />
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <LabControls lab={lab} starting={labStarting} onStart={onStartLab} onStop={onStopLab} />

          {lab.status === "running" && lab.proxyUrl ? (
            // Phase 2: a real, isolated code-server container — this iframe
            // *is* the file tree, editor, and terminal now.
            <LabFrame proxyUrl={lab.proxyUrl} />
          ) : (
            // No lab session yet (or Docker isn't set up): fall back to the
            // Phase 0/1 in-browser editor + shared terminal, still backed
            // by the same on-disk workspace.
            <div className="flex-1 flex flex-col overflow-hidden">
              {!taskDetail?.isTerminalOnly && (
                <>
                  <div className="h-40 border-b border-bg-border overflow-y-auto bg-bg-panel">
                    <FileTree files={files} activePath={activeFile} onSelect={openFile} />
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <Editor
                      path={activeFile}
                      content={fileContent}
                      onChange={(v) => {
                        setFileContent(v);
                        setDirty(true);
                      }}
                    />
                  </div>
                </>
              )}
              <div className={taskDetail?.isTerminalOnly ? "flex-1 min-h-0" : "h-48 border-t border-bg-border"}>
                <Terminal />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
