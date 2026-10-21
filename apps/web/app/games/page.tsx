import Link from "next/link";

import { DemoBanner } from "@/components/DemoBanner";
import {
  ApiError,
  fetchEvents,
  formatEventPrice,
  formatGameWhen,
  type DataStatus,
} from "@/lib/api";

type Props = {
  searchParams: Promise<{ team?: string; start?: string; end?: string }>;
};

export default async function GamesPage({ searchParams }: Props) {
  const { team, start, end } = await searchParams;
  let warning: string | null = null;
  let dataStatus: DataStatus = "DEMO";
  let events: Awaited<ReturnType<typeof fetchEvents>>["data"]["items"] = [];
  let total = 0;
  let loadError: string | null = null;

  try {
    const res = await fetchEvents({ team, start, end });
    events = res.data.items;
    total = res.data.pagination.total;
    warning = res.meta.warning;
    dataStatus = res.meta.data_status;
  } catch (err) {
    loadError =
      err instanceof ApiError
        ? `API error ${err.status}: ${err.message}`
        : "Could not load games from the API.";
  }

  const live = dataStatus === "LIVE" || dataStatus === "CACHED";
  const summary = team
    ? `Filtered by “${team}” · ${total} game${total === 1 ? "" : "s"}`
    : live
      ? `${total} games from Ticketmaster Discovery`
      : `${total} demo games from the fixture provider`;

  return (
    <main>
      <DemoBanner warning={warning} dataStatus={loadError ? "UNAVAILABLE" : dataStatus} />
      <div className="section-head">
        <div>
          <h2>Upcoming games</h2>
          <p>{loadError ? "Search could not be completed." : summary}</p>
        </div>
        <form className="search-form" action="/games" method="get">
          <label className="sr-only" htmlFor="team">
            Team
          </label>
          <input
            id="team"
            name="team"
            placeholder="Team, city, or abbrev"
            defaultValue={team ?? ""}
          />
          <label className="sr-only" htmlFor="start">
            Start date
          </label>
          <input id="start" name="start" type="date" defaultValue={start ?? ""} />
          <label className="sr-only" htmlFor="end">
            End date
          </label>
          <input id="end" name="end" type="date" defaultValue={end ?? ""} />
          <button className="btn btn-primary" type="submit">
            Search
          </button>
        </form>
      </div>

      {loadError ? (
        <div className="error-box" role="alert">
          {loadError}
        </div>
      ) : events.length === 0 ? (
        <div className="empty">
          {live
            ? "No games matched. Ticketmaster Discovery does not list every NBA game, and nothing is filled in from the demo catalog."
            : "No games matched that filter in DEMO data."}
        </div>
      ) : (
        <ul className="game-list">
          {events.map((event, index) => {
            const price = formatEventPrice(event);
            return (
              <li key={event.id} style={{ animationDelay: `${0.06 * index}s` }}>
                <Link className="game-row" href={`/games/${event.id}`}>
                  <div>
                    <h3>
                      {event.away_team.name} @ {event.home_team.name}
                    </h3>
                    <div className="meta">
                      {formatGameWhen(event.local_start_at, event.start_at_utc)} · {event.venue.name},{" "}
                      {event.venue.city}
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
      <style>{`.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}`}</style>
    </main>
  );
}
