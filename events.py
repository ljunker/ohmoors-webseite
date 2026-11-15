from icalevents.icalevents import events
import datetime
import json
import os
import sys
from urllib.parse import urlsplit

URL_ENV = "OHMOORS_CALENDAR_URL"


def build_event(e):
    if getattr(e, "all_day", False):
        # Ganztägig: Kalenderdatum ohne UTC-Umrechnung. DTEND ist exklusiv.
        start_date = e.start.date()
        end_date = e.end.date() - datetime.timedelta(days=1)
        if end_date < start_date:
            end_date = start_date
        return {
            "date": start_date.strftime("%Y-%m-%d"),
            "time": "00:00",
            "end_date": end_date.strftime("%Y-%m-%d"),
            "end_time": "00:00",
            "all_day": True,
            "details": e.summary,
            "location": e.location,
            "caller": e.description,
        }

    start_utc = e.start.astimezone(datetime.timezone.utc)
    end_utc = e.end.astimezone(datetime.timezone.utc)
    return {
        "date": start_utc.strftime("%Y-%m-%d"),
        "time": start_utc.strftime("%H:%M"),
        "end_date": end_utc.strftime("%Y-%m-%d"),
        "end_time": end_utc.strftime("%H:%M"),
        "all_day": False,
        "details": e.summary,
        "location": e.location,
        "caller": e.description,
    }


def main():
    url = os.environ.get(URL_ENV, "").strip()
    if not url:
        print(
            f"ERROR: Umgebungsvariable {URL_ENV} ist nicht gesetzt (Kalender-Feed-URL).",
            file=sys.stderr,
        )
        return 1

    dt = datetime.datetime.today() - datetime.timedelta(days=1)
    in_eight_weeks = dt + datetime.timedelta(weeks=8)

    try:
        es = events(url, start=dt, end=in_eight_weeks, sort=True, fix_apple=True)
        events_json = [build_event(e) for e in es]
    except Exception as exc:
        # Meldung ohne URL ausgeben, da sie ein Freigabe-Token enthält.
        msg = str(exc)
        parsed = urlsplit(url)
        # Token steckt im Pfad: URL, Pfad und Host aus der Meldung entfernen.
        secrets = [url, url.split("://", 1)[-1], parsed.path, parsed.query]
        for part in sorted((x for x in secrets if len(x) > 1), key=len, reverse=True):
            msg = msg.replace(part, "<redacted>")
        print(
            f"ERROR: Kalender konnte nicht abgerufen werden: {type(exc).__name__}: {msg}",
            file=sys.stderr,
        )
        return 2

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(events_json, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
