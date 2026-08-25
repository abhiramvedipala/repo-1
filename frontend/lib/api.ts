import type {
  CheckResponse,
  FileEntry,
  TaskDetail,
  TaskListResponse,
  UserOut,
} from "./types";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  login: (email: string, password: string) =>
    request<UserOut>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request("/api/auth/logout", { method: "POST" }),
  me: () => request<UserOut>("/api/auth/me"),

  listTasks: () => request<TaskListResponse>("/api/tasks"),
  getTask: (id: string) => request<TaskDetail>(`/api/tasks/${id}`),
  selectTask: (id: string) => request<{ created_files: string[] }>(`/api/tasks/${id}/select`, { method: "POST" }),
  checkTask: (id: string) => request<CheckResponse>(`/api/tasks/${id}/check`, { method: "POST" }),

  listFiles: (taskId: string) => request<{ files: FileEntry[] }>(`/api/files?taskId=${encodeURIComponent(taskId)}`),
  readFile: (path: string) => request<{ path: string; content: string }>(`/api/files/content?path=${encodeURIComponent(path)}`),
  writeFile: (path: string, content: string) =>
    request<{ ok: boolean }>("/api/files/content", { method: "POST", body: JSON.stringify({ path, content }) }),
};

export { ApiError };
