import type { ApiErrorResponse } from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860";
export const API_BASE_URL = BASE_URL;

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private getAuthToken(): string | null {
    if (this.token) {
      return this.token;
    }
    if (typeof window === "undefined") {
      return null;
    }
    return localStorage.getItem("chesscoach_token");
  }

  private async request<T>(method: "GET" | "POST" | "DELETE", path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const token = this.getAuthToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const url = `${API_BASE_URL}${path}`;

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        cache: "no-store",
      });

      const raw = await response.text();
      let parsed: unknown = null;
      if (raw) {
        try {
          parsed = JSON.parse(raw) as unknown;
        } catch {
          parsed = null;
        }
      }

      if (!response.ok) {
        const data = (parsed ?? {}) as ApiErrorResponse;
        const detail = data.detail ?? data.message ?? raw ?? `API error ${response.status}`;
        throw new ApiError(response.status, detail);
      }

      return parsed as T;
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        throw error;
      }
      if (error instanceof TypeError && error.message.toLowerCase().includes("fetch")) {
        throw new Error(`Cannot connect to backend. Is it running at ${API_BASE_URL}?`);
      }
      throw error;
    }
  }

  get<T>(path: string): Promise<T> {
    return this.request<T>("GET", path);
  }

  post<T>(path: string, body?: unknown): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  delete(path: string): Promise<void> {
    return this.request<void>("DELETE", path);
  }
}

export const api = new ApiClient();
