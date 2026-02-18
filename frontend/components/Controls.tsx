"use client";

import { useState } from "react";
import axios from "axios";

interface Props {
  urls: string[];
  setUrls: (urls: string[]) => void;
  deletedUrls: Set<string>;
  setDeletedUrls: (set: Set<string>) => void;
  outputDir: string | null;
  setOutputDir: (dir: string) => void;
  backendUrl: string;
}

export default function Controls({
  urls,
  deletedUrls,
  setDeletedUrls,
  outputDir,
  setOutputDir,
  backendUrl,
}: Props) {
  const [url, setUrl] = useState("");
  const [mode, setMode] = useState<"audio" | "video">("audio");
  const [quality, setQuality] = useState("320");
  const [progress, setProgress] = useState(0);

  const startDownload = async () => {
    if (!url) return;
    try {
      const downloadUrl = `${backendUrl}/download`;
      const res = await axios.post(downloadUrl, {
        url,
        mode,
        quality,
      });

      const wsBaseUrl = backendUrl.replace(/^http/, "ws");
      const ws = new WebSocket(`${wsBaseUrl}/ws/${res.data.job_id}`);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.progress !== undefined) setProgress(data.progress);
      };
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex-1 flex flex-col gap-4">
      <textarea
        placeholder="Paste URL(s) or search query..."
        className="w-full p-4 rounded bg-slate-950 border border-slate-700"
        onChange={(e) => setUrl(e.target.value)}
        value={url}
      />

      <div className="flex gap-4">
        <label>
          <input
            type="radio"
            checked={mode === "audio"}
            onChange={() => setMode("audio")}
          />{" "}
          Audio
        </label>
        <label>
          <input
            type="radio"
            checked={mode === "video"}
            onChange={() => setMode("video")}
          />{" "}
          Video
        </label>
      </div>

      <select
        value={quality}
        onChange={(e) => setQuality(e.target.value)}
        className="p-2 rounded bg-slate-950 border border-slate-700"
      >
        {mode === "audio"
          ? ["320", "192", "128"].map((q) => (
              <option key={q} value={q}>
                {q}
              </option>
            ))
          : ["best", "1080", "720"].map((q) => (
              <option key={q} value={q}>
                {q}
              </option>
            ))}
      </select>

      <button
        className="bg-blue-600 px-4 py-2 rounded hover:bg-blue-700"
        onClick={startDownload}
      >
        Start Download
      </button>

      <div className="w-full bg-slate-950 h-3 rounded mt-2">
        <div
          className="h-3 bg-cyan-400 rounded"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
