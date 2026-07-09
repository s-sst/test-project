import { num, titleCase } from "../lib/format";

interface ComplianceCardProps {
  score: string | null;
  status: string;
}

export default function ComplianceCard({ score, status }: ComplianceCardProps) {
  const value = num(score);
  const display = value === null ? "—" : value.toFixed(1);

  const barColor =
    value === null
      ? "#94a3b8"
      : value >= 80
      ? "#059669"
      : value >= 60
      ? "#d97706"
      : "#dc2626";

  return (
    <div className="card card-pad">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Overall Compliance
      </p>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-4xl font-semibold text-slate-900">{display}</span>
        {value !== null && (
          <span className="text-lg font-medium text-slate-400">/100</span>
        )}
      </div>
      <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${value === null ? 0 : Math.min(100, Math.max(0, value))}%`,
            backgroundColor: barColor,
          }}
        />
      </div>
      <p className="mt-3 text-sm text-slate-600">
        Status:{" "}
        <span className="font-medium text-slate-800">
          {status ? titleCase(status) : "Not evaluated"}
        </span>
      </p>
    </div>
  );
}
