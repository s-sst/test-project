import { Link } from "react-router-dom";
import type { Framework } from "../api/types";
import { formatDate } from "../lib/format";

interface FrameworkTableProps {
  frameworks: Framework[];
}

export default function FrameworkTable({ frameworks }: FrameworkTableProps) {
  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="th">Framework</th>
              <th className="th">Publisher</th>
              <th className="th">Category</th>
              <th className="th text-right">Controls</th>
              <th className="th text-right">Requirements</th>
              <th className="th">Synced</th>
              <th className="th"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {frameworks.map((fw) => (
              <tr key={fw.id} className="hover:bg-slate-50">
                <td className="td">
                  <Link
                    to={`/framework/${fw.id}`}
                    className="font-medium text-brand-700 hover:underline"
                  >
                    {fw.name}
                  </Link>
                  <span className="ml-2 text-xs text-slate-400">
                    v{fw.version}
                  </span>
                  {!fw.is_active && (
                    <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                      inactive
                    </span>
                  )}
                </td>
                <td className="td text-slate-500">{fw.publisher}</td>
                <td className="td text-slate-500">{fw.category}</td>
                <td className="td text-right tabular-nums">
                  {fw.control_count}
                </td>
                <td className="td text-right tabular-nums">
                  {fw.requirement_count}
                </td>
                <td className="td text-slate-500">{formatDate(fw.synced_at)}</td>
                <td className="td text-right">
                  <Link
                    to={`/framework/${fw.id}`}
                    className="text-sm font-medium text-brand-600 hover:underline"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
