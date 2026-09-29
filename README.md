# sports-calendars

Prenumerationsbara kalenderflöden med egna matchnamn, byggda från lagens
officiella scheman och uppdaterade dagligen av GitHub Actions.

| Flöde | Innehåll | Prenumerera |
| --- | --- | --- |
| Frölunda HC | SHL och CHL, slutspel när det lottats | `webcal://mrantonlarsson.github.io/sports-calendars/frolunda.ics` |
| Herrlandslaget fotboll | Kommande landskamper | `webcal://mrantonlarsson.github.io/sports-calendars/landslaget-fotboll.ics` |
| Tre Kronor herr | Euro Hockey Tour och VM | `webcal://mrantonlarsson.github.io/sports-calendars/tre-kronor.ics` |

Byt `webcal://` mot `https://` där klienten vill ha det.

## Matchnamnen

`🦚 🏟️ 🇪🇺 MOTSTÅNDARE` – lagmarkör först, sedan 🏟️ om matchen spelas hemma och
en markör för turneringen: 🇪🇺 för CHL, 🏆 för VM. Landskamperna använder 🇸🇪
respektive 🇸🇪🏒 som lagmarkör.

Varje event har arena som plats, påminnelse en timme innan och en sluttid
uppskattad från matchlängden – ingen av källorna anger när en match tar slut.

## Hur ofta det uppdateras

Actions bygger om flödena varje dygn, men det är kalenderklienten som avgör hur
ofta den hämtar: Apple Calendar låter dig välja ned till fem minuter, Google
hämtar externa flöden ungefär en gång per dygn och går inte att styra. Räkna
därför med upp till ett dygns fördröjning på en ändrad matchtid.

Flödena har stabila UID:n, så en ändrad match uppdateras på plats i stället för
att dyka upp som en dubblett.

## Källor

- **Frölunda** – shl.se:s schema-API. Säsong, serier och matchtyper läses från
  sajtens egen filterendpoint, så flödet följer med till nästa säsong och
  plockar upp slutspel automatiskt.
- **Fotbollslandslaget** – matchlistan på svenskfotboll.se. Nya turneringar
  kommer in av sig själva.
- **Tre Kronor** – Svenska Ishockeyförbundets matchtabell. Euro Hockey
  Tour-turneringarna fylls på när de lottas.

## Det som kräver handpåläggning

VM-gruppspelet finns inte i förbundets matchtabell och ligger som en verifierad
lista i [`calendars/tre_kronor.py`](calendars/tre_kronor.py). Den behöver bytas
ut när nästa VM-schema släpps.

Schemalagda workflows stängs av efter 60 dagar utan aktivitet i repot. GitHub
mejlar innan det händer – en commit räcker för att starta om det.

## Köra lokalt

```bash
python3 build.py
```

Skriver om `docs/*.ics` bara när något faktiskt ändrats, så tidsstämplar ensamma
ger inga commits. Ett flöde vars källa ligger nere behåller sin senaste
fungerande version, och körningen avslutas med felkod så att det syns.
