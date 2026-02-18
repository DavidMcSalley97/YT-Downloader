"use client";

import { useEffect, useRef, useState } from "react";
import axios from "axios";

type Mode = "audio" | "video";

interface Props {
  backendUrl: string;

  queue: string[];
  setQueue: (q: string[]) => void;

  deleted: Set<string>;
  setDeleted: (s: Set<string>) => void;

  setSelectedUrl: (u: string | null) => void;

  setStatus: (s: string) => void;
  setProgress: (n: number) => void;
}

function panel(title: string, children: React.ReactNode) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold">{title}</h2>
        <span className="inline-flex items-center rounded-full border border-slate-700 bg-slate-950/40 px-3 py-1 text-xs text-slate-200">
          
        </span>
      </div>
      <div className="text-slate-200 text-sm leading-relaxed">{children}</div>
    </div>
  );
}

export default function Controls({
  backendUrl,
  queue,
  setQueue,
  deleted,
  setDeleted,
  setSelectedUrl,
  setStatus,
  setProgress,
}: Props) {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<Mode>("audio");
  const [quality, setQuality] = useState("320");

  const debounceRef = useRef<number | null>(null);

  // match PyQt behavior: user types, we resolve lines into queue after short delay
  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);

    debounceRef.current = window.setTimeout(async () => {
      const lines = text
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);

      if (lines.length === 0) {
        setQueue([]);
        return;
      }

      try {
        const res = await axios.post(`${backendUrl}/resolve`, { lines });
        const resolved: string[] = res.data?.urls || [];
        const filtered = resolved.filter((u) => !deleted.has(u));
        setQueue(filtered);
        if (filtered[0]) setSelectedUrl(filtered[0]);
      } catch (e) {
        // keep silent like PyQt smart search worker
      }
    }, 450);

    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [text, backendUrl, deleted, setQueue, setSelectedUrl]);

  useEffect(() => {
    setQuality(mode === "audio" ? "320" : "best");
  }, [mode]);

  const startDownload = async () => {
    const first = queue[0];
    if (!first) return;

    try {
      setStatus("Starting…");
      setProgress(0);

      const postUrl = `${backendUrl.replace(/\/$/, "")}/download`;
      const res = await axios.post(postUrl, { url: first, mode, quality });

      const jobId: string | undefined = res.data?.job_id;
      if (!jobId) throw new Error("No job_id returned");

      const wsBase = backendUrl
        .replace(/\/$/, "")
        .replace(/^https?:\/\//, (m) => (m === "https://" ? "wss://" : "ws://"));

      const ws = new WebSocket(`${wsBase}/ws/${jobId}`);

      ws.onmessage = (ev) => {
        const data = JSON.parse(ev.data);

        if (typeof data.progress === "number") {
          setProgress(data.progress);
          setStatus("Downloading…");
        }

        if (data.done) {
          setProgress(0);
          setStatus("Ready");
          ws.close();
        }

        if (data.error) {
          setStatus(data.error);
          ws.close();
        }
      };

      ws.onerror = () => setStatus("WebSocket error");
    } catch (err) {
      console.error(err);
      setStatus("Failed to start download");
    }
  };

  return (
    <div className="flex-[3] flex flex-col gap-4">
      {panel(
        "Source",
        <textarea
          className="w-full min-h-[180px] p-3 rounded bg-slate-950 border border-slate-700 outline-none"
          placeholder="Paste URL(s) or type a search query (one per line)…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      )}

      {panel(
        "Mode",
        <div className="flex gap-4">
          <label
            className={`px-3 py-2 rounded border ${
              mode === "audio"
                ? "border-sky-400 bg-slate-900 font-semibold"
                : "border-slate-700 bg-slate-950"
            } cursor-pointer`}
          >
            <input
              type="radio"
              className="mr-2"
              checked={mode === "audio"}
              onChange={() => setMode("audio")}
            />
            Audio
          </label>

          <label
            className={`px-3 py-2 rounded border ${
              mode === "video"
                ? "border-sky-400 bg-slate-900 font-semibold"
                : "border-slate-700 bg-slate-950"
            } cursor-pointer`}
          >
            <input
              type="radio"
              className="mr-2"
              checked={mode === "video"}
              onChange={() => setMode("video")}
            />
            Video
          </label>
        </div>
      )}

      {panel(
        "Quality",
        <select
          className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2"
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
            </>
          )}
        </select>
      )}

      <button
        className="h-10 rounded bg-blue-600 hover:bg-blue-700 transition font-semibold"
        onClick={startDownload}
        type="button"
      >
        Start Download
      </button>

      <div className="text-xs text-slate-400">
        (Queue auto-builds as you type, like the old GUI.)
      </div>
    </div>
  );
}


