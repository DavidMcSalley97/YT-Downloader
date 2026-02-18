"use client";

import { useState } from "react";

interface Props {
  backendUrl: string;
}

export default function InfoPanel({ backendUrl }: Props) {
  const [thumbnail, setThumbnail] = useState<string | null>(null);
  const [metadata, setMetadata] = useState("Awaiting selection…");
  const [netStatus, setNetStatus] = useState("Not tested");

  const testSpeed = async () => {
    setNetStatus("Testing…");
    const res = await fetch(`${backendUrl}/speed`); // you’d need a backend endpoint
    const data = await res.json();
    setNetStatus(`${data.download} Mbps | ${data.upload} Mbps | ${data.ping} ms`);
  };

  return (
    <div className="flex-1 flex flex-col gap-4">
      <div className="bg-slate-950 p-2 rounded text-center">
        {thumbnail ? (
          <img src={thumbnail} className="mx-auto" alt="thumbnail" />
        ) : (
          <div className="w-80 h-44 bg-slate-800 mx-auto rounded" />
        )}
      </div>

      <div className="bg-slate-950 p-2 rounded">{metadata}</div>

      <div className="bg-slate-950 p-2 rounded flex gap-2 items-center">
        <span>{netStatus}</span>
        <button
          className="ml-auto bg-blue-600 px-2 py-1 rounded hover:bg-blue-700"
          onClick={testSpeed}
        >
          Run Speed Test
        </button>
      </div>
    </div>
  );
}
