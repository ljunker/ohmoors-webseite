import re
import sys
from pathlib import Path


INCLUDE_TOKEN = "{{ include: nav.html }}"
FOOTER_TOKEN = "{{ include: footer.html }}"
ACTIVE_CLASS = "active"


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


def main(argv):
    if len(argv) != 3:
        raise SystemExit("Usage: build_pages.py static/ _site/")
    static_dir = Path(argv[1])
    site_dir = Path(argv[2])
    nav_path = static_dir / "nav.html"
    footer_path = static_dir / "footer.html"
    if not nav_path.exists():
        raise SystemExit("Missing static/nav.html")
    nav_html = nav_path.read_text(encoding="utf-8")
    footer_html = footer_path.read_text(encoding="utf-8") if footer_path.exists() else ""

    for page in static_dir.glob("*.html"):
        if page.name in {"nav.html", "footer.html"}:
            continue
        html = page.read_text(encoding="utf-8")
        if INCLUDE_TOKEN in html:
            html = html.replace(INCLUDE_TOKEN, mark_active(nav_html, page.name))
        if FOOTER_TOKEN in html:
            if not footer_html:
                raise SystemExit("Missing static/footer.html")
            html = html.replace(FOOTER_TOKEN, footer_html)
        (site_dir / page.name).write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
