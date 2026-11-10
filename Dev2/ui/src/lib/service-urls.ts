const SERVICE_URLS_KEY = "secnote-service-urls";
const INCIDENTS_URL_KEY = "secnote-api-url";

export type ServiceUrls = {
  incidents: string;
  password: string;
};

export type ServiceUrlConfiguration = {
  urls: ServiceUrls;
  incidentsFromEnvironment: boolean;
  passwordFromEnvironment: boolean;
};

const environmentUrls = {
  incidents:
    import.meta.env["VITE_INCIDENTS_API_URL"]?.trim().replace(/\/$/, "") ?? "",
  password:
    import.meta.env["VITE_PASSWORD_API_URL"]?.trim().replace(/\/$/, "") ?? "",
};

export function getServiceUrlConfiguration(): ServiceUrlConfiguration {
  const savedUrls = window.localStorage.getItem(SERVICE_URLS_KEY);
  let saved: ServiceUrls = {
    incidents: window.localStorage.getItem(INCIDENTS_URL_KEY) ?? "",
    password: "",
  };
  if (savedUrls) {
    try {
      const parsed: unknown = JSON.parse(savedUrls);
      if (
        typeof parsed !== "object" ||
        parsed === null ||
        Array.isArray(parsed)
      ) {
        throw new Error("Invalid saved service URLs.");
      }
      const values = parsed as { incidents?: unknown; password?: unknown };
      if (
        (values.incidents !== undefined &&
          typeof values.incidents !== "string") ||
        (values.password !== undefined && typeof values.password !== "string")
      ) {
        throw new Error("Invalid saved service URLs.");
      }
      saved = {
        incidents: typeof values.incidents === "string" ? values.incidents : "",
        password: typeof values.password === "string" ? values.password : "",
      };
    } catch {
      throw new Error(
        "Saved service URLs are invalid. Update them in Connection settings.",
      );
    }
  }

  return {
    urls: {
      incidents: environmentUrls.incidents || saved.incidents,
      password: environmentUrls.password || saved.password,
    },
    incidentsFromEnvironment: Boolean(environmentUrls.incidents),
    passwordFromEnvironment: Boolean(environmentUrls.password),
  };
}

export function getServiceUrls(): ServiceUrls {
  return getServiceUrlConfiguration().urls;
}

export function saveServiceUrls(urls: ServiceUrls) {
  const normalized = {
    incidents: urls.incidents.trim().replace(/\/$/, ""),
    password: urls.password.trim().replace(/\/$/, ""),
  };
  window.localStorage.setItem(SERVICE_URLS_KEY, JSON.stringify(normalized));
  window.localStorage.setItem(INCIDENTS_URL_KEY, normalized.incidents);
  return getServiceUrls();
}
