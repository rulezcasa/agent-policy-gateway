"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

type UploadState = "idle" | "selected" | "uploading" | "complete" | "error";

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} bytes`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function UploadIcon() {
  return <svg aria-hidden="true" className="size-7" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24"><path d="M12 16V4" /><path d="m8 8 4-4 4 4" /><path d="M5 14v5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5" /></svg>;
}

export function PolicyUploadDropzone() {
  const inputRef = useRef<HTMLInputElement>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [isDragging, setIsDragging] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => () => {
    if (timerRef.current) clearTimeout(timerRef.current);
  }, []);

  function clearSelection() {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = null;
    setFile(null); setState("idle"); setMessage(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  function selectFile(candidate?: File) {
    if (!candidate) { setState("error"); setMessage("Select a PDF policy document to continue."); return; }
    if (candidate.type !== "application/pdf" && !candidate.name.toLowerCase().endsWith(".pdf")) {
      setFile(null); setState("error"); setMessage("Unsupported file type. Upload a PDF policy document."); return;
    }
    setFile(candidate); setState("selected"); setMessage(null);
  }

  function startExtraction() {
    if (!file) { selectFile(); return; }
    setState("uploading"); setMessage(null);
    timerRef.current = setTimeout(() => { setState("complete"); timerRef.current = null; }, 1100);
  }

  return <div className="space-y-4">
    {state !== "complete" && <div onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }} onDragLeave={() => setIsDragging(false)} onDrop={(event) => { event.preventDefault(); setIsDragging(false); selectFile(event.dataTransfer.files.item(0) ?? undefined); }} className={`rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-200 sm:p-14 ${isDragging ? "border-indigo-500 bg-indigo-50/70 shadow-[0_0_0_4px_rgba(99,91,230,0.08)]" : "border-slate-200 bg-white shadow-[0_1px_2px_rgba(15,23,42,0.025)]"}`}>
      <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-700 ring-1 ring-inset ring-indigo-100"><UploadIcon /></div><p className="mt-5 text-xs font-semibold uppercase tracking-[0.1em] text-indigo-600">Policy ingestion</p><h3 className="mt-2 text-lg font-semibold tracking-[-0.02em] text-slate-900">Upload your company policy</h3><p className="mt-2 text-sm text-slate-500">Drop a PDF here, or choose a file from your computer.</p><input ref={inputRef} className="sr-only" id="policy-document" type="file" accept="application/pdf,.pdf" onChange={(event) => selectFile(event.target.files?.item(0) ?? undefined)} /><label htmlFor="policy-document" className="mt-6 inline-flex h-10 cursor-pointer items-center justify-center rounded-xl bg-indigo-600 px-4 text-sm font-semibold text-white shadow-sm shadow-indigo-200 transition-colors hover:bg-indigo-700">Select PDF document</label><p className="mt-4 text-xs text-slate-500">PDF policy documents are supported.</p>
    </div>}

    {state === "error" && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{message}</div>}
    {file && state !== "complete" && <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex min-w-0 items-center gap-3"><span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-rose-50 text-xs font-bold text-rose-700">PDF</span><div className="min-w-0"><p className="truncate text-sm font-semibold text-slate-900">{file.name}</p><p className="mt-1 text-xs text-slate-500">{formatFileSize(file.size)} · {state === "uploading" ? "Uploading and preparing extraction" : "Ready for extraction"}</p></div></div>{state === "uploading" ? <span className="inline-flex items-center gap-2 text-sm font-medium text-indigo-700"><span className="size-4 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-700" />Processing</span> : <div className="flex gap-3"><button type="button" onClick={clearSelection} className="rounded-lg px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100">Remove</button><button type="button" onClick={startExtraction} className="rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700">Start extraction</button></div>}</div></div>}
    {state === "complete" && <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5"><div className="flex gap-3"><span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white">✓</span><div><h3 className="font-semibold text-emerald-950">Document ready for review</h3><p className="mt-1 text-sm leading-6 text-emerald-800">The demo upload is complete. In the connected product, extracted rules will now be available for administrator review.</p><div className="mt-4 flex flex-wrap gap-3"><Link href="/policies/review" className="rounded-lg bg-emerald-700 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-800">Review extracted rules</Link><button type="button" onClick={clearSelection} className="rounded-lg border border-emerald-300 bg-white px-3.5 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-100">Upload another</button></div></div></div></div>}
  </div>;
}
