"""Delad ICS-byggare för kalenderflödena.

DTSTAMP och LAST-MODIFIED skrivs som en platshållare och fylls i först när
``write_if_changed`` konstaterat att innehållet faktiskt ändrats. Annars hade
varje körning gett en ny commit trots att inga matcher rörts.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

STAMP = "{{STAMP}}"
REFRESH = "PT12H"
ALARM_BEFORE = "PT1H"
_VOLATILE = re.compile(r"^(?:DTSTAMP|LAST-MODIFIED):.*$\r?\n?", re.M)


@dataclass(frozen=True)
class Match:
    """En match, färdig att skrivas som VEVENT."""

    uid: str
    start: datetime          # tidszonsmedveten
    duration: timedelta
    summary: str
    location: str
    description: str


def esc(value: str) -> str:
    """Escapar text enligt RFC 5545."""
    return (value.replace("\\", "\\\\").replace(";", "\\;")
                 .replace(",", "\\,").replace("\n", "\\n"))


def fold(line: str) -> str:
    """Bryter rader längre än 75 oktetter utan att klyva ett tecken."""
    parts, current, size = [], "", 0
    for char in line:
        width = len(char.encode("utf-8"))
        if size + width > 74:
            parts.append(current)
            current, size = " ", 1
        current += char
        size += width
    parts.append(current)
    return "\r\n".join(parts)


def _utc(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _event(match: Match) -> list[str]:
    return [
        "BEGIN:VEVENT",
        f"UID:{match.uid}",
        f"DTSTAMP:{STAMP}",
        f"LAST-MODIFIED:{STAMP}",
        f"DTSTART:{_utc(match.start)}",
        f"DTEND:{_utc(match.start + match.duration)}",
        f"SUMMARY:{esc(match.summary)}",
        f"LOCATION:{esc(match.location)}",
        f"DESCRIPTION:{esc(match.description)}",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Match om 1 timme",
        f"TRIGGER:-{ALARM_BEFORE}",
        "END:VALARM",
        "END:VEVENT",
    ]


def calendar(name: str, matches: list[Match]) -> str:
    """Bygger en komplett VCALENDAR att prenumerera på."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//sports-calendars//SE",
        "METHOD:PUBLISH",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{esc(name)}",
        "X-WR-TIMEZONE:Europe/Stockholm",
        f"X-PUBLISHED-TTL:{REFRESH}",
        f"REFRESH-INTERVAL;VALUE=DURATION:{REFRESH}",
    ]
    for match in sorted(matches, key=lambda m: (m.start, m.uid)):
        lines += _event(match)
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def write_if_changed(path: Path, body: str) -> bool:
    """Skriver filen bara när något annat än tidsstämplarna ändrats.

    Läser och skriver som bytes; textläget skulle översätta radbrytningarna och
    få varje jämförelse att se ut som en ändring.
    """
    if path.exists():
        current = path.read_bytes().decode("utf-8")
        if _VOLATILE.sub("", current) == _VOLATILE.sub("", body):
            return False
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path.write_bytes(body.replace(STAMP, stamp).encode("utf-8"))
    return True
