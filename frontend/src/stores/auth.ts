// Utilities
import { defineStore } from "pinia";

// API client
import { SystemService } from "@/client";

const COOKIE_NAME = "access_token";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 8;

function setCookie(value: string) {
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(value)}; Path=/; SameSite=Lax; Max-Age=${COOKIE_MAX_AGE}`;
}

function getCookie(): string | null {
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${COOKIE_NAME}=([^;]*)`),
  );
  const value = match?.[1];
  return value ? decodeURIComponent(value) : null;
}

export function deleteCookie() {
  document.cookie = `${COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: null as string | null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    initializeFromStorage() {
      if (typeof window === "undefined") return;

      this.token = getCookie();
    },

    setToken(token: string | null) {
      this.token = token;

      if (typeof window !== "undefined") {
        if (token) {
          setCookie(token);
        } else {
          deleteCookie();
        }
      }
    },

    async loginWithToken(token: string) {
      const trimmed = token.trim();
      if (!trimmed) {
        throw new Error("Token is empty");
      }

      this.setToken(trimmed);

      // Validate token by calling a lightweight authenticated endpoint
      await SystemService.getSystemConfigApiV1SystemConfigGet();
    },

    logout() {
      this.setToken(null);
    },
  },
});
