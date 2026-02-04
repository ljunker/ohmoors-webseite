import html
import json
import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


LOCAL_TZ = ZoneInfo("Europe/Berlin")
ACTIVE_CLASS = "active"
MONTHS_DE = [
    "Jan.",
    "Feb.",
    "Mrz.",
    "Apr.",
    "Mai",
    "Jun.",
    "Jul.",
    "Aug.",
    "Sep.",
    "Okt.",
    "Nov.",
    "Dez.",
]


def parse_dt(date_str, time_str):
    # events.json times are UTC; map to local CET/CEST for display and sorting
    utc_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(
        tzinfo=timezone.utc
    )
    return utc_dt.astimezone(LOCAL_TZ)


def format_date_de(dt):
    return f"{dt.day}. {MONTHS_DE[dt.month - 1]} {dt.year}"


def mark_active(nav_html, page_name):
    pattern = re.compile(rf"<a([^>]*?)href=[\"']{re.escape(page_name)}[\"']([^>]*)>")

    def repl(match):
        attrs_before = match.group(1)
        attrs_after = match.group(2)
        full_attrs = f"{attrs_before}{attrs_after}"
        if "data-skip-active" in full_attrs:
            return match.group(0)
        if "class=" in full_attrs:
            return re.sub(
                r"class=[\"']([^\"']*)[\"']",
                lambda m: f'class="{m.group(1)} {ACTIVE_CLASS}"',
                match.group(0),
                count=1,
            )
        return f"<a{attrs_before}href=\"{page_name}\" class=\"{ACTIVE_CLASS}\"{attrs_after}>"

    return pattern.sub(repl, nav_html)


def load_events(path):
    with open(path, "r", encoding="utf-8") as f:
        events = json.load(f)
    events.sort(key=lambda e: parse_dt(e["date"], e["time"]))
    return events


def render(events, nav_html):
    title = "Ohmoor Squeezers e.V. - Clubabende"
    rows = []
    for e in events:
        start_local = parse_dt(e.get("date", ""), e.get("time", ""))
        end_local = parse_dt(e.get("end_date", ""), e.get("end_time", ""))
        date = html.escape(format_date_de(start_local))
        time = html.escape(start_local.strftime("%H:%M"))
        end_time = html.escape(end_local.strftime("%H:%M"))
        raw_details = e.get("details", "")
        is_cancelled = "abgesagt" in raw_details.lower()
        if is_cancelled:
            cleaned = raw_details.replace("abgesagt", "").replace("Abgesagt", "")
            cleaned = " ".join(cleaned.replace("-", " ").split()).strip()
            if not cleaned:
                cleaned = "Clubabend"
            details = f"<span class=\"badge cancelled\">Abgesagt</span> {html.escape(cleaned)}"
        else:
            details = html.escape(raw_details)
        raw_location = e.get("location", "")
        if raw_location:
            location_parts = [html.escape(p.strip()) for p in raw_location.split(",")]
            location = "<br />".join([p for p in location_parts if p])
        else:
            location = ""
        caller = html.escape(e.get("caller", ""))
        date_line = f"{date} | {time}-{end_time}"
        row_class = " class=\"is-cancelled\"" if is_cancelled else ""
        rows.append(
            f"        <tr{row_class}>\n"
            f"          <td data-label=\"Datum & Zeit\">{html.escape(date_line)}</td>\n"
            f"          <td data-label=\"Details\">{details}</td>\n"
            f"          <td data-label=\"Ort\">{location}</td>\n"
            f"          <td data-label=\"Caller\">{caller}</td>\n"
            "        </tr>"
        )

    if rows:
        body = (
            "      <table>\n"
            "        <thead>\n"
            "          <tr>\n"
            "            <th>Datum & Zeit</th>\n"
            "            <th>Details</th>\n"
            "            <th>Ort</th>\n"
            "            <th>Caller</th>\n"
            "          </tr>\n"
            "        </thead>\n"
            "        <tbody>\n"
            + "\n".join(rows)
            + "\n        </tbody>\n"
            "      </table>\n"
        )
    else:
        body = "      <p>Keine Termine vorhanden.</p>\n"

    return (
        "<!doctype html>\n"
        "<html lang=\"de\">\n"
        "  <head>\n"
        "    <meta charset=\"utf-8\" />\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "    <link rel=\"stylesheet\" href=\"style.css\" />\n"
        f"    <title>{html.escape(title)}</title>\n"
        "  </head>\n"
        "  <body>\n"
        f"{mark_active(nav_html, 'schedule.html')}"
        "    <main class=\"container page\">\n"
        f"      <h1>{html.escape(title)}</h1>\n"
        "      <p class=\"muted\">Alle Termine sind in lokaler Zeit (CET/CEST).</p>\n"
        f"{body}"
        "    </main>\n"
        "  </body>\n"
        "</html>\n"
    )


def main(argv):
    if len(argv) != 4:
        raise SystemExit("Usage: generate_schedule.py events.json static/nav.html _site/schedule.html")
    events_path, nav_path, output_path = argv[1], argv[2], argv[3]
    with open(nav_path, "r", encoding="utf-8") as f:
        nav_html = f.read()
    events = load_events(events_path)
    html_out = render(events, nav_html)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_out)


if __name__ == "__main__":
    main(sys.argv)
