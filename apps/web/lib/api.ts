/** Typed client for TicketHound API v1 contract. */

export type DataStatus = "LIVE" | "CACHED" | "DEMO" | "UNAVAILABLE";

export type ResponseMeta = {
  data_status: DataStatus;
  fetched_at: string;
  warning: string | null;
  demo_mode: boolean;
};

export type TeamSummary = {
  id: string;
  name: string;
  abbreviation: string;
  city: string;
};

export type VenueSummary = {
  id: string;
  name: string;
  city: string;
  state: string;
  timezone: string;
};

export type EventSummary = {
  id: string;
  league: string;
  home_team: TeamSummary;
  away_team: TeamSummary;
  venue: VenueSummary;
  start_at_utc: string;
  local_start_at: string;
  status: string;
  data_status: DataStatus;
  lowest_all_in_price_minor: number | null;
  currency: string | null;
};

export type Offer = {
  id: string;
  provider_code: string;
  section: string | null;
  row: string | null;
  seat_zone: string | null;
  ticket_count_for_price: number;
  all_in_price_minor: number | null;
  base_price_minor: number | null;
  currency: string;
  price_basis: string;
  granularity: string;
  purchase_url: string | null;
  observed_at: string;
  data_status: DataStatus;
};

export type ApiResponse<T> = {
  data: T;
  meta: ResponseMeta;
};

export type PaginatedEvents = {
  items: EventSummary[];
  pagination: { page: number; page_size: number; total: number };
};

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiBase(): string {
  // Server components may need a different reachability path than the browser
  // (e.g. host.docker.internal inside Compose bridge networks).
  if (typeof window === "undefined") {
    return (
      process.env.API_BASE_URL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "http://127.0.0.1:8000"
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    next: { revalidate: 0 },
    cache: "no-store",
  });
  if (!res.ok) {
    let code: string | undefined;
    try {
      const body = (await res.json()) as { error?: { code?: string; message?: string } };
      code = body.error?.code;
      throw new ApiError(body.error?.message ?? res.statusText, res.status, code);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(res.statusText, res.status);
    }
  }
  return res.json() as Promise<T>;
}

export function formatUsdFromMinor(minor: number | null | undefined): string {
  if (minor == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(minor / 100);
}

export function formatGameWhen(isoLocal: string, isoUtc: string): string {
  const d = new Date(isoLocal || isoUtc);
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(d);
}

export async function fetchEvents(team?: string): Promise<ApiResponse<PaginatedEvents>> {
  const params = new URLSearchParams();
  if (team) params.set("team", team);
  const q = params.toString();
  return getJson(`/api/v1/events${q ? `?${q}` : ""}`);
}

export async function fetchEvent(id: string): Promise<ApiResponse<EventSummary>> {
  return getJson(`/api/v1/events/${id}`);
}

export async function fetchOffers(
  id: string,
  quantity = 2,
): Promise<ApiResponse<Offer[]>> {
  return getJson(`/api/v1/events/${id}/offers?quantity=${quantity}`);
}

export async function fetchHealth(): Promise<{
  status: string;
  demo_mode: boolean;
  database: string;
}> {
  return getJson("/api/v1/health");
}
