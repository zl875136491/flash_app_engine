import { LayoutGrid, Mic2 } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "@/auth/AuthContext";
import { cn } from "@/lib/utils";

const tabs = [
  { to: "/create", label: "创建", icon: Mic2 },
  { to: "/apps", label: "应用", icon: LayoutGrid },
] as const;

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full flex-col bg-background text-foreground">
      <header
        className="flex shrink-0 items-center justify-between border-b border-border px-4"
        style={{ height: "var(--mobile-header-height)" }}
      >
        <div className="flex items-center gap-2">
          <span className="inline-flex size-7 items-center justify-center rounded-lg bg-primary text-xs font-bold text-primary-foreground">
            F
          </span>
          <span className="font-semibold tracking-tight">FlashApp</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="max-w-28 truncate text-xs text-muted-foreground">
            {user?.name || user?.itcode}
          </span>
          <button
            type="button"
            onClick={logout}
            className="text-xs font-medium text-primary"
          >
            退出
          </button>
        </div>
      </header>

      <main className="docs-scroll min-h-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>

      <nav
        className="flex shrink-0 border-t border-border bg-background"
        style={{
          height: "calc(var(--mobile-tabbar-height) + env(safe-area-inset-bottom, 0px))",
          paddingBottom: "env(safe-area-inset-bottom, 0px)",
        }}
      >
        {tabs.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex flex-1 flex-col items-center justify-center gap-0.5 text-xs transition-colors",
                isActive ? "text-primary" : "text-muted-foreground",
              )
            }
          >
            <Icon className="size-5" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
