// Get version from Vite env variable (set during build) or fallback to _version.json
const getAppVersion = (): string | undefined => {
  // Try Vite env variable first (best practice)
  const envVersion = import.meta.env.VITE_APP_VERSION;
  if (envVersion) return envVersion;

  // Fallback to _version.json if it exists (during dev/build)
  try {
    // Dynamic import would be async, so we skip this fallback at runtime
    // The version file is only used during build process
    return undefined;
  } catch {
    return undefined;
  }
};

export { getAppVersion };
