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
