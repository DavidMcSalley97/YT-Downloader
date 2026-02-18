import axios from "axios";

function stripSlash(s: string) {
  return s.replace(/\/+$/, "");
}

export function getBackendBase(): string {
  const env = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (env && env.trim()) return stripSlash(env.trim());

  // Browser only logic
  if (typeof window !== "undefined") {
    const origin = window.location.origin;

    // Codespaces: front on ...-3000.app.github.dev, back on ...-8000.app.github.dev
    if (origin.includes("-3000.app.github.dev")) {
      return stripSlash(origin.replace("-3000.app.github.dev", "-8000.app.github.dev"));
    }

    // Local dev
    if (origin.includes("localhost:3000")) {
      return "http://localhost:8000";
    }

    // Fallback: same origin
    return stripSlash(origin);
  }

  // SSR fallback
  return "http://localhost:8000";
}

export const api = axios.create({
  baseURL: getBackendBase(),
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});
