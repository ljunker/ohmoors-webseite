#!/usr/bin/env python3
import argparse
import curses
import json
import os
import shutil
import sys
from datetime import datetime


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_NEWS_FILE = os.path.join(BASE_DIR, "static", "news.json")


FIELDS = [
    ("date", "Datum (z.B. 16. Feb. 2026)"),
    ("title", "Titel"),
    ("text", "Text"),
    ("flyer_url", "Flyer URL (optional)"),
    ("flyer_label", "Flyer Label (optional)"),
    ("flyer_text", "Flyer Text (ohne URL)"),
]


def load_news(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("news.json must be a list")
    return data


def normalize_items(items):
    allowed = {k for k, _ in FIELDS}
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        clean = {}
        for key in allowed:
            value = item.get(key, "")
            if value is None:
                continue
            value = str(value).strip()
            if value:
                clean[key] = value
        normalized.append(clean)
    return normalized


def write_news(path, items):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = f"{path}.bak-{ts}"
        shutil.copy2(path, backup)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_path, path)


def center_text(stdscr, y, text, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    stdscr.addstr(y, x, text[: w - 1], attr)


def prompt_line(stdscr, y, label, value):
    h, w = stdscr.getmaxyx()
    stdscr.addstr(y, 2, label[: w - 4])
    stdscr.addstr(y, 2 + len(label) + 1, "(Enter=behalten, '-'=leeren)"[: w - 6])
    stdscr.addstr(y + 1, 2, "> ")
    stdscr.addstr(y + 1, 4, value[: w - 6])
    stdscr.clrtoeol()
    curses.echo()
    curses.curs_set(1)
    stdscr.move(y + 1, 4 + min(len(value), w - 6))
    new_val = stdscr.getstr(y + 1, 4, w - 6).decode("utf-8")
    curses.noecho()
    curses.curs_set(0)
    return new_val.strip()


def edit_item(stdscr, item):
    stdscr.clear()
    center_text(stdscr, 1, "News bearbeiten", curses.A_BOLD)
    y = 3
    for key, label in FIELDS:
        current = item.get(key, "")
        stdscr.addstr(y - 1, 2, "-" * 40)
        value = prompt_line(stdscr, y, f"{label}:", current)
        if value == "":
            pass
        elif value == "-":
            if key in item:
                del item[key]
        else:
            item[key] = value
        y += 3
    stdscr.addstr(y, 2, "Speichern mit Enter...")
    stdscr.getch()
    return item


def draw_list(stdscr, items, index, status):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    center_text(stdscr, 1, "News TUI", curses.A_BOLD)
    stdscr.addstr(3, 2, "a=Neu  e=Bearb  d=Loesch  u=Hoch  n=Runter  s=Speichern  r=Reload  q=Quit")
    stdscr.addstr(4, 2, "-" * (w - 4))
    if not items:
        stdscr.addstr(6, 2, "Keine News vorhanden.")
    else:
        for i, item in enumerate(items):
            line = f"{i+1}. {item.get('date','')} | {item.get('title','')}"
            if i == index:
                stdscr.addstr(6 + i, 2, line[: w - 4], curses.A_REVERSE)
            else:
                stdscr.addstr(6 + i, 2, line[: w - 4])
            if 6 + i >= h - 3:
                break
    if status:
        stdscr.addstr(h - 2, 2, status[: w - 4], curses.A_BOLD)
    stdscr.refresh()


def run_tui(stdscr, news_path):
    curses.curs_set(0)
    items = normalize_items(load_news(news_path))
    index = 0
    status = ""

    while True:
        if index < 0:
            index = 0
        if items and index >= len(items):
            index = len(items) - 1

        draw_list(stdscr, items, index, status)
        status = ""
        ch = stdscr.getch()

        if ch in (ord("q"), 27):
            break
        elif ch in (curses.KEY_UP, ord("k")):
            index -= 1
        elif ch in (curses.KEY_DOWN, ord("j")):
            index += 1
        elif ch == ord("a"):
            new_item = {}
            items.append(edit_item(stdscr, new_item))
            index = len(items) - 1
        elif ch == ord("e"):
            if items:
                items[index] = edit_item(stdscr, items[index])
        elif ch == ord("d"):
            if items:
                del items[index]
                index = max(0, index - 1)
        elif ch == ord("u"):
            if items and index > 0:
                items[index - 1], items[index] = items[index], items[index - 1]
                index -= 1
        elif ch == ord("n"):
            if items and index < len(items) - 1:
                items[index + 1], items[index] = items[index], items[index + 1]
                index += 1
        elif ch == ord("s"):
            write_news(news_path, normalize_items(items))
            status = f"Gespeichert: {news_path}"
        elif ch == ord("r"):
            items = normalize_items(load_news(news_path))
            index = 0
            status = "Neu geladen"


def main(argv):
    parser = argparse.ArgumentParser(description="TUI CRUD for static/news.json")
    parser.add_argument("--file", default=DEFAULT_NEWS_FILE, help="Path to news.json")
    args = parser.parse_args(argv)
    news_path = os.path.abspath(args.file)

    try:
        curses.wrapper(run_tui, news_path)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
