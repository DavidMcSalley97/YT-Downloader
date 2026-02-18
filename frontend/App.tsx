"use client";

import axios from "axios";
import { useMemo, useState } from "react";

interface DownloadResponse {
  job_id: string;
}

interface ProgressMessage {
  progress?: number;
  done?: boolean;
  error?: string;
  filename?: string;
}

function cleanBase(s: string) {
  return s.trim().replace(/^["']|["']$/g, "").replace(/\/+$/g, "");
}

function computeBackendBase(): string {
  // Prefer env var
  const env = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (env && env.trim()) return cleanBase(env);

  // Browser-derived (Codespaces safe)
  if (typeof window !== "undefined") {
    const origin = window.location.origin;

    // Codespaces mapping 3000 -> 8000
    if (origin.includes("-3000.app.github.dev")) {
      return origin.replace("-3000.app.github.dev", "-8000.app.github.dev");
    }

    // Local dev
    if (origin.includes("localhost:3000")) {
      return "http://localhost:8000";
    }

    // Fallback
    return origin;
  }

  return "http://localhost:8000";
}

function wsBaseFromHttp(httpBase: string) {
  return httpBase.replace(/^https:\/\//, "wss://").replace(/^http:\/\//, "ws://");
}

export default function App() {
  const BACKEND_BASE = useMemo(() => computeBackendBase(), []);

  const api = useMemo(() => {
    return axios.create({
      baseURL: BACKEND_BASE,
      timeout: 60000,
      headers: { "Content-Type": "application/json" },
    });
  }, [BACKEND_BASE]);

  const [url, setUrl] = useState("");
  const [mode, setMode] = useState<"audio" | "video">("audio");
  const [quality, setQuality] = useState("320");

  const [progress, setProgress] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);
  const [filename, setFilename] = useState<string | null>(null);
  const [status, setStatus] = useState("Awaiting selection...");
  const [error, setError] = useState<string | null>(null);

  const startDownload = async () => {
    const trimmed = url.trim();
    if (!trimmed) return;

    setIsDownloading(true);
    setProgress(0);
    setFilename(null);
    setError(null);
    setStatus(`POST ${BACKEND_BASE}/download`);

    try {
      const res = await api.post<DownloadResponse>("/download", {
        url: trimmed,
        mode,
        quality,
      });

      const jobId = res.data.job_id;
      setStatus(`Job: ${jobId} (connecting WS...)`);

      const wsUrl = `${wsBaseFromHttp(BACKEND_BASE)}/ws/${jobId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => setStatus("WebSocket connected");

      ws.onmessage = (event) => {
        const msg: ProgressMessage = JSON.parse(event.data);

        if (typeof msg.progress === "number") setProgress(msg.progress);
        if (msg.filename) setFilename(msg.filename);

        if (msg.error) {
          setError(msg.error);
          setStatus("Download failed");
          setIsDownloading(false);
          ws.close();
          return;
        }

        if (msg.done) {
          setProgress(100);
          setStatus("Done ✅");
          setIsDownloading(false);
          ws.close();
        }
      };

      ws.onerror = () => {
        setError("WebSocket error (backend URL/port exposure)");
        setStatus("WS failed");
        setIsDownloading(false);
        try { ws.close(); } catch {}
      };
    } catch (e: any) {
      const msg = e?.response
        ? `HTTP ${e.response.status}: ${JSON.stringify(e.response.data)}`
        : `Network Error: cannot reach backend at ${BACKEND_BASE}`;

      setError(msg);
      setStatus("Backend unreachable");
      setIsDownloading(false);
    }
  };

  const fileUrl = filename ? `${BACKEND_BASE}/files/${encodeURIComponent(filename)}` : null;

  return (
    <div className="min-h-screen bg-slate-900 text-gray-200 p-8">
      <h1 className="text-3xl font-bold mb-6">FUBAR MEDIA DOWNLOADER</h1>

      <p className="text-xs text-slate-400 mb-3">
        Backend in use: <span className="text-slate-200">{BACKEND_BASE}</span>
      </p>

      <textarea
        className="w-full bg-slate-950 border border-slate-700 p-4 rounded"
        placeholder="Paste URL..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        rows={3}
      />

      <div className="mt-4 flex gap-4 items-center">
        <label className="flex items-center gap-2">
          <input type="radio" checked={mode === "audio"} onChange={() => setMode("audio")} />
          Audio
        </label>

        <label className="flex items-center gap-2">
          <input type="radio" checked={mode === "video"} onChange={() => setMode("video")} />
          Video
        </label>

        <select
          className="ml-auto bg-slate-950 border border-slate-700 rounded px-3 py-2"
          value={quality}
          onChange={(e) => setQuality(e.target.value)}
        >
          {mode === "audio" ? (
            <>
              <option value="320">320</option>
              <option value="192">192</option>
              <option value="128">128</option>
            </>
          ) : (
            <>
              <option value="best">best</option>
              <option value="1080">1080</option>
              <option value="720">720</option>
              <option value="480">480</option>
            </>
          )}
        </select>
      </div>

      <button
        onClick={startDownload}
        disabled={isDownloading}
        className="mt-4 bg-blue-600 px-4 py-2 rounded disabled:opacity-50 w-full"
      >
        {isDownloading ? "Downloading..." : "Start Download"}
      </button>

      <div className="mt-6 bg-slate-950 h-3 rounded overflow-hidden">
        <div className="bg-cyan-400 h-3 rounded transition-all duration-300" style={{ width: `${progress}%` }} />
      </div>

      <p className="mt-3 text-sm text-slate-400">{status}</p>

      {fileUrl && (
        <a className="mt-2 inline-block text-cyan-300 underline" href={fileUrl} target="_blank" rel="noreferrer">
          Download: {filename}
        </a>
      )}

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
    </div>
  );
}
