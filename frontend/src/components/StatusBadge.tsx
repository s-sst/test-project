import { riskColor, statusColor, titleCase } from "../lib/format";

type Kind = "status" | "risk" | "neutral";

interface StatusBadgeProps {
  value: string;
  kind?: Kind;
  label?: string;
  className?: string;
}

export default function StatusBadge({
  value,
  kind = "status",
  label,
  className,
}: StatusBadgeProps) {
  const palette =
    kind === "risk"
      ? riskColor(value)
      : kind === "status"
      ? statusColor(value)
      : { text: "text-slate-600", bg: "bg-slate-100", border: "border-slate-200", hex: "#64748b" };

  const text = label ?? titleCase(value);

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${palette.bg} ${palette.text} ${palette.border} ${
        className ?? ""
      }`}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: palette.hex }}
      />
      {text}
    </span>
  );
}
