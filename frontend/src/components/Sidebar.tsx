import { NavLink } from "react-router-dom";

interface NavItem {
  to: string;
  label: string;
  icon: JSX.Element;
  end?: boolean;
}

const icon = (d: string) => (
  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none">
    <path
      d={d}
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const NAV: NavItem[] = [
  {
    to: "/",
    label: "Dashboard",
    end: true,
    icon: icon("M4 13h6V4H4v9zm0 7h6v-5H4v5zm10 0h6V11h-6v9zm0-16v5h6V4h-6z"),
  },
  {
    to: "/upload",
    label: "Documents",
    icon: icon("M12 16V4m0 0L8 8m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"),
  },
  {
    to: "/history",
    label: "Assessments",
    icon: icon("M4 6h16M4 12h16M4 18h10"),
  },
  {
    to: "/frameworks",
    label: "Frameworks",
    icon: icon("M4 5h16v4H4V5zm0 6h16v8H4v-8zm4 3h8"),
  },
  {
    to: "/reports",
    label: "Reports",
    icon: icon(
      "M7 3h7l5 5v13a1 1 0 01-1 1H7a1 1 0 01-1-1V4a1 1 0 011-1zm7 0v5h5M9 13h6M9 17h6"
    ),
  },
  {
    to: "/settings",
    label: "Settings",
    icon: icon(
      "M12 15a3 3 0 100-6 3 3 0 000 6zm7.4-3a7.4 7.4 0 00-.1-1.2l2-1.6-2-3.4-2.4 1a7.3 7.3 0 00-2-1.2l-.4-2.5H9.5l-.4 2.5a7.3 7.3 0 00-2 1.2l-2.4-1-2 3.4 2 1.6a7.4 7.4 0 000 2.4l-2 1.6 2 3.4 2.4-1c.6.5 1.3.9 2 1.2l.4 2.5h5l.4-2.5c.7-.3 1.4-.7 2-1.2l2.4 1 2-3.4-2-1.6c.1-.4.1-.8.1-1.2z"
    ),
  },
];

export default function Sidebar() {
  return (
    <aside className="flex h-full w-60 flex-col border-r border-slate-200 bg-white">
      <div className="flex h-16 items-center gap-2.5 border-b border-slate-200 px-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l8 4v6c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V6l8-4z" />
          </svg>
        </span>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-slate-800">AI Governance</p>
          <p className="text-[11px] text-slate-400">Compliance Platform</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-brand-50 text-brand-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`
            }
          >
            {item.icon}
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-200 px-4 py-3">
        <p className="text-[11px] leading-relaxed text-slate-400">
          Decision-support tooling. A human auditor owns every final compliance
          determination.
        </p>
      </div>
    </aside>
  );
}
