"use client";

import { useMemo, useState } from "react";
import Controls from "./Controls";
import InfoPanel from "./InfoPanel";
import QueuePanel from "./QueuePanel";

function buildBackendUrl() {
  const envUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) return envUrl.replace(/\/$/, "");
  if (typeof window !== "undefined") return window.location.origin.replace(/\/$/, "");
  return "https://silver-broccoli-455p97r4j743q6wr-8000.app.github.dev/";
}

export default function App() {
  const backendUrl = useMemo(buildBackendUrl, []);

  const [queue, setQueue] = useState<string[]>([]);
  const [deleted, setDeleted] = useState<Set<string>>(new Set());
  const [selectedUrl, setSelectedUrl] = useState<string | null>(null);

  const [status, setStatus] = useState("Ready");
  const [progress, setProgress] = useState(0);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 p-8 flex flex-col gap-6">
      <h1 className="text-3xl font-bold tracking-wide">FUBAR MEDIA DOWNLOADER</h1>

      <div className="flex gap-6">
        <Controls
          backendUrl={backendUrl}
          queue={queue}
          setQueue={setQueue}
          deleted={deleted}
          setDeleted={setDeleted}
          setSelectedUrl={setSelectedUrl}
          setStatus={setStatus}
          setProgress={setProgress}
        />

        <InfoPanel backendUrl={backendUrl} selectedUrl={selectedUrl} />
      </div>

      <QueuePanel
        backendUrl={backendUrl}
        queue={queue}
        setQueue={setQueue}
        deleted={deleted}
        setDeleted={setDeleted}
        selectedUrl={selectedUrl}
        setSelectedUrl={setSelectedUrl}
      />

      <div className="flex items-center gap-4">
        <div className="text-sm text-slate-300">{status}</div>
        <div className="flex-1 h-2 rounded bg-slate-950 border border-slate-700 overflow-hidden">
          <div className="h-full bg-sky-400" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  );
}

