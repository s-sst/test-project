import type { AuditLog } from "../api/types";
import { formatDate, titleCase } from "../lib/format";
import EmptyState from "./EmptyState";

interface TimelineProps {
  logs: AuditLog[];
}

export default function Timeline({ logs }: TimelineProps) {
  if (logs.length === 0) {
    return (
      <EmptyState
        title="No audit activity"
        description="Actions across the platform will appear here."
      />
    );
  }

  return (
    <ol className="relative space-y-5 border-l border-slate-200 pl-6">
      {logs.map((log) => (
        <li key={log.id} className="relative">
          <span className="absolute -left-[27px] top-1 h-3 w-3 rounded-full border-2 border-white bg-brand-500" />
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-sm font-medium text-slate-800">
              {log.action_display || titleCase(log.action)}
            </p>
            <time className="text-xs text-slate-400">
              {formatDate(log.timestamp)}
            </time>
          </div>
          <p className="mt-0.5 text-sm text-slate-600">{log.summary}</p>
          <p className="mt-0.5 text-[11px] text-slate-400">
            {log.actor_label}
            {log.entity_type && ` · ${titleCase(log.entity_type)}`}
          </p>
        </li>
      ))}
    </ol>
  );
}
