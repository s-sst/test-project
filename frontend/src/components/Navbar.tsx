import { useAsync } from "../hooks/useApi";
import { get } from "../api/client";
import type { AuthMe, Health } from "../api/types";

export default function Navbar() {
  const health = useAsync<Health>(
    () => get<Health>("/health").then((r) => r.data),
    []
  );
  const me = useAsync<AuthMe>(
    () => get<AuthMe>("/auth/me").then((r) => r.data),
    []
  );

  const user = me.data?.user;
  const initials = user?.username
    ? user.username.slice(0, 2).toUpperCase()
    : "AU";

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div>
        <h1 className="text-base font-semibold text-slate-800">
          AI Governance &amp; Compliance Platform
        </h1>
        <p className="text-xs text-slate-400">
          Automated audit assistance with human oversight
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-2 sm:flex">
          <span
            className={`h-2 w-2 rounded-full ${
              health.data?.status === "ok" || health.data?.status === "healthy"
                ? "bg-emerald-500"
                : health.data
                ? "bg-amber-500"
                : health.error
                ? "bg-red-500"
                : "bg-slate-300"
            }`}
          />
          <span className="text-xs text-slate-500">
            {health.loading
              ? "Checking…"
              : health.data
              ? `v${health.data.version} · ${health.data.phase}`
              : "API offline"}
          </span>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="hidden text-right sm:block">
            <p className="text-sm font-medium leading-tight text-slate-700">
              {user?.username ?? "Guest"}
            </p>
            <p className="text-[11px] leading-tight text-slate-400">
              {user?.role_display ?? (me.loading ? "…" : "Not signed in")}
            </p>
          </div>
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
            {initials}
          </span>
        </div>
      </div>
    </header>
  );
}
