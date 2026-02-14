"use client";

interface Props {
  urls: string[];
  setUrls: (urls: string[]) => void;
  deletedUrls: Set<string>;
}

export default function QueuePanel({ urls, setUrls, deletedUrls }: Props) {
  const removeUrl = (index: number) => {
    const copy = [...urls];
    copy.splice(index, 1);
    setUrls(copy);
  };

  const clearQueue = () => setUrls([]);

  return (
    <div className="bg-slate-950 p-2 rounded flex flex-col gap-2">
      <h2 className="font-bold">Download Queue:</h2>
      <ul className="flex flex-col gap-1 max-h-64 overflow-y-auto">
        {urls.map((url, i) => (
          <li
            key={i}
            className="flex justify-between items-center p-2 bg-slate-800 rounded"
          >
            {url}
            <button
              className="bg-red-600 px-2 py-1 rounded hover:bg-red-700"
              onClick={() => removeUrl(i)}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <button
        className="bg-red-600 px-2 py-1 rounded hover:bg-red-700 mt-2"
        onClick={clearQueue}
      >
        Clear All
      </button>
    </div>
  );
}

