"use client";

import { useState } from "react";
import Controls from "./Controls";
import InfoPanel from "./InfoPanel";
import QueuePanel from "./QueuePanel";

function buildBackendUrl() {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) return envUrl.replace(/\/$/, "");

  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    return `${protocol}//${window.location.hostname}:8000`;
  }

  return "http://localhost:8000";
}

export default function App() {
  const [urls, setUrls] = useState<string[]>([]);
  const [deletedUrls, setDeletedUrls] = useState<Set<string>>(new Set());
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [outputDir, setOutputDir] = useState<string | null>(null);
  const [backendUrl] = useState(buildBackendUrl);

  return (
    <div className="min-h-screen bg-slate-900 text-gray-200 p-8 flex flex-col gap-6">
      <h1 className="text-3xl font-bold">FUBAR MEDIA DOWNLOADER</h1>

      <div className="flex gap-6">
        <Controls
          urls={urls}
          setUrls={setUrls}
          deletedUrls={deletedUrls}
          setDeletedUrls={setDeletedUrls}
          outputDir={outputDir}
          setOutputDir={setOutputDir}
          backendUrl={backendUrl}
        />
        <InfoPanel backendUrl={backendUrl} />
      </div>

      <QueuePanel urls={urls} setUrls={setUrls} deletedUrls={deletedUrls} />
    </div>
  );
}
