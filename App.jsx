import { useState } from "react";
import axios from "axios";

export default function App() {
  const [url, setUrl] = useState("");
  const [progress, setProgress] = useState(0);

  const startDownload = async () => {
    const res = await axios.post("http://localhost:8000/download", {
      url,
      mode: "audio",
      quality: "320"
    });

    const ws = new WebSocket(`ws://localhost:8000/ws/${res.data.job_id}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.progress !== undefined) {
        setProgress(data.progress);
      }
    };
  };

  return (
    <div className="min-h-screen bg-slate-900 text-gray-200 p-8">
      <h1 className="text-3xl font-bold mb-6">
        FUBAR MEDIA DOWNLOADER
      </h1>

      <textarea
        className="w-full bg-slate-950 border border-slate-700 p-4 rounded"
        placeholder="Paste URL..."
        onChange={(e) => setUrl(e.target.value)}
      />

      <button
        onClick={startDownload}
        className="mt-4 bg-blue-600 px-4 py-2 rounded"
      >
        Start Download
      </button>

      <div className="mt-6 bg-slate-950 h-3 rounded">
        <div
          className="bg-cyan-400 h-3 rounded"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
