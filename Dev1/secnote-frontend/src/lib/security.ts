export type Severity = "Low" | "Medium" | "High" | "Critical";
export type Status = "Open" | "In Progress" | "Resolved" | "Closed";
export type Incident = {
  id: number;
  title: string;
  description: string;
  severity: Severity;
  status: Status;
  created_at: string;
  updated_at: string;
  tags?: string[];
};
export type NewIncident = Pick<Incident, "title" | "description" | "severity" | "status"> & { tags: string[] };

export function scorePassword(password: string) {
  let score = 0;
  const feedback: string[] = [];
  if (password.length < 8) feedback.push("Use at least 8 characters.");
  else if (password.length < 12) { score += 20; feedback.push("A longer password would be stronger."); }
  else score += 30;
  if (/[A-Z]/.test(password)) score += 15; else feedback.push("Add an uppercase letter.");
  if (/[a-z]/.test(password)) score += 15; else feedback.push("Add a lowercase letter.");
  if (/[0-9]/.test(password)) score += 15; else feedback.push("Add a number.");
  if (/[!@#$%^&*()\-_=+\[\]{}|;:'",.<>?/`~]/.test(password)) score += 15; else feedback.push("Add a special character.");
  if (password.length >= 16) score += 10;
  return { score, strength: score < 40 ? "Weak" : score < 70 ? "Moderate" : score < 90 ? "Strong" : "Very Strong", feedback };
}

export async function apiRequest<T>(baseUrl: string, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl.replace(/\/$/, "")}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(typeof payload?.detail === "string" ? payload.detail : `Request failed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}
