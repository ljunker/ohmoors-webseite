#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_NEWS_FILE = os.path.join(BASE_DIR, "static", "news.json")


HTML_PAGE = """<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <title>News Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root { color-scheme: light; --bg: #f6f7fb; --surface: #fff; --text: #111827; --muted: #6b7280; --border: #e5e7eb; --accent: #419545; }
      * { box-sizing: border-box; }
      body { margin: 0; font-family: "Manrope","Avenir Next","Segoe UI","Helvetica Neue",Arial,sans-serif; color: var(--text); background: var(--bg); }
      .container { width: min(1100px, 92vw); margin: 32px auto 64px; }
      header { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
      h1 { margin: 0; font-size: 28px; }
      .muted { color: var(--muted); }
      .controls { display: flex; gap: 8px; flex-wrap: wrap; }
      button { border: 1px solid var(--border); background: var(--surface); padding: 8px 12px; border-radius: 10px; cursor: pointer; font-weight: 600; }
      button.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
      button.danger { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
      .card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 16px; margin-top: 16px; }
      .row { display: grid; grid-template-columns: 140px 1fr; gap: 12px; align-items: center; }
      .row + .row { margin-top: 10px; }
      input, textarea { width: 100%; border: 1px solid var(--border); border-radius: 10px; padding: 8px 10px; font: inherit; }
      textarea { min-height: 70px; resize: vertical; }
      .item-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
      .item-actions { display: flex; gap: 6px; flex-wrap: wrap; }
      .list { display: grid; gap: 16px; margin-top: 16px; }
      .status { margin-top: 10px; font-weight: 600; }
      @media (max-width: 720px) {
        .row { grid-template-columns: 1fr; }
        header { flex-direction: column; align-items: flex-start; }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <header>
        <div>
          <h1>News Admin</h1>
          <p class="muted">Bearbeite Einträge in news.json</p>
        </div>
        <div class="controls">
          <button id="add-btn">Neu</button>
          <button id="save-btn" class="primary">Speichern</button>
        </div>
      </header>
      <div id="status" class="status muted"></div>
      <div id="list" class="list"></div>
    </div>

    <template id="item-template">
      <div class="card">
        <div class="item-header">
          <strong>News</strong>
          <div class="item-actions">
            <button data-action="up">Hoch</button>
            <button data-action="down">Runter</button>
            <button data-action="delete" class="danger">Löschen</button>
          </div>
        </div>
        <div class="row">
          <label>Datum</label>
          <input name="date" placeholder="z.B. 16. Feb. 2026" />
        </div>
        <div class="row">
          <label>Titel</label>
          <input name="title" placeholder="Titel" />
        </div>
        <div class="row">
          <label>Text</label>
          <textarea name="text" placeholder="Kurztext"></textarea>
        </div>
        <div class="row">
          <label>Flyer URL</label>
          <input name="flyer_url" placeholder="2026-Rosenmontag.pdf" />
        </div>
        <div class="row">
          <label>Flyer Label</label>
          <input name="flyer_label" placeholder="Flyer (PDF)" />
        </div>
        <div class="row">
          <label>Flyer Text (ohne URL)</label>
          <input name="flyer_text" placeholder="Flyer folgt" />
        </div>
      </div>
    </template>

    <script>
      (function () {
        var listEl = document.getElementById("list");
        var statusEl = document.getElementById("status");
        var addBtn = document.getElementById("add-btn");
        var saveBtn = document.getElementById("save-btn");
        var template = document.getElementById("item-template");

        function setStatus(text, isError) {
          statusEl.textContent = text || "";
          statusEl.className = "status " + (isError ? "" : "muted");
          if (isError) statusEl.style.color = "#b91c1c";
          else statusEl.style.color = "";
        }

        function createItem(item) {
          var node = template.content.firstElementChild.cloneNode(true);
          node.querySelector("[name='date']").value = item.date || "";
          node.querySelector("[name='title']").value = item.title || "";
          node.querySelector("[name='text']").value = item.text || "";
          node.querySelector("[name='flyer_url']").value = item.flyer_url || "";
          node.querySelector("[name='flyer_label']").value = item.flyer_label || "";
          node.querySelector("[name='flyer_text']").value = item.flyer_text || "";

          node.addEventListener("click", function (e) {
            var action = e.target && e.target.getAttribute("data-action");
            if (!action) return;
            e.preventDefault();
            var card = node;
            if (action === "delete") {
              card.remove();
            } else if (action === "up") {
              if (card.previousElementSibling) {
                listEl.insertBefore(card, card.previousElementSibling);
              }
            } else if (action === "down") {
              if (card.nextElementSibling) {
                listEl.insertBefore(card.nextElementSibling, card);
              }
            }
          });

          return node;
        }

        function readItems() {
          return Array.prototype.map.call(listEl.children, function (card) {
            function v(name) {
              return card.querySelector("[name='" + name + "']").value.trim();
            }
            var item = {
              date: v("date"),
              title: v("title"),
              text: v("text"),
            };
            var flyerUrl = v("flyer_url");
            var flyerLabel = v("flyer_label");
            var flyerText = v("flyer_text");
            if (flyerUrl) item.flyer_url = flyerUrl;
            if (flyerLabel) item.flyer_label = flyerLabel;
            if (flyerText) item.flyer_text = flyerText;
            return item;
          });
        }

        function render(items) {
          listEl.innerHTML = "";
          items.forEach(function (item) {
            listEl.appendChild(createItem(item));
          });
        }

        function load() {
          setStatus("Lade ...");
          fetch("api/news", { cache: "no-store" })
            .then(function (res) {
              if (!res.ok) throw new Error("HTTP " + res.status);
              return res.json();
            })
            .then(function (data) {
              if (!Array.isArray(data)) throw new Error("news.json hat kein Array-Format");
              render(data);
              setStatus("");
            })
            .catch(function (err) {
              setStatus("Fehler beim Laden: " + err.message, true);
            });
        }

        function save() {
          var payload = readItems();
          setStatus("Speichere ...");
          fetch("api/news", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload, null, 2),
          })
            .then(function (res) {
              if (!res.ok) throw new Error("HTTP " + res.status);
              return res.json();
            })
            .then(function (data) {
              setStatus(data.message || "Gespeichert");
            })
            .catch(function (err) {
              setStatus("Fehler beim Speichern: " + err.message, true);
            });
        }

        addBtn.addEventListener("click", function () {
          listEl.appendChild(createItem({}));
        });
        saveBtn.addEventListener("click", save);

        load();
      })();
    </script>
  </body>
</html>
"""


def load_news(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("news.json must be a list")
    return data


def normalize_items(items):
    allowed = {"date", "title", "text", "flyer_url", "flyer_label", "flyer_text"}
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


class NewsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
            return

        if self.path == "/api/news":
            try:
                data = load_news(self.server.news_file)
            except Exception as exc:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                payload = {"error": str(exc)}
                self.wfile.write(json.dumps(payload).encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/api/news":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
            if not isinstance(data, list):
                raise ValueError("news.json must be a list")
            items = normalize_items(data)
            write_news(self.server.news_file, items)
        except Exception as exc:
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            payload = {"error": str(exc)}
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "Gespeichert"}).encode("utf-8"))

    def log_message(self, fmt, *args):
        return


def main(argv):
    parser = argparse.ArgumentParser(description="CRUD UI for static/news.json")
    parser.add_argument("--file", default=DEFAULT_NEWS_FILE, help="Path to news.json")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    args = parser.parse_args(argv)

    server = HTTPServer((args.host, args.port), NewsHandler)
    server.news_file = os.path.abspath(args.file)
    print(f"News admin running on http://{args.host}:{args.port}")
    print(f"Editing: {server.news_file}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main(sys.argv[1:])
