"""Tre Kronor herr – landskamper från Svenska Ishockeyförbundet, plus VM.

Förbundets matchtabell fylls på turnering för turnering, så nya Euro Hockey
Tour-matcher kommer in automatiskt. VM-gruppspelet ligger inte i den tabellen
och underhålls därför som en verifierad lista här nere – den behöver bytas ut
inför varje mästerskap.
"""
from datetime import date, datetime, timedelta
import hashlib
import html
import re
import urllib.request

from .ics import Match
from zoneinfo import ZoneInfo

NAME = "Tre Kronor herr"
TEAM = "Sverige"
DURATION = timedelta(hours=2, minutes=30)
URL = "https://www.swehockey.se/landslag/vaara-landslag/tre-kronor-herr/"
SE = ZoneInfo("Europe/Stockholm")
MONTHS = "jan feb mar apr maj jun jul aug sep okt nov dec".split()
SEASON_BREAK = 7                       # säsongen räknas från juli
# Orter där landslaget spelar hemma. Sverige står som "hemmalag" även i t.ex.
# Prag, så lagkolumnen duger inte för att avgöra 🏟️.
SWEDISH_CITIES = {"stockholm", "solna", "göteborg", "malmö", "karlstad", "leksand",
                  "luleå", "växjö", "södertälje", "jönköping", "linköping", "örebro",
                  "gävle", "umeå", "ängelholm", "helsingborg", "falun", "nyköping"}

# VM 2027 i Tyskland, samtliga gruppspelsmatcher i SAP Arena, Mannheim.
# Källa: IIHF:s spelschema 2026-09-08 (vmhockey.se, bekräftat av hockeynews.se).
# Tiderna är svenska. Byt ut listan när nästa VM-schema släpps.
CHAMPIONSHIP = "VM"
CHAMPIONSHIP_VENUE = "SAP Arena, Mannheim"
CHAMPIONSHIP_GAMES = [
    ("2027-05-14", "16:20", "Ukraina", "Sverige"),
    ("2027-05-16", "12:20", "Sverige", "Lettland"),
    ("2027-05-17", "16:20", "Slovenien", "Sverige"),
    ("2027-05-20", "16:20", "Sverige", "Österrike"),
    ("2027-05-21", "20:20", "Sverige", "Schweiz"),
    ("2027-05-23", "20:20", "Finland", "Sverige"),
    ("2027-05-25", "20:20", "Tyskland", "Sverige"),
]


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _season_start(today: date) -> int:
    """Året säsongen inleddes; tabellen anger datum utan årtal."""
    return today.year if today.month >= SEASON_BREAK else today.year - 1


def _match(start: datetime, venue: str, home: str, away: str, competition: str) -> Match:
    at_home = venue.split(",")[-1].strip().lower() in SWEDISH_CITIES
    marker = ("🏟️ " if at_home else "") + ("🏆 " if competition == CHAMPIONSHIP else "")
    key = f"{start:%Y%m%d}{home}{away}".encode("utf-8")
    return Match(
        uid=f"{hashlib.md5(key).hexdigest()[:16]}@swehockey.se",
        start=start,
        duration=DURATION,
        summary="🇸🇪🏒 " + marker + (away if home == TEAM else home).upper(),
        location=venue,
        description=f"{competition}: {home} – {away}",
    )


def _international_games(season_start: int) -> list[Match]:
    """Landskamperna ur förbundets matchtabell."""
    request = urllib.request.Request(URL, headers={"User-Agent": "sports-calendars"})
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")
    table = next((t for t in re.findall(r"<table.*?</table>", page, re.S) if "Hemmalag" in t), None)
    if table is None:
        raise RuntimeError("Hittade ingen matchtabell – har sidan bytt format?")

    matches = []
    for row in re.findall(r"<tr.*?</tr>", table, re.S):
        cells = [_text(cell) for cell in re.findall(r"<td.*?</td>", row, re.S)]
        if len(cells) < 5 or not re.match(r"^\d{1,2} [a-zå-ö]{3}$", cells[0]):
            continue
        day, month_name = cells[0].split()
        month = MONTHS.index(month_name) + 1
        hour, minute = re.split(r"[.:]", cells[1])
        year = season_start if month >= SEASON_BREAK else season_start + 1
        start = datetime(year, month, int(day), int(hour), int(minute), tzinfo=SE)
        matches.append(_match(start, cells[2], cells[3], cells[4], "Euro Hockey Tour"))

    if not matches:
        raise RuntimeError("Matchtabellen gav inga rader – har sidan bytt format?")
    return matches


def build() -> tuple[str, list[Match]]:
    matches = _international_games(_season_start(date.today()))
    matches += [
        _match(datetime.fromisoformat(f"{day} {time}").replace(tzinfo=SE),
               CHAMPIONSHIP_VENUE, home, away, CHAMPIONSHIP)
        for day, time, home, away in CHAMPIONSHIP_GAMES
    ]
    return NAME, matches
