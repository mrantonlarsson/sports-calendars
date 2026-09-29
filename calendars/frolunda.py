"""Frölunda HC herr – SHL och CHL, inklusive slutspel när det lottats.

Säsong, serier och matchtyper hämtas från shl.se:s egen filterendpoint, så
flödet följer med till nästa säsong och plockar upp slutspelsmatcher av sig
självt när förbundet lägger in dem.
"""
from datetime import datetime, timedelta
import json
import urllib.parse
import urllib.request

from .ics import Match

NAME = "Frölunda HC"
TEAM = "FHC"
DURATION = timedelta(hours=2, minutes=30)
FILTER_URL = "https://www.shl.se/api/sports-v2/season-series-game-types-filter"
SCHEDULE_URL = "https://www.shl.se/api/sports-v2/game-schedule"
# Serier att följa, och vilken markör de får i kalendernamnet.
SERIES_MARKERS = {"SHL": "", "CHL": "🇪🇺 "}
# Förbundets "long"-namn är snyggast, men några få behöver hjälp.
NAME_FIX = {"Björklöven": "IF Björklöven"}


def _get(url: str, **params) -> dict:
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "sports-calendars"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _games(season: str, series: str, game_type: str) -> list[dict]:
    schedule = _get(SCHEDULE_URL, seasonUuid=season, seriesUuid=series, gameTypeUuid=game_type)
    return schedule.get("gameInfo", [])


def build() -> tuple[str, list[Match]]:
    current = _get(FILTER_URL)
    season = current["defaultSsgtFilter"]["season"]
    series_uuids = {s["code"]: s["uuid"] for s in current["series"]}

    matches = []
    for code, marker in SERIES_MARKERS.items():
        series = series_uuids[code]
        # Varje serie har sina egna matchtyper (grundserie, slutspel, kval).
        for game_type in _get(FILTER_URL, series=series, season=season)["gameType"]:
            for game in _games(season, series, game_type["uuid"]):
                home, away = game["homeTeamInfo"], game["awayTeamInfo"]
                if TEAM not in (home["code"], away["code"]):
                    continue
                at_home = home["code"] == TEAM
                opponent = (away if at_home else home)["names"]["long"]
                opponent = NAME_FIX.get(opponent, opponent).upper()
                label = game["seriesInfo"]["code"]
                if game_type["code"] != "regular":
                    label += " " + game_type["names"][0]["translation"].lower()
                matches.append(Match(
                    uid=f"{game['uuid']}@shl.se",
                    start=datetime.fromisoformat(game["rawStartDateTime"].replace("Z", "+00:00")),
                    duration=DURATION,
                    summary="🦚 " + ("🏟️ " if at_home else "") + marker + opponent,
                    location=game["venueInfo"]["name"],
                    description=f"{label}: {home['names']['long']} – {away['names']['long']}",
                ))

    if not matches:
        raise RuntimeError("Inga Frölundamatcher i schemat – har API:t ändrats?")
    return NAME, matches
