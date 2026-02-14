"use client";

import { useState } from "react";
import Controls from "./Controls";
import InfoPanel from "./InfoPanel";
import QueuePanel from "./QueuePanel";

export default function App() {
  const [urls, setUrls] = useState<string[]>([]);
  const [deletedUrls, setDeletedUrls] = useState<Set<string>>(new Set());
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [outputDir, setOutputDir] = useState<string | null>(null);

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
        />
        <InfoPanel />
      </div>

      <QueuePanel urls={urls} setUrls={setUrls} deletedUrls={deletedUrls} />
    </div>
  );
}
