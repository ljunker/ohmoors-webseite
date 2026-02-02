import sys
from pathlib import Path


INCLUDE_TOKEN = "{{ include: nav.html }}"


def main(argv):
    if len(argv) != 3:
        raise SystemExit("Usage: build_pages.py static/ _site/")
    static_dir = Path(argv[1])
    site_dir = Path(argv[2])
    nav_path = static_dir / "nav.html"
    if not nav_path.exists():
        raise SystemExit("Missing static/nav.html")
    nav_html = nav_path.read_text(encoding="utf-8")

    for page in static_dir.glob("*.html"):
        if page.name == "nav.html":
            continue
        html = page.read_text(encoding="utf-8")
        if INCLUDE_TOKEN in html:
            html = html.replace(INCLUDE_TOKEN, nav_html)
        (site_dir / page.name).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
