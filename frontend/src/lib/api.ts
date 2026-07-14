import { clearSession, getStoredToken } from "@/lib/auth-storage";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  auth?: boolean;
};

async function parseError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string | { msg?: string }[] };
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  } catch {
    // ignore
  }
  return `请求失败（${response.status}）`;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const useAuth = options.auth !== false;
  if (useAuth) {
    const token = getStoredToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(path, {
    ...options,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (response.status === 401 && useAuth) {
    clearSession();
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export type TokenResponse = {
  access_token: string;
  token_type: string;
  itcode: string;
  expires_in: number;
};

export type MeResponse = {
  itcode: string;
  name: string;
};

export function loginWithItcode(itcode: string) {
  return apiRequest<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: { itcode },
    auth: false,
  });
}

export function fetchMe() {
  return apiRequest<MeResponse>("/api/v1/auth/me");
}

export type Stage =
  | "Received"
  | "Analyzing"
  | "Coding"
  | "Building"
  | "Verifying"
  | "Success"
  | "Failed"
  | "Stopped";

export type TaskDetail = {
  id: string;
  author_itcode: string;
  raw_voice_text: string | null;
  current_stage: Stage;
  exposed_url: string | null;
  created_at: string;
  updated_at: string;
  images_content: string[];
  image_paths: string[];
  logs: { stage: Stage; message: string; detail: string; created_at: string }[];
  generated_code_path: string | null;
};

export type CreateTaskPayload = {
  raw_voice_text?: string | null;
  images_content?: string[];
  image_paths?: string[];
};

export function createTask(payload: CreateTaskPayload) {
  return apiRequest<TaskDetail>("/api/v1/tasks", {
    method: "POST",
    body: payload,
  });
}

export type UploadImageResponse = {
  path: string;
  filename: string;
  content_type: string | null;
  size: number;
};

export async function uploadImage(file: File): Promise<UploadImageResponse> {
  const token = getStoredToken();
  const form = new FormData();
  form.append("file", file);

  const headers = new Headers({ Accept: "application/json" });
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch("/api/v1/uploads/images", {
    method: "POST",
    headers,
    body: form,
  });

  if (response.status === 401) {
    clearSession();
  }
  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response));
  }
  return (await response.json()) as UploadImageResponse;
}

export type TaskSummary = {
  id: string;
  author_itcode: string;
  raw_voice_text: string | null;
  current_stage: Stage;
  exposed_url: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskListResponse = {
  items: TaskSummary[];
  total: number;
  quota?: QuotaInfo | null;
};

export type QuotaInfo = {
  limit: number;
  used: number;
  remaining: number;
};

export type StageLog = {
  stage: Stage;
  message: string;
  detail: string;
  created_at: string;
};

export function listTasks(params?: { skip?: number; limit?: number }) {
  const search = new URLSearchParams();
  if (params?.skip != null) search.set("skip", String(params.skip));
  if (params?.limit != null) search.set("limit", String(params.limit));
  const qs = search.toString();
  return apiRequest<TaskListResponse>(`/api/v1/tasks${qs ? `?${qs}` : ""}`);
}

export function fetchQuota() {
  return apiRequest<QuotaInfo>("/api/v1/tasks/quota");
}

export function getTask(taskId: string) {
  return apiRequest<TaskDetail>(`/api/v1/tasks/${taskId}`);
}

export function getTaskLogs(taskId: string) {
  return apiRequest<StageLog[]>(`/api/v1/tasks/${taskId}/logs`);
}

export function stopTask(taskId: string) {
  return apiRequest<TaskDetail>(`/api/v1/tasks/${taskId}/stop`, { method: "POST" });
}

export function startTask(taskId: string) {
  return apiRequest<TaskDetail>(`/api/v1/tasks/${taskId}/start`, { method: "POST" });
}

export function retryTask(taskId: string) {
  return apiRequest<TaskDetail>(`/api/v1/tasks/${taskId}/retry`, { method: "POST" });
}

export function removeTask(taskId: string) {
  return apiRequest<{ ok: boolean; task_id: string; detail: string }>(
    `/api/v1/tasks/${taskId}`,
    { method: "DELETE" },
  );
}
