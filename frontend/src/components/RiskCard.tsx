import { num, riskColor, titleCase } from "../lib/format";

interface RiskCardProps {
  score: string | null;
  level: string;
}

export default function RiskCard({ score, level }: RiskCardProps) {
  const value = num(score);
  const palette = riskColor(level);

  return (
    <div className="card card-pad">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        Risk Assessment
      </p>
      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="flex items-baseline gap-2">
          <span className="text-4xl font-semibold text-slate-900">
            {value === null ? "—" : value.toFixed(1)}
          </span>
          {value !== null && (
            <span className="text-lg font-medium text-slate-400">/100</span>
          )}
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-sm font-semibold ${palette.bg} ${palette.text} ${palette.border}`}
        >
          {level ? titleCase(level) : "Unknown"}
        </span>
      </div>
      <div className="mt-4 flex gap-1.5">
        {(["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const).map((lvl) => {
          const active = lvl === level;
          const c = riskColor(lvl);
          return (
            <div
              key={lvl}
              className="h-2.5 flex-1 rounded-full"
              style={{
                backgroundColor: active ? c.hex : "#e2e8f0",
              }}
              title={titleCase(lvl)}
            />
          );
        })}
      </div>
    </div>
  );
}
