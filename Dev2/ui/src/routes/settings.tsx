import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowUpRight,
  CheckCircle2,
  CircleAlert,
  Link2,
  Server,
} from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { AppButton } from "@/components/AppButton";
import { useIncidents } from "@/lib/use-incidents";
import { apiRequest } from "@/lib/security";
import {
  getServiceUrlConfiguration,
  saveServiceUrls,
} from "@/lib/service-urls";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Connection — secnote" },
      {
        name: "description",
        content:
          "Connect the secnote interface to its incident and password services.",
      },
      { property: "og:title", content: "Connection — secnote" },
      {
        property: "og:description",
        content:
          "Connect the secnote interface to its incident and password services.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const {
    url: incidentUrl,
    error: incidentError,
    ready,
    saveUrl,
  } = useIncidents();
  const [incidentDraft, setIncidentDraft] = useState<string | null>(null);
  const [passwordDraft, setPasswordDraft] = useState("");
  const [passwordReady, setPasswordReady] = useState(false);
  const [incidentsFromEnvironment, setIncidentsFromEnvironment] =
    useState(false);
  const [passwordFromEnvironment, setPasswordFromEnvironment] = useState(false);
  const [saved, setSaved] = useState(false);
  const [passwordError, setPasswordError] = useState("");
  const [invalid, setInvalid] = useState("");
  const incidentValue = incidentDraft ?? incidentUrl;

  useEffect(() => {
    try {
      const configuration = getServiceUrlConfiguration();
      setPasswordDraft(configuration.urls.password);
      setIncidentsFromEnvironment(configuration.incidentsFromEnvironment);
      setPasswordFromEnvironment(configuration.passwordFromEnvironment);
    } catch (cause) {
      setInvalid(
        cause instanceof Error
          ? cause.message
          : "Saved service URLs are invalid.",
      );
    } finally {
      setPasswordReady(true);
    }
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const incidents = incidentValue.trim();
    const password = passwordDraft.trim();
    const validUrl = (value: string) =>
      !value || /^https?:\/\/[^\s]+$/.test(value);
    if (!validUrl(incidents) || !validUrl(password)) {
      setInvalid("Enter full service URLs starting with http:// or https://.");
      return;
    }

    setInvalid("");
    setSaved(false);
    setPasswordError("");
    const urls = saveServiceUrls({ incidents, password });
    await saveUrl(urls.incidents);
    if (urls.password) {
      try {
        await apiRequest<{ status: string }>(
          urls.password,
          "/password/api/health",
        );
      } catch (cause) {
        setPasswordError(
          cause instanceof Error
            ? cause.message
            : "Unable to reach the password service.",
        );
      }
    }
    setSaved(true);
  }

  const isReady = ready && passwordReady;
  return (
    <AppShell
      title="Connection"
      subtitle="Configure the HTTP API URL for each service."
    >
      <div className="max-w-175">
        <div className="rounded-md border border-border bg-card p-6 sm:p-8">
          <div className="mb-7 flex size-11 items-center justify-center rounded-md bg-accent text-primary">
            <Server size={21} />
          </div>
          <h2 className="font-display text-lg font-bold">
            Service connections
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Enter the base URLs reachable from your browser. The incident
            service uses{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">
              /incidents
            </code>
            ; the password service uses{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">
              /password/api/check
            </code>
            .
          </p>
          <form className="mt-8 space-y-6" onSubmit={submit}>
            <div>
              <label
                htmlFor="incidents-url"
                className="mb-2 block text-xs font-bold"
              >
                Incident service URL
              </label>
              <div className="relative">
                <Link2
                  size={17}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                />
                <input
                  id="incidents-url"
                  type="url"
                  value={isReady ? incidentValue : ""}
                  readOnly={incidentsFromEnvironment}
                  onChange={(event) => {
                    setIncidentDraft(event.target.value);
                    setSaved(false);
                  }}
                  placeholder="http://localhost:8000"
                  className="h-11 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm outline-none placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/15 read-only:opacity-70"
                />
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                {incidentsFromEnvironment
                  ? "Managed by VITE_INCIDENTS_API_URL in the UI environment."
                  : "Leave blank to use preview incidents."}
              </p>
            </div>
            <div>
              <label
                htmlFor="password-url"
                className="mb-2 block text-xs font-bold"
              >
                Password service URL
              </label>
              <div className="relative">
                <Link2
                  size={17}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                />
                <input
                  id="password-url"
                  type="url"
                  value={passwordReady ? passwordDraft : ""}
                  readOnly={passwordFromEnvironment}
                  onChange={(event) => {
                    setPasswordDraft(event.target.value);
                    setSaved(false);
                    setPasswordError("");
                  }}
                  placeholder="http://localhost:8001"
                  className="h-11 w-full rounded-md border border-input bg-card pl-10 pr-4 text-sm outline-none placeholder:text-muted-foreground focus:border-primary focus:ring-2 focus:ring-primary/15 read-only:opacity-70"
                />
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                {passwordFromEnvironment
                  ? "Managed by VITE_PASSWORD_API_URL in the UI environment."
                  : "Leave blank to disable remote password checks. Both URLs can be the same when one server hosts both APIs."}
              </p>
            </div>
            {invalid && (
              <p role="alert" className="text-xs text-danger">
                {invalid}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-3">
              <AppButton type="submit" disabled={!isReady}>
                Save service URLs
              </AppButton>
              {saved && !incidentError && !passwordError && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-success">
                  <CheckCircle2 size={15} /> URLs saved.
                </span>
              )}
              {saved && (incidentError || passwordError) && (
                <span className="flex items-center gap-1.5 text-xs font-medium text-warning">
                  <CircleAlert size={15} /> URLs saved; check service
                  availability.
                </span>
              )}
            </div>
          </form>
        </div>
        <div className="mt-5 rounded-md border border-border bg-card p-6">
          <h3 className="text-sm font-bold">Connection status</h3>
          <div className="mt-4 space-y-4">
            <div className="flex items-start gap-3">
              {incidentUrl && !incidentError ? (
                <CheckCircle2
                  size={19}
                  className="mt-0.5 shrink-0 text-success"
                />
              ) : (
                <CircleAlert
                  size={19}
                  className="mt-0.5 shrink-0 text-warning"
                />
              )}
              <div>
                <p className="text-sm font-semibold">
                  Incidents:{" "}
                  {!incidentUrl
                    ? "Preview mode"
                    : incidentError
                      ? "Unable to connect"
                      : "Connected"}
                </p>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                  {!incidentUrl
                    ? "Add an incident service URL to load and manage live records."
                    : incidentError
                      ? incidentError
                      : "Incident records are loaded from the configured service."}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              {passwordDraft && !passwordError && saved ? (
                <CheckCircle2
                  size={19}
                  className="mt-0.5 shrink-0 text-success"
                />
              ) : (
                <CircleAlert
                  size={19}
                  className="mt-0.5 shrink-0 text-warning"
                />
              )}
              <div>
                <p className="text-sm font-semibold">
                  Password checks:{" "}
                  {!passwordDraft
                    ? "Not configured"
                    : passwordError
                      ? "Unable to connect"
                      : saved
                        ? "Connected"
                        : "Not checked"}
                </p>
                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                  {!passwordDraft
                    ? "Add a password service URL to enable server-side checks."
                    : passwordError ||
                      "The password API is checked when you save its URL."}
                </p>
              </div>
            </div>
          </div>
        </div>
        <a
          href="https://github.com/Palee222/DevOPS"
          target="_blank"
          rel="noreferrer"
          className="mt-6 inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
        >
          View the backend repository <ArrowUpRight size={14} />
        </a>
      </div>
    </AppShell>
  );
}
