import { useEffect, useState } from "react";
import { apiRequest } from "./security";
import { getServiceUrls } from "./service-urls";

export type PasswordCheck = {
  score: number;
  strength: "Weak" | "Moderate" | "Strong" | "Very Strong";
  feedback: string[];
  incident_report?: {
    status: "not_requested" | "not_needed" | "created" | "unavailable";
    incident_id: number | null;
  };
};

export function usePasswordChecker() {
  const [url, setUrl] = useState("");
  const [ready, setReady] = useState(false);
  const [configurationError, setConfigurationError] = useState("");

  useEffect(() => {
    try {
      setUrl(getServiceUrls().password);
    } catch (cause) {
      setConfigurationError(
        cause instanceof Error
          ? cause.message
          : "Saved service URLs are invalid.",
      );
    } finally {
      setReady(true);
    }
  }, []);

  async function check(password: string, reportAsIncident = false) {
    if (!url)
      throw new Error(
        "Connect the password service in Connection settings first.",
      );
    return apiRequest<PasswordCheck>(url, "/password/api/check", {
      method: "POST",
      body: JSON.stringify({
        password,
        report_as_incident: reportAsIncident,
      }),
    });
  }

  return { url, ready, configurationError, check };
}
