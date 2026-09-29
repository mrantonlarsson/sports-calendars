#!/usr/bin/env python3
"""Bygger alla kalenderflöden till docs/.

En källa som ligger nere ska inte tömma de andra flödena: varje kalender byggs
för sig, och den som misslyckas behåller sin senast fungerande fil. Körningen
avslutas ändå med felkod så att det syns i GitHub Actions.
"""
from pathlib import Path
import sys

from calendars import frolunda, landslaget_fotboll, tre_kronor
from calendars.ics import calendar, write_if_changed

OUTPUT = Path(__file__).parent / "docs"
FEEDS = {
    "frolunda.ics": frolunda,
    "landslaget-fotboll.ics": landslaget_fotboll,
    "tre-kronor.ics": tre_kronor,
}


def main() -> int:
    OUTPUT.mkdir(exist_ok=True)
    failures = []
    for filename, source in FEEDS.items():
        try:
            name, matches = source.build()
        except Exception as error:                      # noqa: BLE001 – rapportera, fortsätt
            failures.append(filename)
            print(f"FEL  {filename}: {error} (behåller föregående version)", file=sys.stderr)
            continue
        changed = write_if_changed(OUTPUT / filename, calendar(name, matches))
        print(f"{'skrev' if changed else 'oförändrad':>11}  {filename}  {len(matches)} matcher")

    if failures:
        print(f"\n{len(failures)} av {len(FEEDS)} flöden misslyckades: {', '.join(failures)}",
              file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
