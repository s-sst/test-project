import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
  accent?: "brand" | "emerald" | "amber" | "red" | "slate";
  icon?: ReactNode;
}

const ACCENTS: Record<NonNullable<StatCardProps["accent"]>, string> = {
  brand: "text-brand-600 bg-brand-50",
  emerald: "text-emerald-600 bg-emerald-50",
  amber: "text-amber-600 bg-amber-50",
  red: "text-red-600 bg-red-50",
  slate: "text-slate-600 bg-slate-100",
};

export default function StatCard({
  label,
  value,
  hint,
  accent = "brand",
  icon,
}: StatCardProps) {
  return (
    <div className="card card-pad">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {label}
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
        </div>
        {icon && (
          <span
            className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${ACCENTS[accent]}`}
          >
            {icon}
          </span>
        )}
      </div>
    </div>
  );
}
