import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState, type FormEvent } from "react";
import { ArrowLeft, Plus, Search, X } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { AppButton } from "@/components/AppButton";
import { ErrorNotice, formatDate, IncidentTable, PreviewNotice, SeverityBadge, StatusLabel } from "@/components/IncidentUI";
import { useIncidents } from "@/lib/use-incidents";
import type { Incident, Severity, Status } from "@/lib/security";

export const Route = createFileRoute("/incidents")({
  head: () => ({ meta: [{ title: "Incidents — secnote" }, { name: "description", content: "Track, search, and update security incidents in secnote." }, { property: "og:title", content: "Incidents — secnote" }, { property: "og:description", content: "Track, search, and update security incidents in secnote." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" }] }),
  validateSearch: (search: Record<string, unknown>): { new?: string } => search["new"] === "1" ? { new: "1" } : {},
  component: IncidentsPage,
});
const statuses: Status[] = ["Open", "In Progress", "Resolved", "Closed"];
const severities: Severity[] = ["Low", "Medium", "High", "Critical"];
const field = "w-full rounded-md border border-input bg-card px-3 py-2.5 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/15";
function IncidentsPage() {
  const search = Route.useSearch();
  const { incidents, url, error, ready, refresh, create, updateStatus } = useIncidents();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All incidents");
  const [selected, setSelected] = useState<Incident | null>(null);
  const [creating, setCreating] = useState(search.new === "1");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<Severity>("Medium");
  const [tags, setTags] = useState("");
  const filtered = useMemo(() => [...incidents].reverse().filter((incident) => (filter === "All incidents" || incident.status === filter) && `${incident.title} ${incident.description} ${incident.id}`.toLowerCase().includes(query.toLowerCase())), [incidents, filter, query]);
  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setFormError("");
    try { await create({ title: title.trim(), description: description.trim(), severity, status: "Open", tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean) }); setCreating(false); setTitle(""); setDescription(""); setTags(""); }
    catch (cause) { setFormError(cause instanceof Error ? cause.message : "Unable to save incident."); }
    finally { setSaving(false); }
  }
  async function changeStatus(status: Status) {
    if (!selected) return;
    setSaving(true); setFormError("");
    try { setSelected(await updateStatus(selected.id, status)); }
    catch (cause) { setFormError(cause instanceof Error ? cause.message : "Unable to update incident."); }
    finally { setSaving(false); }
  }
  return <AppShell title="Incidents" subtitle="Track and manage your security incidents in one place." action={<AppButton onClick={() => { setFormError(""); setCreating(true); }}><Plus size={16} /> New incident</AppButton>}>
    {ready && !url && <PreviewNotice />}{error && <ErrorNotice message={error} onRetry={refresh} />}
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="relative w-full sm:max-w-82"><Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search incidents..." aria-label="Search incidents" className={`${field} pl-10`} /></div><select className={`${field} sm:w-43`} aria-label="Filter by status" value={filter} onChange={(e) => setFilter(e.target.value)}><option>All incidents</option>{statuses.map((status) => <option key={status}>{status}</option>)}</select></div>
    <IncidentTable incidents={filtered} onSelect={(incident) => { setSelected(incident); setFormError(""); }} />
    <p className="mt-4 text-xs text-muted-foreground">Showing {filtered.length} of {incidents.length} incidents</p>
    {(creating || selected) && <div className="fixed inset-0 z-50 flex justify-end bg-shell/55" onMouseDown={(event) => { if (event.target === event.currentTarget) { setCreating(false); setSelected(null); } }}><section role="dialog" aria-modal="true" aria-label={creating ? "New incident" : "Incident details"} className="app-scrollbar flex h-full w-full max-w-lg flex-col overflow-y-auto bg-card shadow-xl"><div className="flex items-center justify-between border-b border-border px-6 py-5"><div><p className="text-[11px] font-bold uppercase tracking-[0.12em] text-primary">Incident log</p><h2 className="mt-1 font-display text-xl font-bold">{creating ? "New incident" : `INC-${selected?.id}`}</h2></div><AppButton variant="ghost" size="icon" onClick={() => { setCreating(false); setSelected(null); }} aria-label="Close panel"><X size={20} /></AppButton></div>
      {creating ? <form className="flex flex-1 flex-col" onSubmit={submit}><div className="space-y-5 px-6 py-7"><div><label htmlFor="incident-title" className="mb-2 block text-xs font-bold">Incident title</label><input id="incident-title" required maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Briefly describe what happened" className={field} /></div><div><label htmlFor="incident-description" className="mb-2 block text-xs font-bold">Description</label><textarea id="incident-description" required rows={6} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Add relevant details about the incident..." className={field} /></div><div><label htmlFor="incident-severity" className="mb-2 block text-xs font-bold">Severity</label><select id="incident-severity" className={field} value={severity} onChange={(e) => setSeverity(e.target.value as Severity)}>{severities.map((item) => <option key={item}>{item}</option>)}</select></div><div><label htmlFor="incident-tags" className="mb-2 block text-xs font-bold">Tags <span className="font-normal text-muted-foreground">(optional)</span></label><input id="incident-tags" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="e.g. Access, Phishing" className={field} /><p className="mt-1.5 text-xs text-muted-foreground">Separate multiple tags with commas.</p></div>{formError && <p role="alert" className="text-sm text-danger">{formError}</p>}{!url && <p className="rounded-md bg-info-soft p-3 text-xs text-info">Connect your backend before saving a real incident. <Link to="/settings" className="font-bold underline">Connection settings</Link></p>}</div><div className="mt-auto flex justify-end gap-2 border-t border-border p-5"><AppButton type="button" variant="outline" onClick={() => setCreating(false)}>Cancel</AppButton><AppButton type="submit" disabled={saving || !url}>{saving ? "Saving..." : "Create incident"}</AppButton></div></form> : selected && <div className="space-y-7 px-6 py-7"><div><h3 className="font-display text-xl font-bold leading-snug">{selected.title}</h3><p className="mt-2 text-xs text-muted-foreground">Created {formatDate(selected.created_at)}</p></div><div className="flex gap-10"><div><p className="mb-2 text-xs font-semibold text-muted-foreground">Severity</p><SeverityBadge severity={selected.severity} /></div><div><p className="mb-2 text-xs font-semibold text-muted-foreground">Status</p><StatusLabel status={selected.status} /></div></div><div className="border-t border-border pt-6"><h4 className="mb-2 text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">Description</h4><p className="whitespace-pre-wrap text-sm leading-7">{selected.description}</p></div>{selected.tags && selected.tags.length > 0 && <div><h4 className="mb-3 text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">Tags</h4><div className="flex flex-wrap gap-2">{selected.tags.map((tag) => <span key={tag} className="rounded bg-secondary px-2.5 py-1 text-xs text-secondary-foreground">{tag}</span>)}</div></div>}<div className="border-t border-border pt-6"><label htmlFor="status-update" className="mb-2 block text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">Update status</label><select id="status-update" value={selected.status} disabled={!url || saving} onChange={(e) => void changeStatus(e.target.value as Status)} className={field}>{statuses.map((status) => <option key={status}>{status}</option>)}</select>{!url && <p className="mt-2 text-xs text-muted-foreground">Connect your backend to update status.</p>}{formError && <p role="alert" className="mt-2 text-xs text-danger">{formError}</p>}</div><AppButton variant="ghost" size="sm" onClick={() => setSelected(null)}><ArrowLeft size={14} /> Back to incidents</AppButton></div>}
    </section></div>}
  </AppShell>;
}
