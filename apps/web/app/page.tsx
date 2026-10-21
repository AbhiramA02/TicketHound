import Link from "next/link";

import { DemoBanner } from "@/components/DemoBanner";
import {
  ApiError,
  fetchEvents,
  formatEventPrice,
  formatGameWhen,
  type DataStatus,
} from "@/lib/api";

export default async function HomePage() {
  let warning: string | null =
    "Synthetic demonstration data — not purchasable tickets.";
  let dataStatus: DataStatus = "DEMO";
  let events: Awaited<ReturnType<typeof fetchEvents>>["data"]["items"] = [];
  let loadError: string | null = null;

  try {
    const res = await fetchEvents();
    events = res.data.items.slice(0, 3);
    warning = res.meta.warning;
    dataStatus = res.meta.data_status;
  } catch (err) {
    loadError =
      err instanceof ApiError
        ? `API unavailable (${err.status}). Start the FastAPI service on port 8000.`
        : "Could not reach the TicketHound API.";
  }

  const live = dataStatus === "LIVE" || dataStatus === "CACHED";

  return (
    <main>
      <DemoBanner warning={warning} dataStatus={dataStatus} />
      <section className="hero">
        <h1>TicketHound</h1>
        <p>
          Stop opening five tabs to buy NBA tickets. Compare upcoming games with honest
          provenance — demo fixtures stay labeled, and Ticketmaster Discovery supplies real
          events only when it is configured.
        </p>
        <div className="cta-row">
          <Link className="btn btn-primary" href="/games">
            {live ? "Browse games" : "Browse demo games"}
          </Link>
          <Link className="btn btn-ghost" href="/games?team=Lakers">
            Filter Lakers
          </Link>
        </div>
      </section>

      <section>
        <div className="section-head">
          <div>
            <h2>{live ? "Upcoming games" : "Featured demo games"}</h2>
            <p>
              {live
                ? "From Ticketmaster Discovery. A missing game means the source did not return it."
                : "From the isolated DEMO provider — never labeled LIVE."}
            </p>
          </div>
        </div>
        {loadError ? (
          <div className="error-box" role="alert">
            {loadError}
          </div>
        ) : events.length === 0 ? (
          <div className="empty">
            {live ? "No games returned for this search." : "No demo events returned."}
          </div>
        ) : (
          <ul className="game-list">
            {events.map((event, index) => {
              const price = formatEventPrice(event);
              return (
                <li key={event.id} style={{ animationDelay: `${0.08 * index}s` }}>
                  <Link className="game-row" href={`/games/${event.id}`}>
                    <div>
                      <h3>
                        {event.away_team.abbreviation} @ {event.home_team.abbreviation}
                      </h3>
                      <div className="meta">
                        {event.away_team.name} at {event.home_team.name} ·{" "}
                        {formatGameWhen(event.local_start_at, event.start_at_utc)} ·{" "}
                        {event.venue.name}
                      </div>
                      <span className="status-pill">{event.data_status}</span>
                    </div>
                    <div className="price">
                      {price.amount}
                      <small>{price.caption}</small>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </main>
  );
}
