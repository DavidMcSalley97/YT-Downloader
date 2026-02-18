
"use client";

import { useEffect, useState } from "react";
import axios from "axios";

interface Props {
  backendUrl: string;
  selectedUrl: string | null;
}

export default function InfoPanel({ backendUrl, selectedUrl }: Props) {
  const [thumb, setThumb] = useState<string | null>(null);
  const [metaHtml, setMetaHtml] = useState("Awaiting selection…");
  const [netStatus, setNetStatus] = useState("Not tested");

  useEffect(() => {
    if (!selectedUrl) {
      setThumb(null);
      setMetaHtml("Awaiting selection…");
      return;
    }

    (async () => {
      try {
        setMetaHtml("Fetching metadata…");
        const res = await axios.get(`${backendUrl}/info`, { params: { url: selectedUrl } });
        const info = res.data;

        if (info?.error) {
          setThumb(null);
          setMetaHtml(info.error);
          return;
        }

        setThumb(info.thumbnail || null);

        const duration = info.duration_str || "Unknown";
        const views = typeof info.view_count === "number" ? info.view_count.toLocaleString() : "0";

        setMetaHtml(
          `<b>${info.title || "Unknown title"}</b><br>` +
            `${info.uploader || ""}<br>` +
            `Duration: ${duration}<br>` +
            `${views} views`
        );
      } catch {
        setThumb(null);
        setMetaHtml("Failed to fetch metadata");
      }
    })();
  }, [backendUrl, selectedUrl]);

  const testSpeed = async () => {
    try {
      setNetStatus("Testing…");
      const res = await axios.get(`${backendUrl}/speed`);
      const d = res.data || {};
      setNetStatus(`${d.download} Mbps | ${d.upload} Mbps | ${d.ping} ms`);
    } catch {
      setNetStatus("Speed test failed");
    }
  };

  return (
    <div className="flex-[2] flex flex-col gap-4">
      <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Thumbnail</h2>
          <span className="inline-flex items-center rounded-full border border-slate-700 bg-slate-950/40 px-3 py-1 text-xs text-slate-200">
           
          </span>
        </div>

        <div className="bg-slate-950 p-2 rounded text-center border border-slate-700">
          {thumb ? (
            <img src={thumb} className="mx-auto max-w-full rounded" alt="thumbnail" />
          ) : (
            <div className="w-80 h-44 bg-slate-800 mx-auto rounded" />
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Metadata</h2>
          <span className="inline-flex items-center rounded-full border border-slate-700 bg-slate-950/40 px-3 py-1 text-xs text-slate-200">
           
          </span>
        </div>

        <div
          className="bg-slate-950 border border-slate-700 rounded p-3 text-sm text-slate-200 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: metaHtml }}
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-base font-semibold">Network</h2>
          <span className="inline-flex items-center rounded-full border border-slate-700 bg-slate-950/40 px-3 py-1 text-xs text-slate-200">
            
          </span>
        </div>

        <div className="flex gap-2 items-center">
          <span className="text-sm text-slate-300">{netStatus}</span>
          <button
            className="ml-auto bg-blue-600 px-3 py-2 rounded hover:bg-blue-700 transition"
            onClick={testSpeed}
            type="button"
          >
            Run Speed Test
          </button>
        </div>
      </div>
    </div>
  );
}
