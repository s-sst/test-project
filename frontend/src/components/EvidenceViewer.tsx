import type { Evidence } from "../api/types";
import { ratioPct } from "../lib/format";

interface EvidenceViewerProps {
  evidence: Evidence[];
}

export default function EvidenceViewer({ evidence }: EvidenceViewerProps) {
  if (evidence.length === 0) {
    return (
      <p className="text-xs italic text-slate-400">
        No supporting evidence captured.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {evidence.map((ev) => (
        <div
          key={ev.id}
          className="rounded-lg border border-slate-200 bg-slate-50 p-3"
        >
          <blockquote className="border-l-2 border-brand-300 pl-3 text-sm italic text-slate-700">
            “{ev.quote}”
          </blockquote>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
            {ev.page !== null && <span>Page {ev.page}</span>}
            <span>Confidence {ratioPct(ev.confidence, 0)}</span>
            <span
              className={`inline-flex items-center gap-1 ${
                ev.verified ? "text-emerald-600" : "text-slate-400"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  ev.verified ? "bg-emerald-500" : "bg-slate-300"
                }`}
              />
              {ev.verified ? "Verified" : "Unverified"}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
