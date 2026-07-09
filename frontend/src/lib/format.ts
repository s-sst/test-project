import type { RequirementStatus, RiskLevel } from "../api/types";

/** Parse a numeric string like "72.50" safely. Returns null if not parseable. */
export function num(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const n = typeof value === "number" ? value : parseFloat(value);
  return Number.isFinite(n) ? n : null;
}

/** Format a 0-100 score as a percentage string. */
export function pct(
  value: string | number | null | undefined,
  digits = 1
): string {
  const n = num(value);
  if (n === null) return "—";
  return `${n.toFixed(digits)}%`;
}

/** Format a 0-1 ratio as a percentage string. */
export function ratioPct(
  value: string | number | null | undefined,
  digits = 1
): string {
  const n = num(value);
  if (n === null) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

/** Human-readable byte size. */
export function bytes(size: number | null | undefined): string {
  if (size === null || size === undefined || !Number.isFinite(size)) return "—";
  if (size < 1024) return `${size} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = size / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit++;
  }
  return `${value.toFixed(1)} ${units[unit]}`;
}

/** Duration in seconds -> compact human string. */
export function duration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds))
    return "—";
  if (seconds < 1) return "<1s";
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  if (m < 60) return s ? `${m}m ${s}s` : `${m}m`;
  const h = Math.floor(m / 60);
  const mr = m % 60;
  return mr ? `${h}h ${mr}m` : `${h}h`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// --- Color conventions ---------------------------------------------------

export interface Palette {
  text: string;
  bg: string;
  border: string;
  hex: string;
}

const STATUS_PALETTE: Record<string, Palette> = {
  PASS: {
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    hex: "#059669",
  },
  PARTIAL: {
    text: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
    hex: "#d97706",
  },
  FAIL: {
    text: "text-red-700",
    bg: "bg-red-50",
    border: "border-red-200",
    hex: "#dc2626",
  },
  CANNOT_DETERMINE: {
    text: "text-slate-600",
    bg: "bg-slate-100",
    border: "border-slate-200",
    hex: "#64748b",
  },
};

const RISK_PALETTE: Record<string, Palette> = {
  LOW: {
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    hex: "#059669",
  },
  MEDIUM: {
    text: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200",
    hex: "#d97706",
  },
  HIGH: {
    text: "text-orange-700",
    bg: "bg-orange-50",
    border: "border-orange-200",
    hex: "#ea580c",
  },
  CRITICAL: {
    text: "text-red-700",
    bg: "bg-red-50",
    border: "border-red-200",
    hex: "#dc2626",
  },
};

const NEUTRAL: Palette = {
  text: "text-slate-600",
  bg: "bg-slate-100",
  border: "border-slate-200",
  hex: "#64748b",
};

export function statusColor(status: RequirementStatus | string): Palette {
  return STATUS_PALETTE[status] ?? NEUTRAL;
}

export function riskColor(level: RiskLevel | string): Palette {
  return RISK_PALETTE[level] ?? NEUTRAL;
}

export function titleCase(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
