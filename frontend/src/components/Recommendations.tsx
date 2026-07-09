import type { Recommendation } from "../api/types";
import { titleCase } from "../lib/format";
import EmptyState from "./EmptyState";

interface RecommendationsProps {
  recommendations: Recommendation[];
}

function priorityStyle(rank: number): string {
  if (rank <= 1) return "bg-red-50 text-red-700 border-red-200";
  if (rank === 2) return "bg-orange-50 text-orange-700 border-orange-200";
  if (rank === 3) return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-slate-100 text-slate-600 border-slate-200";
}

export default function Recommendations({
  recommendations,
}: RecommendationsProps) {
  if (recommendations.length === 0) {
    return (
      <EmptyState
        title="No recommendations"
        description="No remediation items were generated for this assessment."
      />
    );
  }

  const sorted = [...recommendations].sort(
    (a, b) => a.priority_rank - b.priority_rank
  );

  return (
    <div className="space-y-3">
      {sorted.map((rec) => (
        <div key={rec.id} className="card card-pad">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${priorityStyle(
                    rec.priority_rank
                  )}`}
                >
                  {rec.priority_display || titleCase(rec.priority)}
                </span>
                {rec.requirement_identifier && (
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-500">
                    {rec.requirement_identifier}
                  </span>
                )}
                {rec.category && (
                  <span className="text-[11px] text-slate-400">
                    {titleCase(rec.category)}
                  </span>
                )}
              </div>
              <h4 className="mt-2 text-sm font-semibold text-slate-800">
                {rec.title}
              </h4>
            </div>
          </div>
          {rec.description && (
            <p className="mt-2 text-sm text-slate-600">{rec.description}</p>
          )}
          {rec.rationale && (
            <p className="mt-2 text-xs italic text-slate-500">
              Rationale: {rec.rationale}
            </p>
          )}
          {rec.remediation_steps.length > 0 && (
            <div className="mt-3">
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Remediation steps
              </p>
              <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-600">
                {rec.remediation_steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
