import type { DataStatus } from "@/lib/api";

const COPY: Record<DataStatus, { tag: string; fallback: string }> = {
  DEMO: {
    tag: "DEMO DATA",
    fallback:
      "Synthetic demonstration listings — not live marketplace prices and not purchasable.",
  },
  LIVE: {
    tag: "LIVE",
    fallback:
      "Ticketmaster Discovery event data. Prices, when shown, are event-level ranges, not seat listings.",
  },
  CACHED: {
    tag: "CACHED",
    fallback:
      "Stored Ticketmaster Discovery event. Prices, when shown, are event-level ranges, not seat listings.",
  },
  UNAVAILABLE: {
    tag: "UNAVAILABLE",
    fallback: "Event data is unavailable.",
  },
};

export function DemoBanner({
  warning,
  dataStatus = "DEMO",
}: {
  warning?: string | null;
  dataStatus?: DataStatus;
}) {
  const copy = COPY[dataStatus];
  const tone = dataStatus.toLowerCase();
  return (
    <div
      role="status"
      className={`demo-banner provenance-banner provenance-banner--${tone}`}
      aria-live="polite"
    >
      <span className="demo-banner__tag">{copy.tag}</span>
      <span>{warning ?? copy.fallback}</span>
    </div>
  );
}
