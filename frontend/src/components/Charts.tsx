import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { riskColor, statusColor, titleCase } from "../lib/format";
import type { RequirementStatus, RiskLevel } from "../api/types";
import EmptyState from "./EmptyState";

const RISK_ORDER: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
const STATUS_ORDER: RequirementStatus[] = [
  "PASS",
  "PARTIAL",
  "FAIL",
  "CANNOT_DETERMINE",
];

interface ChartCardProps {
  title: string;
  children: React.ReactNode;
  subtitle?: string;
}

export function ChartCard({ title, subtitle, children }: ChartCardProps) {
  return (
    <div className="card card-pad">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function hasData(values: number[]): boolean {
  return values.some((v) => v > 0);
}

// --- Risk distribution pie ----------------------------------------------

interface RiskPieProps {
  distribution: Record<string, number>;
  height?: number;
}

export function RiskPie({ distribution, height = 240 }: RiskPieProps) {
  const data = RISK_ORDER.map((level) => ({
    name: titleCase(level),
    key: level,
    value: distribution[level] ?? 0,
  })).filter((d) => d.value > 0);

  if (!hasData(RISK_ORDER.map((l) => distribution[l] ?? 0))) {
    return (
      <EmptyState
        title="No risk data yet"
        description="Risk levels appear once assessments complete."
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={2}
        >
          {data.map((entry) => (
            <Cell key={entry.key} fill={riskColor(entry.key).hex} />
          ))}
        </Pie>
        <Tooltip />
        <Legend
          iconType="circle"
          formatter={(value) => (
            <span className="text-xs text-slate-600">{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

// --- Requirement status bar ---------------------------------------------

interface StatusBarProps {
  distribution: Record<string, number>;
  height?: number;
}

export function StatusBar({ distribution, height = 240 }: StatusBarProps) {
  const data = STATUS_ORDER.map((status) => ({
    name: titleCase(status),
    key: status,
    value: distribution[status] ?? 0,
  }));

  if (!hasData(data.map((d) => d.value))) {
    return (
      <EmptyState
        title="No requirement results yet"
        description="Requirement outcomes appear after processing."
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11, fill: "#64748b" }}
          axisLine={{ stroke: "#e2e8f0" }}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip cursor={{ fill: "#f1f5f9" }} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((entry) => (
            <Cell key={entry.key} fill={statusColor(entry.key).hex} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// --- Coverage bar (horizontal, covered vs total) ------------------------

interface CoverageBarProps {
  covered: number;
  total: number;
}

export function CoverageBar({ covered, total }: CoverageBarProps) {
  const pct = total > 0 ? Math.round((covered / total) * 100) : 0;
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-2xl font-semibold text-slate-900">{pct}%</span>
        <span className="text-xs text-slate-500">
          {covered} of {total} frameworks covered
        </span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-brand-500 transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
