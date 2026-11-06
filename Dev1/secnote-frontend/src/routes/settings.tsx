import { createFileRoute } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";
import { ArrowUpRight, CheckCircle2, CircleAlert, Link2, Server } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { AppButton } from "@/components/AppButton";
import { useIncidents } from "@/lib/use-incidents";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Connection — secnote" }, { name: "description", content: "Connect the secnote interface to your incident backend." }, { property: "og:title", content: "Connection — secnote" }, { property: "og:description", content: "Connect the secnote interface to your incident backend." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" }] }),
  component: SettingsPage,
});
function SettingsPage() {
  const { url, error, ready, saveUrl } = useIncidents();
  const [draft, setDraft] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [invalid, setInvalid] = useState("");
  const value = draft ?? url;
  async function submit(event: FormEvent) {
    event.preventDefault();
    const next = value.trim();
    if (next && !/^https?:\/\/[^\s]+$/.test(next)) { setInvalid("Enter a full URL starting with http:// or https://."); return; }
    setInvalid(""); setSaved(false);
    await saveUrl(next);
    setSaved(true);
  }
  return <AppShell title="Connection" subtitle="Link secnote to your existing incident backend.">
    <div className="max-w-175"><div className="rounded-md border border-border bg-card p-6 sm:p-8"><div className="mb-7 flex size-11 items-center justify-center rounded-md bg-accent text-primary"><Server size={21} /></div><h2 className="font-display text-lg font-bold">Backend connection</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Enter the URL where your FastAPI app is running. Incident records will then load from its <code className="rounded bg-muted px-1 py-0.5 text-xs">/incidents</code> endpoint.</p><form className="mt-8" onSubmit={submit}><label htmlFor="backend-url" className="mb-2 block text-xs font-bold">Backend URL</label><div className="relative"><Link2 size={17} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" /><input id="backend-url" type="url" value={ready ? value : ""} onChange={(e) => { setDraft(e.target.value); setSaved(false); }} placeholder="http://localhost:8000" className="h-11 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm outline-none placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/15" /></div><p className="mt-2 text-xs leading-5 text-muted-foreground">Use an address accessible from your browser. Leave blank to return to preview data.</p>{invalid && <p role="alert" className="mt-3 text-xs text-danger">{invalid}</p>}<div className="mt-6 flex items-center gap-3"><AppButton type="submit">Save connection</AppButton>{saved && !error && <span className="flex items-center gap-1.5 text-xs font-medium text-success"><CheckCircle2 size={15} /> Connected</span>}</div></form></div>
      <div className="mt-5 rounded-md border border-border bg-card p-6"><h3 className="text-sm font-bold">Connection status</h3><div className="mt-4 flex items-start gap-3">{url && !error ? <CheckCircle2 size={19} className="mt-0.5 shrink-0 text-success" /> : <CircleAlert size={19} className="mt-0.5 shrink-0 text-warning" />}<div><p className="text-sm font-semibold">{!url ? "Preview mode" : error ? "Unable to connect" : "Backend connected"}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{!url ? "You are viewing sample incidents. Add your backend URL above to work with real data." : error ? `The server could not be reached: ${error}. Make sure it is running and allows requests from this site.` : "Incident records are loading from your configured backend."}</p></div></div></div>
      <a href="https://github.com/Palee222/DevOPS" target="_blank" rel="noreferrer" className="mt-6 inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline">View the backend repository <ArrowUpRight size={14} /></a>
    </div>
  </AppShell>;
}
