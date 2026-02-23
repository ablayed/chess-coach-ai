import { create } from "zustand";

import { api, ApiError } from "@/lib/api";
import type { AuthResponse, LoginRequest, RegisterRequest, UserPublic } from "@/types/api";

const TOKEN_KEY = "chesscoach_token";
const USER_KEY = "chesscoach_user";

interface AuthState {
  user: UserPublic | null;
  token: string | null;
  isLoading: boolean;
  initialized: boolean;
  error: string | null;
  initialize: () => void;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, username: string) => Promise<void>;
  logout: () => void;
}

function persistAuth(token: string, user: UserPublic): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearPersistedAuth(): void {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,
  initialized: false,
  error: null,

  initialize: () => {
    if (typeof window === "undefined") {
      return;
    }

    const token = localStorage.getItem(TOKEN_KEY);
    const userRaw = localStorage.getItem(USER_KEY);

    if (!token || !userRaw) {
      set({ initialized: true, user: null, token: null });
      return;
    }

    try {
      const user = JSON.parse(userRaw) as UserPublic;
      set({ token, user, initialized: true });
    } catch {
      clearPersistedAuth();
      set({ token: null, user: null, initialized: true });
    }
  },

  login: async (email, password) => {
    set({ isLoading: true, error: null });

    const payload: LoginRequest = { email, password };
    try {
      const response = await api.post<AuthResponse>("/api/v1/auth/login", payload);
      persistAuth(response.access_token, response.user);
      set({
        isLoading: false,
        token: response.access_token,
        user: response.user,
        error: null,
      });
    } catch (error: unknown) {
      const message = error instanceof ApiError ? error.detail : "Login failed";
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  register: async (email, password, username) => {
    set({ isLoading: true, error: null });

    const payload: RegisterRequest = { email, password, username };
    try {
      const response = await api.post<AuthResponse>("/api/v1/auth/register", payload);
      persistAuth(response.access_token, response.user);
      set({
        isLoading: false,
        token: response.access_token,
        user: response.user,
        error: null,
      });
    } catch (error: unknown) {
      const message = error instanceof ApiError ? error.detail : "Registration failed";
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  logout: () => {
    clearPersistedAuth();
    set({ user: null, token: null, error: null });
  },
}));
