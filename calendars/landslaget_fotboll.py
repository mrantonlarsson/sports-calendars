"""Herrlandslaget i fotboll – matchlistan på svenskfotboll.se.

Sidan är serverrenderad och listar kommande matcher med exakt avsparkstid i
svensk tid, så nya turneringar (EM-kval, play-off) dyker upp av sig självt.
"""
from datetime import datetime, timedelta
import html
import re
import urllib.request

from .ics import Match

NAME = "Herrlandslaget fotboll"
TEAM = "Sverige"
DURATION = timedelta(hours=2)          # 90 min + paus + tillägg
URL = "https://www.svenskfotboll.se/landslag/herr/"
BLOCK = re.compile(r'<a[^>]*class="match-link__match".*?</a>', re.S)


def _field(block: str, name: str) -> str:
    found = re.search(r'class="match-link__%s"[^>]*>(.*?)</span>' % name, block, re.S)
    if not found:
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", found.group(1)))).strip()


def build() -> tuple[str, list[Match]]:
    request = urllib.request.Request(URL, headers={"User-Agent": "sports-calendars"})
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")

    matches = []
    for block in BLOCK.findall(page):
        start = datetime.fromisoformat(html.unescape(re.search(r'datetime="([^"]*)"', block).group(1)))
        home, _, away = (part.strip() for part in _field(block, "title").partition(" - "))
        if TEAM not in (home, away):
            continue
        at_home = home == TEAM
        venue = _field(block, "event")
        # Platsfältet inleds med avsparkstiden; den har vi redan.
        venue = venue.split(" ", 1)[1].strip() if re.match(r"^\d{1,2}:\d{2} ", venue) else venue
        competition = _field(block, "tag")
        matches.append(Match(
            uid=f"{re.search(r'fmid=(\d+)', block).group(1)}@svenskfotboll.se",
            start=start,
            duration=DURATION,
            summary="🇸🇪 " + ("🏟️ " if at_home else "") + (away if at_home else home).upper(),
            location=venue,
            description=f"{competition}: {home} – {away}",
        ))

    if not matches:
        raise RuntimeError("Inga landskamper hittades – har sidan bytt format?")
    return NAME, matches
