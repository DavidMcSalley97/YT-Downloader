"use client"; // Required because we use useState and WebSockets

import { useState } from "react";
import axios, { AxiosResponse } from "axios";

interface DownloadResponse {
  job_id: string;
}

interface ProgressMessage {
  progress?: number;
  done?: boolean;
}

export default function App() {
  const [url, setUrl] = useState<string>("");
  const [progress, setProgress] = useState<number>(0);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  const startDownload = async () => {
    if (!url.trim()) return;

    try {
      setIsDownloading(true);
      setProgress(0);

      // Call FastAPI backend
      const res: AxiosResponse<DownloadResponse> = await axios.post(
        "http://localhost:8000/download",
        {
          url,
          mode: "audio",
          quality: "320",
        }
      );

      const ws = new WebSocket(`https://reimagined-winner-x77gqw46wgph9pww-3000.app.github.dev//ws/${res.data.job_id}`);

      ws.onmessage = (event: MessageEvent<string>) => {
        const data: ProgressMessage = JSON.parse(event.data);
        if (typeof data.progress === "number") setProgress(data.progress);
        if (data.done) {
          ws.close();
          setIsDownloading(false);
        }
      };

      ws.onerror = () => {
        ws.close();
        setIsDownloading(false);
      };
    } catch (err) {
      console.error("Download failed:", err);
      setIsDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-gray-200 p-8">
      <h1 className="text-3xl font-bold mb-6">FUBAR MEDIA DOWNLOADER</h1>

      <textarea
        className="w-full bg-slate-950 border border-slate-700 p-4 rounded"
        placeholder="Paste URL..."
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />

      <button
        onClick={startDownload}
        disabled={isDownloading}
        className="mt-4 bg-blue-600 px-4 py-2 rounded disabled:opacity-50"
      >
        {isDownloading ? "Downloading..." : "Start Download"}
      </button>

      <div className="mt-6 bg-slate-950 h-3 rounded overflow-hidden">
        <div
          className="bg-cyan-400 h-3 rounded transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
