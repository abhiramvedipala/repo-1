export type TaskStatus = "not_started" | "current" | "passed";

export interface TaskSummary {
  id: string;
  phase: number;
  phaseName: string;
  title: string;
  difficulty: number;
  concepts: string;
  index: number;
  isTerminalOnly: boolean;
  status: TaskStatus;
}

export interface TaskDetail extends TaskSummary {
  brief: string;
  hint: string;
  editorFiles: string[];
  starterFiles: Record<string, string>;
  workspaceHasFiles: boolean;
}

export interface TaskListResponse {
  tasks: TaskSummary[];
  total: number;
  completed: number;
  currentTaskId: string | null;
}

export interface CheckResult {
  label: string;
  passed: boolean;
  message: string;
}

export interface CheckResponse {
  passed: boolean;
  results: CheckResult[];
}

export interface FileEntry {
  path: string;
  type: "file" | "dir";
}

export interface UserOut {
  id: number;
  email: string;
  is_admin: boolean;
}
