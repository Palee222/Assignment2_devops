import { useCallback, useEffect, useState } from "react";
import { apiRequest, type Incident, type NewIncident, type Status } from "./security";

const previewIncidents: Incident[] = [
  { id: 1042, title: "Unusual sign-in activity detected", description: "Multiple sign-in attempts were observed from an unrecognized location. Review the access logs and confirm whether the account owner initiated the activity.", severity: "Critical", status: "Open", created_at: "2026-09-26 09:24:00", updated_at: "2026-09-26 09:24:00", tags: ["Authentication", "Access"] },
  { id: 1041, title: "Outdated dependency identified", description: "A routine scan flagged a dependency that should be reviewed and updated.", severity: "High", status: "In Progress", created_at: "2026-09-25 14:12:00", updated_at: "2026-09-25 14:12:00", tags: ["Infrastructure"] },
  { id: 1040, title: "Suspicious email reported", description: "A team member reported a message requesting credentials from an unknown sender.", severity: "Medium", status: "Resolved", created_at: "2026-09-24 11:38:00", updated_at: "2026-09-24 11:38:00", tags: ["Phishing"] },
  { id: 1039, title: "Device encryption check", description: "The scheduled device compliance review was completed.", severity: "Low", status: "Closed", created_at: "2026-09-22 16:05:00", updated_at: "2026-09-22 16:05:00", tags: ["Devices"] },
  { id: 1038, title: "Unexpected file sharing permission", description: "Review sharing permissions on a document containing internal information.", severity: "High", status: "Open", created_at: "2026-09-21 08:45:00", updated_at: "2026-09-21 08:45:00", tags: ["Access"] },
];

const STORAGE_KEY = "secnote-api-url";
export function useIncidents() {
  const [url, setUrl] = useState("");
  const [incidents, setIncidents] = useState<Incident[]>(previewIncidents);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [ready, setReady] = useState(false);

  const refresh = useCallback(async (apiUrl: string) => {
    if (!apiUrl) { setIncidents(previewIncidents); setError(""); setLoading(false); return; }
    setLoading(true);
    try { setIncidents(await apiRequest<Incident[]>(apiUrl, "/incidents")); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to reach the server."); setIncidents([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const savedUrl = window.localStorage.getItem(STORAGE_KEY) ?? "";
    setUrl(savedUrl);
    setReady(true);
    void refresh(savedUrl);
  }, [refresh]);

  const saveUrl = async (value: string) => {
    const normalized = value.trim().replace(/\/$/, "");
    window.localStorage.setItem(STORAGE_KEY, normalized);
    setUrl(normalized);
    await refresh(normalized);
  };
  const create = async (data: NewIncident) => {
    if (!url) throw new Error("Connect your backend before creating an incident.");
    const result = await apiRequest<Incident>(url, "/incidents", { method: "POST", body: JSON.stringify(data) });
    await refresh(url);
    return result;
  };
  const updateStatus = async (id: number, status: Status) => {
    if (!url) throw new Error("Connect your backend before updating an incident.");
    const result = await apiRequest<Incident>(url, `/incidents/${id}/status`, { method: "POST", body: JSON.stringify({ status }) });
    await refresh(url);
    return result;
  };
  return { url, incidents, loading, error, ready, refresh: () => refresh(url), saveUrl, create, updateStatus };
}
