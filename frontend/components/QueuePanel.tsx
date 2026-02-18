"use client";

import { useEffect, useRef, useState } from "react";

interface Props {
  backendUrl: string;
  queue: string[];
  setQueue: (q: string[]) => void;

  deleted: Set<string>;
  setDeleted: (s: Set<string>) => void;

  selectedUrl: string | null;
  setSelectedUrl: (u: string | null) => void;
}

export default function QueuePanel({
  queue,
  setQueue,
  deleted,
  setDeleted,
  selectedUrl,
  setSelectedUrl,
}: Props) {
  const [menu, setMenu] = useState<{ x: number; y: number; open: boolean }>({
    x: 0,
    y: 0,
    open: false,
  });

  const listRef = useRef<HTMLDivElement | null>(null);
  const [selectedSet, setSelectedSet] = useState<Set<string>>(new Set());

  useEffect(() => {
    const onClick = () => setMenu((m) => ({ ...m, open: false }));
    window.addEventListener("click", onClick);
    return () => window.removeEventListener("click", onClick);
  }, []);

  const onRightClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setMenu({ x: e.clientX, y: e.clientY, open: true });
  };

  const toggleSelect = (url: string) => {
    setSelectedUrl(url);
    setSelectedSet((prev) => {
      const n = new Set(prev);
      if (n.has(url)) n.delete(url);
      else n.add(url);
      return n;
    });
  };

  const removeSelected = () => {
    const toRemove = new Set(selectedSet);
    const nextDeleted = new Set(deleted);
    toRemove.forEach((u) => nextDeleted.add(u));

    setDeleted(nextDeleted);
    const nextQueue = queue.filter((u) => !toRemove.has(u));
    setQueue(nextQueue);

    // reset selection
    setSelectedSet(new Set());
    setSelectedUrl(nextQueue[0] || null);
    setMenu((m) => ({ ...m, open: false }));
  };

  const clearAll = () => {
    setQueue([]);
    setSelectedSet(new Set());
    setSelectedUrl(null);
    setMenu((m) => ({ ...m, open: false }));
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/40 p-5 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold">Download Queue:</h2>
        <span className="inline-flex items-center rounded-full border border-slate-700 bg-slate-950/40 px-3 py-1 text-xs text-slate-200">
          
        </span>
      </div>

      <div
        ref={listRef}
        onContextMenu={onRightClick}
        className="bg-slate-950 border border-slate-700 rounded p-2 min-h-[160px]"
      >
        {queue.length === 0 ? (
          <div className="text-sm text-slate-500 p-3">Queue is empty.</div>
        ) : (
          <ul className="text-sm">
            {queue.map((u) => {
              const active = u === selectedUrl;
              const multi = selectedSet.has(u);
              return (
                <li
                  key={u}
                  onClick={() => toggleSelect(u)}
                  className={`px-3 py-2 rounded cursor-pointer select-none ${
                    active || multi
                      ? "bg-slate-800 border border-sky-400 font-semibold"
                      : "hover:bg-slate-900"
                  }`}
                >
                  {u}
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {menu.open && (
        <div
          className="fixed z-50 w-44 rounded border border-slate-700 bg-slate-950 shadow-xl"
          style={{ left: menu.x, top: menu.y }}
        >
          <button
            className="w-full text-left px-3 py-2 text-sm hover:bg-slate-800"
            onClick={removeSelected}
            disabled={selectedSet.size === 0}
          >
            Remove selected
          </button>
          <button
            className="w-full text-left px-3 py-2 text-sm hover:bg-slate-800"
            onClick={clearAll}
          >
            Clear all
          </button>
        </div>
      )}
    </div>
  );
}
