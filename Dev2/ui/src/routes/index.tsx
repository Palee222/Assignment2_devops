import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, ArrowUpRight, BookOpenText, Fingerprint, Plus, ShieldCheck, ShieldAlert, Activity } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { AppButton } from "@/components/AppButton";
import { ErrorNotice, IncidentTable, PreviewNotice } from "@/components/IncidentUI";
import { useIncidents } from "@/lib/use-incidents";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Overview — secnote" }, { name: "description", content: "Security incident overview and password hygiene workspace." }, { property: "og:title", content: "Overview — secnote" }, { property: "og:description", content: "Security incident overview and password hygiene workspace." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" }] }),
  component: Overview,
});

function Overview() {
  const { incidents, url, error, ready, refresh } = useIncidents();
  const open = incidents.filter((incident) => incident.status === "Open").length;
  const inProgress = incidents.filter((incident) => incident.status === "In Progress").length;
  const critical = incidents.filter((incident) => incident.severity === "Critical" && incident.status !== "Closed" && incident.status !== "Resolved").length;
  return <AppShell title="Overview" subtitle="A clear picture of your security activity." action={<Link to="/incidents" search={{ new: "1" }}><AppButton><Plus size={16} /> New incident</AppButton></Link>}>
    {ready && !url && <PreviewNotice />}{error && <ErrorNotice message={error} onRetry={refresh} />}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {[
        { label: "Total incidents", value: incidents.length, icon: BookOpenText, iconColor: "text-info", iconBg: "bg-info-soft", note: "All recorded incidents" },
        { label: "Open incidents", value: open, icon: ShieldAlert, iconColor: "text-danger", iconBg: "bg-danger-soft", note: "Awaiting attention" },
        { label: "In progress", value: inProgress, icon: Activity, iconColor: "text-warning", iconBg: "bg-warning-soft", note: "Currently being handled" },
        { label: "Critical alerts", value: critical, icon: ShieldCheck, iconColor: "text-primary", iconBg: "bg-accent", note: "High-priority issues" },
      ].map(({ label, value, icon: Icon, iconColor, iconBg, note }) => <div key={label} className="rounded-md border border-border bg-card p-5"><div className="flex items-start justify-between"><p className="text-xs font-semibold text-muted-foreground">{label}</p><span className={`flex size-9 items-center justify-center rounded-md ${iconBg} ${iconColor}`}><Icon size={18} /></span></div><div className="mt-4 font-display text-3xl font-bold leading-none">{value}</div><p className="mt-2 text-xs text-muted-foreground">{note}</p></div>)}
    </div>
    <div className="mt-9 grid gap-7 xl:grid-cols-[minmax(0,1fr)_280px]">
      <section className="min-w-0"><div className="mb-4 flex items-end justify-between"><div><h2 className="font-display text-lg font-bold">Recent incidents</h2><p className="mt-1 text-xs text-muted-foreground">The latest activity in your incident log</p></div><Link to="/incidents" search={{}} className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline">View all <ArrowRight size={14} /></Link></div><IncidentTable incidents={[...incidents].reverse()} compact /></section>
      <aside><h2 className="mb-4 font-display text-lg font-bold">Quick access</h2><div className="space-y-3"><Link to="/incidents" search={{ new: "1" }} className="group flex items-start gap-3 rounded-md border border-border bg-card p-4 transition-colors hover:border-primary/40"><span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-accent text-primary"><Plus size={18} /></span><span className="flex-1"><span className="block text-sm font-bold">Log an incident</span><span className="mt-1 block text-xs leading-5 text-muted-foreground">Record and track a new security issue.</span></span><ArrowUpRight size={15} className="text-muted-foreground group-hover:text-primary" /></Link><Link to="/password" className="group flex items-start gap-3 rounded-md border border-border bg-card p-4 transition-colors hover:border-primary/40"><span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-info-soft text-info"><Fingerprint size={18} /></span><span className="flex-1"><span className="block text-sm font-bold">Check a password</span><span className="mt-1 block text-xs leading-5 text-muted-foreground">Review strength and get helpful feedback.</span></span><ArrowUpRight size={15} className="text-muted-foreground group-hover:text-primary" /></Link></div><div className="mt-5 border-l-2 border-primary pl-4"><p className="text-xs font-bold">Keep your records current</p><p className="mt-1 text-xs leading-5 text-muted-foreground">Update incident statuses as your team investigates and resolves them.</p></div></aside>
    </div>
  </AppShell>;
}
