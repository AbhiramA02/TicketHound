import Link from "next/link";
import { notFound } from "next/navigation";

import { DemoBanner } from "@/components/DemoBanner";
import {
  ApiError,
  fetchEvent,
  fetchOffers,
  formatEventPrice,
  formatGameWhen,
  formatObserved,
  formatUsdFromMinor,
  type EventSummary,
  type Offer,
  type ResponseMeta,
} from "@/lib/api";

type Props = {
  params: Promise<{ id: string }>;
};

export default async function GameDetailPage({ params }: Props) {
  const { id } = await params;

  let event: EventSummary | null = null;
  let offers: Offer[] = [];
  let meta: ResponseMeta | null = null;
  let offerWarning: string | null = null;
  let loadError: string | null = null;
  let missing = false;

  try {
    const [eventRes, offersRes] = await Promise.all([fetchEvent(id), fetchOffers(id, 2)]);
    event = eventRes.data;
    offers = offersRes.data;
    meta = eventRes.meta;
    offerWarning = offersRes.meta.warning;
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      missing = true;
    } else {
      loadError =
        err instanceof ApiError
          ? `Failed to load game: ${err.message}`
          : "Failed to load game detail.";
    }
  }

  if (missing) notFound();

  if (loadError || !event) {
    return (
      <main>
        <DemoBanner dataStatus="UNAVAILABLE" warning={loadError} />
        <div className="error-box" role="alert">
          {loadError ?? "Failed to load game detail."}
        </div>
      </main>
    );
  }

  const eventLevel = offers.some((offer) => offer.granularity === "EVENT");
  const price = formatEventPrice(event);
  const source =
    event.data_status === "DEMO"
      ? "Source: DEMO fixture"
      : `Source: Ticketmaster Discovery · observed ${formatObserved(event.source_observed_at)}`;

  return (
    <main>
      <DemoBanner warning={meta?.warning} dataStatus={meta?.data_status ?? event.data_status} />
      <div className="detail-header">
        <Link href="/games" className="meta">
          ← All games
        </Link>
        <h1>
          {event.away_team.abbreviation} @ {event.home_team.abbreviation}
        </h1>
        <p className="meta">
          {event.away_team.name} at {event.home_team.name}
          <br />
          {formatGameWhen(event.local_start_at, event.start_at_utc)} · {event.venue.name},{" "}
          {event.venue.city} {event.venue.state}
          <br />
          {source}
          {event.season_type ? ` · ${event.season_type}` : ""}
        </p>
        <span className="status-pill">{event.data_status}</span>
      </div>

      <div className="section-head">
        <div>
          <h2>{eventLevel ? "Event-level price" : "Offers (qty 2)"}</h2>
          <p>
            {eventLevel
              ? "Ticketmaster Discovery published an event-level price range. This is not a section, row, or seat listing."
              : event.data_status === "DEMO"
                ? "All rows are DEMO — purchase links disabled in Phase 0."
                : (offerWarning ?? "No seat-level listings are available from this source.")}
          </p>
        </div>
        <div className="price">
          {price.amount}
          <small>{price.caption}</small>
        </div>
      </div>

      {offers.length === 0 ? (
        <div className="empty">{offerWarning ?? "No offers for this quantity."}</div>
      ) : (
        <table className="offer-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Section</th>
              <th>Row</th>
              <th>Zone</th>
              <th>{eventLevel ? "Range min" : "All-in"}</th>
              <th>Basis</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => (
              <tr key={offer.id}>
                <td>{offer.provider_code}</td>
                <td>{offer.section ?? "—"}</td>
                <td>{offer.row ?? "—"}</td>
                <td>{offer.seat_zone ?? "—"}</td>
                <td>
                  {formatUsdFromMinor(
                    offer.granularity === "EVENT" ? offer.base_price_minor : offer.all_in_price_minor,
                  )}
                </td>
                <td>
                  {offer.price_basis}
                  {offer.granularity === "EVENT" ? " · EVENT" : ""}
                </td>
                <td>
                  <span className="status-pill">{offer.data_status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {event.source_url ? (
        <p className="meta">
          <a href={event.source_url}>View the event on Ticketmaster</a>
        </p>
      ) : null}
    </main>
  );
}
