/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Components
import App from "./App.vue";

// Composables
import { createApp } from "vue";

// Plugins
import { registerPlugins } from "@/plugins";

// API client
import { OpenAPI } from "@/client";

// Styles
import "unfonts.css";

const app = createApp(App);

OpenAPI.BASE = import.meta.env.DEV
  ? import.meta.env.VITE_BASE_URL
  : window.location.origin;

// Initialize token from localStorage at startup
const storedToken = localStorage.getItem("auth:token");
if (storedToken) {
  OpenAPI.TOKEN = storedToken;
}

// Add response interceptor to handle token expiration (401/403)
OpenAPI.interceptors.response.use((response) => {
  if (response.status === 401 || response.status === 403) {
    // Clear auth token from localStorage
    localStorage.removeItem("auth:token");
    // Redirect to login page
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }
  return response;
});

registerPlugins(app);

app.mount("#app");
