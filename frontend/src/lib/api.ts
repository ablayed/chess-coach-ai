import type { ApiErrorResponse } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:7860";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return localStorage.getItem("chesscoach_token");
}

async function request<T>(
  method: "GET" | "POST" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  const raw = await response.text();
  let jsonData: unknown = null;
  if (raw) {
    try {
      jsonData = JSON.parse(raw) as unknown;
    } catch {
      jsonData = null;
    }
  }

  if (!response.ok) {
    const data = (jsonData ?? {}) as ApiErrorResponse;
    const detail = data.detail ?? data.message ?? `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }

  return jsonData as T;
}

export const api = {
  get: <T>(path: string): Promise<T> => request<T>("GET", path),
  post: <T>(path: string, body?: unknown): Promise<T> => request<T>("POST", path, body),
  delete: (path: string): Promise<void> => request<void>("DELETE", path),
};

export { API_BASE_URL };
