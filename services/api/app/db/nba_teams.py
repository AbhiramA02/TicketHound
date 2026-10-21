"""Canonical NBA directory used for matching and the teams API.

Stable UUIDs match the Phase 1 seed migration. Aliases are a controlled list:
city alone is not an alias, because Los Angeles is shared by two teams.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


def _id(n: int) -> UUID:
    return UUID(f"aaaaaaaa-aaaa-4aaa-8aaa-{n:012d}")


@dataclass(frozen=True)
class NbaTeam:
    id: UUID
    nba_team_id: str
    name: str
    abbreviation: str
    city: str
    aliases: tuple[str, ...]

    def row(self) -> dict[str, object]:
        return {
            "id": self.id,
            "nba_team_id": self.nba_team_id,
            "name": self.name,
            "abbreviation": self.abbreviation,
            "city": self.city,
            "aliases": ", ".join(self.aliases),
            "active": "true",
        }


def _team(n: int, code: str, name: str, city: str, aliases: str) -> NbaTeam:
    return NbaTeam(_id(n), code, name, code, city, tuple(aliases.split("|")))


NBA_TEAMS: tuple[NbaTeam, ...] = (
    _team(1, "ATL", "Atlanta Hawks", "Atlanta", "atlanta hawks|hawks|atl"),
    _team(2, "BOS", "Boston Celtics", "Boston", "boston celtics|celtics|bos"),
    _team(3, "BKN", "Brooklyn Nets", "Brooklyn", "brooklyn nets|nets|bkn|brk"),
    _team(4, "CHA", "Charlotte Hornets", "Charlotte", "charlotte hornets|hornets|cha|cho"),
    _team(5, "CHI", "Chicago Bulls", "Chicago", "chicago bulls|bulls|chi"),
    _team(6, "CLE", "Cleveland Cavaliers", "Cleveland", "cleveland cavaliers|cavaliers|cavs|cle"),
    _team(7, "DAL", "Dallas Mavericks", "Dallas", "dallas mavericks|mavericks|mavs|dal"),
    _team(8, "DEN", "Denver Nuggets", "Denver", "denver nuggets|nuggets|den"),
    _team(9, "DET", "Detroit Pistons", "Detroit", "detroit pistons|pistons|det"),
    _team(
        10,
        "GSW",
        "Golden State Warriors",
        "San Francisco",
        "golden state warriors|golden state|warriors|gsw|gs warriors",
    ),
    _team(11, "HOU", "Houston Rockets", "Houston", "houston rockets|rockets|hou"),
    _team(12, "IND", "Indiana Pacers", "Indianapolis", "indiana pacers|pacers|ind"),
    _team(
        13,
        "LAC",
        "LA Clippers",
        "Los Angeles",
        "la clippers|los angeles clippers|clippers|lac",
    ),
    _team(
        14,
        "LAL",
        "Los Angeles Lakers",
        "Los Angeles",
        "los angeles lakers|la lakers|lakers|lal",
    ),
    _team(15, "MEM", "Memphis Grizzlies", "Memphis", "memphis grizzlies|grizzlies|mem"),
    _team(16, "MIA", "Miami Heat", "Miami", "miami heat|heat|mia"),
    _team(17, "MIL", "Milwaukee Bucks", "Milwaukee", "milwaukee bucks|bucks|mil"),
    _team(
        18,
        "MIN",
        "Minnesota Timberwolves",
        "Minneapolis",
        "minnesota timberwolves|timberwolves|wolves|min",
    ),
    _team(19, "NOP", "New Orleans Pelicans", "New Orleans", "new orleans pelicans|pelicans|nop"),
    _team(20, "NYK", "New York Knicks", "New York", "new york knicks|ny knicks|knicks|nyk"),
    _team(21, "OKC", "Oklahoma City Thunder", "Oklahoma City", "oklahoma city thunder|thunder|okc"),
    _team(22, "ORL", "Orlando Magic", "Orlando", "orlando magic|magic|orl"),
    _team(23, "PHI", "Philadelphia 76ers", "Philadelphia", "philadelphia 76ers|76ers|sixers|phi"),
    _team(24, "PHX", "Phoenix Suns", "Phoenix", "phoenix suns|suns|phx|pho"),
    _team(
        25,
        "POR",
        "Portland Trail Blazers",
        "Portland",
        "portland trail blazers|trail blazers|blazers|por",
    ),
    _team(26, "SAC", "Sacramento Kings", "Sacramento", "sacramento kings|kings|sac"),
    _team(27, "SAS", "San Antonio Spurs", "San Antonio", "san antonio spurs|spurs|sas"),
    _team(28, "TOR", "Toronto Raptors", "Toronto", "toronto raptors|raptors|tor"),
    _team(29, "UTA", "Utah Jazz", "Salt Lake City", "utah jazz|jazz|uta"),
    _team(30, "WAS", "Washington Wizards", "Washington", "washington wizards|wizards|was|wsh"),
)
