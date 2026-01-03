/**
 * Extracts error message from API error response.
 * If the error body contains a string `detail` field, returns it.
 * Otherwise returns the fallback message.
 */
export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === "object") {
    const body = (error as any).body;
    if (body && typeof body.detail === "string") {
      return body.detail;
    }
  }
  return fallback;
}
