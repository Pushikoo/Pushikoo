// Utilities
import { defineStore } from "pinia";

// API client
import { OpenAPI, SystemService } from "@/client";

const TOKEN_STORAGE_KEY = "auth:token";

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

      const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
      if (storedToken) {
        this.token = storedToken;
        OpenAPI.TOKEN = storedToken;
      }
    },

    setToken(token: string | null) {
      this.token = token;

      if (typeof window !== "undefined") {
        if (token) {
          localStorage.setItem(TOKEN_STORAGE_KEY, token);
        } else {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
        }
      }

      OpenAPI.TOKEN = token ?? undefined;
    },

    async loginWithToken(token: string) {
      debugger;
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
