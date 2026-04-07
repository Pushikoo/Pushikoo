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
import { deleteCookie } from "@/stores/auth";

// Styles
import "unfonts.css";

const app = createApp(App);

OpenAPI.BASE = window.location.origin;
OpenAPI.WITH_CREDENTIALS = true;

// Add response interceptor to handle token expiration (401/403)
OpenAPI.interceptors.response.use((response) => {
  if (response.status === 401 || response.status === 403) {
    // Clear auth token cookie
    deleteCookie();
    // Redirect to login page
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }
  return response;
});

registerPlugins(app);

app.mount("#app");
