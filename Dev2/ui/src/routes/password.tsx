import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Check, Eye, EyeOff, Fingerprint, Info, LockKeyhole, ShieldCheck, X } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { AppButton } from "@/components/AppButton";
import { scorePassword } from "@/lib/security";

export const Route = createFileRoute("/password")({
  head: () => ({ meta: [{ title: "Password check — secnote" }, { name: "description", content: "Check password strength and see practical recommendations in secnote." }, { property: "og:title", content: "Password check — secnote" }, { property: "og:description", content: "Check password strength and see practical recommendations in secnote." }, { property: "og:type", content: "website" }, { name: "twitter:card", content: "summary_large_image" }] }),
  component: PasswordPage,
});
const checks = [
  { label: "At least 8 characters", test: (value: string) => value.length >= 8 },
  { label: "One uppercase letter", test: (value: string) => /[A-Z]/.test(value) },
  { label: "One lowercase letter", test: (value: string) => /[a-z]/.test(value) },
  { label: "One number", test: (value: string) => /[0-9]/.test(value) },
  { label: "One special character", test: (value: string) => /[!@#$%^&*()\-_=+\[\]{}|;:'",.<>?/`~]/.test(value) },
];
function PasswordPage() {
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const result = password ? scorePassword(password) : null;
  const scoreColor = result ? result.score < 40 ? "bg-danger" : result.score < 70 ? "bg-warning" : result.score < 90 ? "bg-info" : "bg-success" : "bg-border";
  return <AppShell title="Password check" subtitle="Check password strength against the current scoring rules.">
    <div className="grid max-w-275 gap-7 lg:grid-cols-[minmax(0,1fr)_320px]">
      <section className="min-w-0 rounded-md border border-border bg-card p-6 sm:p-8"><div className="mb-7 flex size-11 items-center justify-center rounded-md bg-accent text-primary"><Fingerprint size={23} /></div><h2 className="font-display text-lg font-bold">Check a password</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">Enter a password to see its strength and what could be improved.</p><div className="mt-8"><label htmlFor="password-input" className="mb-2 block text-xs font-bold">Password</label><div className="relative"><input id="password-input" type={visible ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="off" spellCheck={false} placeholder="Enter a password to check" className="h-12 w-full rounded-md border border-input bg-card px-4 pr-12 text-sm outline-none placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/15" /><AppButton variant="ghost" size="icon" className="absolute right-1.5 top-1.5" onClick={() => setVisible((current) => !current)} aria-label={visible ? "Hide password" : "Show password"}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</AppButton></div></div>
        <div className="mt-8 border-t border-border pt-7"><div className="flex items-end justify-between"><div><p className="text-xs font-semibold text-muted-foreground">Strength score</p><p className="mt-2 font-display text-4xl font-bold">{result ? result.score : "—"}<span className="ml-1 text-sm font-medium text-muted-foreground">/ 100</span></p></div><span className={`mb-1 text-xs font-bold ${result ? result.score < 40 ? "text-danger" : result.score < 70 ? "text-warning" : result.score < 90 ? "text-info" : "text-success" : "text-muted-foreground"}`}>{result?.strength ?? "Not checked"}</span></div><div className="mt-5 h-2 overflow-hidden rounded-full bg-muted" role="progressbar" aria-label="Password strength" aria-valuenow={result?.score ?? 0} aria-valuemin={0} aria-valuemax={100}><div className={`h-full rounded-full transition-all duration-300 ${scoreColor}`} style={{ width: `${result?.score ?? 0}%` }} /></div>{result && <div className="mt-7"><h3 className="text-xs font-bold uppercase tracking-[0.08em] text-muted-foreground">{result.feedback.length ? "Suggestions" : "Looking good"}</h3>{result.feedback.length ? <ul className="mt-3 space-y-3">{result.feedback.map((item) => <li key={item} className="flex items-start gap-2 text-sm text-foreground"><Info size={15} className="mt-0.5 shrink-0 text-warning" />{item}</li>)}</ul> : <p className="mt-3 flex items-center gap-2 text-sm text-success"><ShieldCheck size={17} /> This password meets all scoring checks.</p>}</div>}</div>
      </section>
      <aside className="space-y-5"><div className="rounded-md border border-border bg-card p-6"><h2 className="font-display text-base font-bold">Password guidelines</h2><p className="mt-1 text-xs leading-5 text-muted-foreground">The checks used in the backend's scoring logic.</p><ul className="mt-6 space-y-4">{checks.map(({ label, test }) => <li key={label} className="flex items-center gap-3 text-sm"><span className={`flex size-5 shrink-0 items-center justify-center rounded-full ${password && test(password) ? "bg-success-soft text-success" : "bg-muted text-muted-foreground"}`}>{password && test(password) ? <Check size={12} strokeWidth={3} /> : <X size={11} strokeWidth={2.5} />}</span>{label}</li>)}</ul><div className="mt-6 border-t border-border pt-5 text-xs leading-5 text-muted-foreground">A password with 12+ characters earns a higher length score; 16+ adds a bonus.</div></div><div className="flex items-start gap-3 rounded-md border border-primary/15 bg-accent p-5 text-accent-foreground"><LockKeyhole size={19} className="mt-0.5 shrink-0" /><div><p className="text-xs font-bold">Checked in your browser</p><p className="mt-1 text-xs leading-5">Your password is not sent to the incident server or saved by this page.</p></div></div></aside>
    </div>
  </AppShell>;
}
