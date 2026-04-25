const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ComplaintInput = {
  agency: string;
  system_name?: string;
  affected_service?: string;
  incident_description: string;
};

export type ComplaintResponse = {
  status: string;
  complaint_token: string;
  message: string;
};

export type ComplaintStatus = {
  token: string;
  status: string;
  agency: string;
};

export type Disclosure = {
  id?: string;
  agency_name: string;
  system_name: string;
  purpose?: string | null;
  vendor?: string | null;
  extraction_confidence?: number | null;
  disclosure_source_url?: string | null;
};

export type Signal = {
  id?: string;
  agency: string;
  system_name?: string | null;
  signal_type: string;
  severity: "low" | "medium" | "high";
  description?: string | null;
  disparity_ratio?: number | null;
  generated_at?: string | null;
};

export type AgencySummary = {
  id: string;
  name: string;
  description: string;
  disclosed_systems_count: number;
  active_signals_count: number;
  highest_severity: "low" | "medium" | "high" | null;
};

export type AgencyDetail = AgencySummary & {
  disclosures: Disclosure[];
  signals: Signal[];
};

const AGENCY_SEEDS = [
  {
    id: "acs",
    name: "Administration for Children's Services",
    description: "Child welfare and foster care services",
    aliases: ["acs", "administration for children's services"],
  },
  {
    id: "nypd",
    name: "NY Police Department",
    description: "Law enforcement and public safety",
    aliases: ["nypd", "ny police department", "new york police department"],
  },
  {
    id: "dhs",
    name: "Department of Homeless Services",
    description: "Homeless shelter and services",
    aliases: ["dhs", "department of homeless services"],
  },
  {
    id: "hra",
    name: "Human Resources Administration",
    description: "Benefits and social services administration",
    aliases: ["hra", "human resources administration"],
  },
];

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const detail = await res
      .json()
      .then((body) => body.detail)
      .catch(() => undefined);
    throw new Error(detail || `API error ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

function normalize(value: string | null | undefined): string {
  return (value || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function seedForAgency(value: string | null | undefined) {
  const normalized = normalize(value);
  return AGENCY_SEEDS.find((seed) => seed.aliases.some((alias) => normalize(alias) === normalized));
}

function seedForSlug(slug: string) {
  return AGENCY_SEEDS.find((seed) => seed.id === slug);
}

function highestSeverity(signals: Signal[]): "low" | "medium" | "high" | null {
  if (signals.some((signal) => signal.severity === "high")) return "high";
  if (signals.some((signal) => signal.severity === "medium")) return "medium";
  if (signals.some((signal) => signal.severity === "low")) return "low";
  return null;
}

export async function submitComplaint(data: ComplaintInput): Promise<ComplaintResponse> {
  return apiFetch<ComplaintResponse>("/complaints", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function getComplaintStatus(token: string): Promise<ComplaintStatus> {
  return apiFetch<ComplaintStatus>(`/complaints/${encodeURIComponent(token)}`);
}

export async function getDisclosures(): Promise<Disclosure[]> {
  return apiFetch<Disclosure[]>("/disclosures");
}

export async function getSignals(): Promise<Signal[]> {
  return apiFetch<Signal[]>("/signals");
}

export async function getAgencySummaries(): Promise<AgencySummary[]> {
  const [disclosures, signals] = await Promise.all([getDisclosures(), getSignals()]);

  return AGENCY_SEEDS.map((seed) => {
    const agencyDisclosures = disclosures.filter(
      (disclosure) => seedForAgency(disclosure.agency_name)?.id === seed.id,
    );
    const agencySignals = signals.filter((signal) => seedForAgency(signal.agency)?.id === seed.id);

    return {
      id: seed.id,
      name: seed.name,
      description: seed.description,
      disclosed_systems_count: agencyDisclosures.length,
      active_signals_count: agencySignals.length,
      highest_severity: highestSeverity(agencySignals),
    };
  });
}

export async function getAgencyDetail(slug: string): Promise<AgencyDetail | null> {
  const seed = seedForSlug(slug);
  if (!seed) return null;

  const [disclosures, signals] = await Promise.all([getDisclosures(), getSignals()]);
  const agencyDisclosures = disclosures.filter(
    (disclosure) => seedForAgency(disclosure.agency_name)?.id === seed.id,
  );
  const agencySignals = signals.filter((signal) => seedForAgency(signal.agency)?.id === seed.id);

  return {
    id: seed.id,
    name: seed.name,
    description: seed.description,
    disclosed_systems_count: agencyDisclosures.length,
    active_signals_count: agencySignals.length,
    highest_severity: highestSeverity(agencySignals),
    disclosures: agencyDisclosures,
    signals: agencySignals,
  };
}

export async function uploadDisclosure(
  file: File,
  agencyName: string,
  adminToken: string,
): Promise<Record<string, unknown>> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("agency_name", agencyName);

  return apiFetch<Record<string, unknown>>("/disclosures/upload", {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
    body: formData,
  });
}
