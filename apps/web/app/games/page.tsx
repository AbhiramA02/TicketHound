import Link from "next/link";

import { DemoBanner } from "@/components/DemoBanner";
import { ApiError, fetchEvents, formatGameWhen, formatUsdFromMinor } from "@/lib/api";

type Props = {
  searchParams: Promise<{ team?: string }>;
};

export default async function GamesPage({ searchParams }: Props) {
  const { team } = await searchParams;
  let warning: string | null = null;
  let events: Awaited<ReturnType<typeof fetchEvents>>["data"]["items"] = [];
  let total = 0;
  let loadError: string | null = null;

  try {
    const res = await fetchEvents(team);
    events = res.data.items;
    total = res.data.pagination.total;
    warning = res.meta.warning;
  } catch (err) {
    loadError =
      err instanceof ApiError
        ? `API error ${err.status}: ${err.message}`
        : "Could not load games from the API.";
  }

  return (
    <main>
      <DemoBanner warning={warning} />
      <div className="section-head">
        <div>
          <h2>Upcoming games</h2>
          <p>
            {team
              ? `Filtered by “${team}” · ${total} demo match${total === 1 ? "" : "es"}`
              : `${total} demo games from the fixture provider`}
          </p>
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
        <div className="empty">No games matched that filter in DEMO data.</div>
      ) : (
        <ul className="game-list">
          {events.map((event, index) => (
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
                  {formatUsdFromMinor(event.lowest_all_in_price_minor)}
                  <small>DEMO all-in from</small>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <style>{`.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}`}</style>
    </main>
  );
}
