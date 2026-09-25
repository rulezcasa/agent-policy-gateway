"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useState } from "react";

type IconName = "dashboard" | "policies" | "upload" | "review" | "actions" | "approvals" | "menu";
type NavigationItem = { href: string; label: string; icon: IconName; exact?: boolean };

const navigation: NavigationItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: "dashboard", exact: true },
  { href: "/policies", label: "Policies", icon: "policies", exact: true },
  { href: "/policies/upload", label: "Upload policies", icon: "upload" },
  { href: "/policies/review", label: "Review rules", icon: "review" },
  { href: "/actions", label: "Actions", icon: "actions" },
  { href: "/approvals", label: "Approvals", icon: "approvals" },
];

const pageTitles: Record<string, string> = {
  "/dashboard": "Dashboard", "/policies": "Policies", "/policies/upload": "Upload policies",
  "/policies/review": "Review extracted rules", "/actions": "Agent actions", "/approvals": "Approvals",
};

function isActive(item: NavigationItem, pathname: string) {
  return item.exact ? pathname === item.href : pathname.startsWith(item.href);
}

function Icon({ name }: { name: IconName }) {
  const common = { "aria-hidden": true, className: "size-5 shrink-0", fill: "none", stroke: "currentColor", strokeLinecap: "round" as const, strokeLinejoin: "round" as const, strokeWidth: 1.8, viewBox: "0 0 24 24" };
  const paths: Record<IconName, ReactNode> = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    policies: <><path d="M7 3.5h7l3 3V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1v-15a1.5 1.5 0 0 1 1-1.5Z" /><path d="M14 3.5V7h3" /><path d="M9 11h5M9 15h5" /></>,
    upload: <><path d="M12 16V4" /><path d="m8 8 4-4 4 4" /><path d="M5 14v5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-5" /></>,
    review: <><path d="M5 4h10l4 4v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1Z" /><path d="M14 4v4h4" /><path d="m8 15 2.2 2L16 11.5" /></>,
    actions: <><path d="M12 3a9 9 0 1 0 9 9" /><path d="M12 7v5l3 2" /><path d="M17 3v4h4" /></>,
    approvals: <><path d="M12 3 4.5 6v5c0 4.7 3.2 8.6 7.5 10 4.3-1.4 7.5-5.3 7.5-10V6L12 3Z" /><path d="m8.5 12 2.3 2.3 4.7-4.7" /></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
  };
  return <svg {...common}>{paths[name]}</svg>;
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return <aside className="flex h-full w-64 flex-col border-r border-slate-200/80 bg-white px-3 py-5 shadow-[1px_0_0_rgba(15,23,42,0.02)]">
    <Link href="/dashboard" onClick={onNavigate} className="flex items-center gap-3 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-coral-500">
      <span className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-coral-500 to-coral-700 text-[11px] font-bold tracking-tight text-white shadow-sm shadow-coral-200">EA</span>
      <span className="leading-tight"><span className="block text-sm font-semibold tracking-tight text-slate-950">Enforce.ai</span><span className="block text-xs font-medium text-slate-500">Gateway</span></span>
    </Link>
    <nav aria-label="Primary navigation" className="mt-9 flex flex-1 flex-col gap-1.5">
      {navigation.map((item) => {
        const active = isActive(item, pathname);
        return <Link key={item.href} href={item.href} onClick={onNavigate} className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-coral-500 ${item.href.startsWith("/policies/") ? "ml-3" : ""} ${active ? "bg-coral-50/70 text-coral-700 before:absolute before:inset-y-2 before:left-0 before:w-0.5 before:rounded-full before:bg-coral-600" : "text-slate-500 hover:bg-slate-100/70 hover:text-slate-900"}`}><Icon name={item.icon} />{item.label}</Link>;
      })}
    </nav>
  </aside>;
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const title = pageTitles[pathname] ?? "Enforce.ai";
  return <div className="min-h-screen bg-[#f7f6f4] text-slate-950">
    <div className="fixed inset-y-0 left-0 z-30 hidden lg:block"><Sidebar /></div>
    {mobileNavOpen && <div className="fixed inset-0 z-50 lg:hidden"><button aria-label="Close navigation" className="absolute inset-0 bg-slate-950/35" onClick={() => setMobileNavOpen(false)} /><div className="relative h-full w-72 shadow-2xl"><Sidebar onNavigate={() => setMobileNavOpen(false)} /></div></div>}
    <div className="lg:pl-64">
      <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
        <div className="flex items-center gap-3"><button type="button" aria-label="Open navigation" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-coral-500 lg:hidden" onClick={() => setMobileNavOpen(true)}><Icon name="menu" /></button><h1 className="text-[19px] font-semibold tracking-[-0.025em] text-slate-950">{title}</h1></div>
      </header>
      <main className="mx-auto w-full max-w-7xl px-4 py-7 sm:px-6 lg:px-8 lg:py-9">{children}</main>
    </div>
  </div>;
}
