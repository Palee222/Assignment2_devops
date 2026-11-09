import { Link, useRouterState } from "@tanstack/react-router";
import { Activity, ArrowUpRight, BookOpenText, Fingerprint, LayoutDashboard, Menu, Settings2, ShieldCheck, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { AppButton } from "./AppButton";

const navigation = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/incidents", label: "Incidents", icon: BookOpenText },
  { to: "/password", label: "Password check", icon: Fingerprint },
  { to: "/settings", label: "Connection", icon: Settings2 },
] as const;

export function AppShell({ children, title, subtitle, action }: { children: ReactNode; title: string; subtitle: string; action?: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return <div className="min-h-screen bg-background lg:flex">
    {mobileOpen && <div className="fixed inset-0 z-30 bg-shell/55 lg:hidden" onClick={() => setMobileOpen(false)} aria-hidden="true" />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-62 flex-col bg-shell text-primary-foreground transition-transform lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex h-21 items-center justify-between border-b border-primary-foreground/10 px-6">
        <Link to="/" className="flex items-center gap-3" onClick={() => setMobileOpen(false)}>
          <span className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground"><ShieldCheck size={21} strokeWidth={2.3} /></span>
          <span className="font-display text-xl font-bold">secnote<span className="text-primary">.</span></span>
        </Link>
        <AppButton variant="ghost" size="icon" className="text-primary-foreground lg:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={19} /></AppButton>
      </div>
      <div className="px-4 pt-8">
        <p className="px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-primary-foreground/40">Workspace</p>
        <nav className="mt-4 space-y-1" aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon }) => <Link key={to} to={to} search={{}} onClick={() => setMobileOpen(false)} className={`flex h-11 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors ${pathname === to ? "bg-primary text-primary-foreground" : "text-primary-foreground/60 hover:bg-primary-foreground/10 hover:text-primary-foreground"}`}><Icon size={18} strokeWidth={1.9} /><span>{label}</span></Link>)}
        </nav>
      </div>
      <div className="mt-auto border-t border-primary-foreground/10 p-5">
        <div className="flex items-start gap-3 rounded-md bg-primary-foreground/5 p-3">
          <Activity size={17} className="mt-0.5 shrink-0 text-primary" />
          <div><p className="text-xs font-semibold">Security workspace</p><p className="mt-1 text-xs leading-5 text-primary-foreground/45">A clearer view of every incident and password check.</p></div>
        </div>
        <a href="https://github.com/Palee222/DevOPS" target="_blank" rel="noreferrer" className="mt-5 flex items-center justify-between px-2 text-xs text-primary-foreground/45 transition-colors hover:text-primary-foreground">View source on GitHub <ArrowUpRight size={14} /></a>
      </div>
    </aside>
    <div className="min-w-0 flex-1">
      <header className="sticky top-0 z-20 flex h-17 items-center justify-between border-b border-border bg-card px-5 sm:px-8 lg:px-10">
        <div className="flex items-center gap-3"><AppButton variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={20} /></AppButton><span className="hidden text-xs font-semibold uppercase tracking-[0.12em] text-muted-foreground sm:block">Secnote / Workspace</span><span className="text-sm font-semibold sm:hidden">{title}</span></div>
        <div className="flex items-center gap-2.5"><span className="hidden text-xs font-medium text-muted-foreground sm:block">Security workspace</span><span className="ml-2 flex size-8 items-center justify-center rounded-full bg-secondary text-xs font-bold text-secondary-foreground">PS</span></div>
      </header>
      <main className="mx-auto max-w-345 px-5 pb-20 pt-8 sm:px-8 sm:pt-10 lg:px-10">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-5"><div><p className="mb-2 text-[11px] font-bold uppercase tracking-[0.13em] text-primary">Security workspace</p><h1 className="font-display text-[27px] font-bold leading-tight text-foreground sm:text-[32px]">{title}</h1><p className="mt-2 text-sm text-muted-foreground">{subtitle}</p></div>{action}</div>
        {children}
      </main>
    </div>
  </div>;
}
