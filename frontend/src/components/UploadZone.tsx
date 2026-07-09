import { useRef, useState } from "react";
import { postForm } from "../api/client";
import type { Document } from "../api/types";

interface UploadZoneProps {
  onUploaded: (docs: Document[]) => void;
}

const DOC_TYPES = [
  { value: "", label: "Auto-detect" },
  { value: "POLICY", label: "Policy" },
  { value: "PROCEDURE", label: "Procedure" },
  { value: "EVIDENCE", label: "Evidence" },
  { value: "CONTRACT", label: "Contract" },
  { value: "REPORT", label: "Report" },
  { value: "OTHER", label: "Other" },
];

export default function UploadZone({ onUploaded }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [docType, setDocType] = useState("");

  async function upload(files: FileList | File[]) {
    const list = Array.from(files);
    if (list.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      const form = new FormData();
      if (list.length === 1) {
        form.append("file", list[0]);
      } else {
        list.forEach((f) => form.append("files", f));
      }
      if (docType) form.append("doc_type", docType);
      const res = await postForm<Document[]>("/upload", form);
      onUploaded(res.data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="card card-pad">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="w-full sm:w-56">
          <label className="label" htmlFor="doc-type">
            Document type
          </label>
          <select
            id="doc-type"
            className="input"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
          >
            {DOC_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          void upload(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          dragging
            ? "border-brand-400 bg-brand-50"
            : "border-slate-300 bg-slate-50 hover:border-brand-300 hover:bg-brand-50/40"
        }`}
      >
        <svg
          className="mb-3 h-8 w-8 text-brand-500"
          viewBox="0 0 24 24"
          fill="none"
        >
          <path
            d="M12 16V4m0 0L8 8m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <p className="text-sm font-medium text-slate-700">
          {uploading ? "Uploading…" : "Drop files here or click to browse"}
        </p>
        <p className="mt-1 text-xs text-slate-400">
          PDF, DOCX, TXT and more · single or multiple files
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) void upload(e.target.files);
          }}
        />
      </div>

      {error && (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
