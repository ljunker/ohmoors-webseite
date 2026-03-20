#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_NEWS_FILE = os.path.join(BASE_DIR, "static", "news.json")
DEFAULT_DEPLOY_DIR = "/var/www/ohmoors.de/html"


HTML_PAGE = r"""<!doctype html>
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
      textarea { min-height: 110px; resize: vertical; }
      .item-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
      .item-actions { display: flex; gap: 6px; flex-wrap: wrap; }
      .list { display: grid; gap: 16px; margin-top: 16px; }
      .status { margin-top: 10px; font-weight: 600; }
      .field-note { margin-top: 6px; font-size: 13px; color: var(--muted); }
      .preview-block { margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); }
      .preview-label { margin: 0 0 10px; font-size: 13px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); }
      .preview-card { background: #fbfcfd; border: 1px solid var(--border); border-radius: 16px; padding: 18px 20px; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06); }
      .preview-meta-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
      .preview-meta { font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }
      .preview-state { display: inline-flex; align-items: center; padding: 4px 9px; border-radius: 999px; border: 1px solid #f5c2c7; background: #fff1f2; color: #9f1239; font-size: 12px; font-weight: 700; }
      .preview-card h2 { margin: 8px 0 8px; font-size: 20px; }
      .preview-body > :first-child { margin-top: 0; }
      .preview-body > :last-child { margin-bottom: 0; }
      .preview-body ul, .preview-body ol { margin: 10px 0; padding-left: 22px; }
      .preview-body li + li { margin-top: 6px; }
      .preview-body code { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace; font-size: 0.95em; background: #eef3ea; border-radius: 6px; padding: 0.12em 0.4em; }
      .preview-body a { color: var(--accent); text-decoration: underline; text-decoration-thickness: 1.5px; text-underline-offset: 2px; font-weight: 600; }
      .preview-actions { margin-top: 14px; }
      .button-preview { display: inline-flex; align-items: center; justify-content: center; padding: 12px 22px; border-radius: 999px; background: var(--accent); color: #fff; font-weight: 600; }
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
          <button id="git-btn">Git Commit & Push</button>
          <button id="deploy-btn">Deploy news.json</button>
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
          <div>
            <textarea name="text" placeholder="Kurztext in Markdown"></textarea>
            <div class="field-note">Markdown: Absätze, Listen, Links, <code>**fett**</code>, <code>*kursiv*</code>, <code>`code`</code></div>
          </div>
        </div>
        <div class="row">
          <label>Veröffentlicht ab</label>
          <div>
            <input name="published_from" type="date" />
            <div class="field-note">Leer = sofort sichtbar. Die Auswahl nutzt den Kalender des Browsers und wird als Datum gespeichert.</div>
          </div>
        </div>
        <div class="row">
          <label>Veröffentlicht bis</label>
          <div>
            <input name="published_until" type="date" />
            <div class="field-note">Leer = unbegrenzt sichtbar. Mit beiden Feldern entsteht ein Veröffentlichungszeitraum.</div>
          </div>
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
        <div class="preview-block">
          <p class="preview-label">Vorschau</p>
          <article class="preview-card">
            <div class="preview-meta-row">
              <div class="preview-meta" data-preview="date"></div>
              <span class="preview-state" data-preview="state" hidden>Entwurf</span>
            </div>
            <h2 data-preview="title"></h2>
            <div class="preview-body" data-preview="text"></div>
            <div class="preview-actions" data-preview="actions"></div>
          </article>
        </div>
      </div>
    </template>

    <script>
      (function () {
        var listEl = document.getElementById("list");
        var statusEl = document.getElementById("status");
        var addBtn = document.getElementById("add-btn");
        var saveBtn = document.getElementById("save-btn");
        var gitBtn = document.getElementById("git-btn");
        var deployBtn = document.getElementById("deploy-btn");
        var template = document.getElementById("item-template");

        function parseJsonResponse(res) {
          return res.text().then(function (text) {
            var data = {};

            if (text) {
              try {
                data = JSON.parse(text);
              } catch (err) {
                throw new Error("Ungültige Server-Antwort");
              }
            }

            if (!res.ok) {
              throw new Error(data.error || ("HTTP " + res.status));
            }

            return data;
          });
        }

        function pad2(value) {
          return String(value).padStart(2, "0");
        }

        function isLegacyDraftValue(value) {
          if (value === false) {
            return true;
          }

          if (typeof value === "string") {
            return /^(false|0|no|nein|off)$/i.test(value.trim());
          }

          return false;
        }

        function parsePublicationDateKey(value) {
          var text = String(value || "").trim();
          var match;

          if (!text) {
            return "";
          }

          match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
          if (match) {
            return match[1] + "-" + match[2] + "-" + match[3];
          }

          match = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec(text);
          if (match) {
            return match[3] + "-" + pad2(match[2]) + "-" + pad2(match[1]);
          }

          return "";
        }

        function toDateInputValue(value) {
          return parsePublicationDateKey(value);
        }

        function getBerlinTodayKey() {
          var parts = new Intl.DateTimeFormat("en-CA", {
            timeZone: "Europe/Berlin",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
          }).formatToParts(new Date());
          var values = {};

          parts.forEach(function (part) {
            if (part.type !== "literal") {
              values[part.type] = part.value;
            }
          });

          return values.year + "-" + values.month + "-" + values.day;
        }

        function getPublicationState(fromValue, untilValue, legacyDraft) {
          var hasWindow = String(fromValue || "").trim() || String(untilValue || "").trim();
          var from = parsePublicationDateKey(fromValue);
          var until = parsePublicationDateKey(untilValue);
          var today = getBerlinTodayKey();

          if ((String(fromValue || "").trim() && !from) || (String(untilValue || "").trim() && !until)) {
            return "invalid";
          }

          if (!hasWindow && legacyDraft) {
            return "draft";
          }

          if (from && today < from) {
            return "scheduled";
          }

          if (until && today > until) {
            return "expired";
          }

          return "live";
        }

        function setStatus(text, isError) {
          statusEl.textContent = text || "";
          statusEl.className = "status " + (isError ? "" : "muted");
          if (isError) statusEl.style.color = "#b91c1c";
          else statusEl.style.color = "";
        }

        function escapeHtml(value) {
          return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#39;");
        }

        function sanitizeUrl(value) {
          var url = String(value || "").trim();

          if (!url) {
            return "";
          }

          if (
            /^(https?:|mailto:|tel:)/i.test(url) ||
            /^[./#?]/.test(url) ||
            !/^[a-z][a-z0-9+.-]*:/i.test(url)
          ) {
            return url;
          }

          return "";
        }

        function restorePlaceholders(text, placeholders) {
          return text.replace(/\u0000(\d+)\u0000/g, function (_, index) {
            return placeholders[Number(index)] || "";
          });
        }

        function renderInlineMarkdown(value) {
          var placeholders = [];
          var text = escapeHtml(value);

          function stash(html) {
            placeholders.push(html);
            return "\u0000" + (placeholders.length - 1) + "\u0000";
          }

          text = text.replace(/`([^`]+)`/g, function (_, code) {
            return stash("<code>" + code + "</code>");
          });

          text = text.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (_, label, url) {
            var safeUrl = sanitizeUrl(url);
            if (!safeUrl) {
              return label;
            }

            return stash(
              '<a href="' +
                escapeHtml(safeUrl) +
                '" target="_blank" rel="noopener noreferrer">' +
                label +
                "</a>"
            );
          });

          text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
          text = text.replace(/\*([^*]+)\*/g, "<em>$1</em>");

          return restorePlaceholders(text, placeholders);
        }

        function renderMarkdown(value) {
          var lines = String(value || "").replace(/\r\n?/g, "\n").split("\n");
          var html = [];
          var paragraph = [];
          var listType = null;
          var listItems = [];

          function flushParagraph() {
            if (!paragraph.length) {
              return;
            }

            html.push("<p>" + renderInlineMarkdown(paragraph.join(" ")) + "</p>");
            paragraph = [];
          }

          function flushList() {
            if (!listType || !listItems.length) {
              listType = null;
              listItems = [];
              return;
            }

            html.push(
              "<" +
                listType +
                ">" +
                listItems
                  .map(function (item) {
                    return "<li>" + renderInlineMarkdown(item) + "</li>";
                  })
                  .join("") +
                "</" +
                listType +
                ">"
            );
            listType = null;
            listItems = [];
          }

          lines.forEach(function (line) {
            var trimmed = line.trim();
            var unorderedMatch = /^[-*+]\s+(.+)$/.exec(trimmed);
            var orderedMatch = /^(\d+)\.\s+(.+)$/.exec(trimmed);

            if (!trimmed) {
              flushParagraph();
              flushList();
              return;
            }

            if (unorderedMatch) {
              flushParagraph();
              if (listType !== "ul") {
                flushList();
                listType = "ul";
              }
              listItems.push(unorderedMatch[1]);
              return;
            }

            if (orderedMatch) {
              flushParagraph();
              if (listType !== "ol") {
                flushList();
                listType = "ol";
              }
              listItems.push(orderedMatch[2]);
              return;
            }

            flushList();
            paragraph.push(trimmed);
          });

          flushParagraph();
          flushList();

          return html.join("") || "<p class='muted'>Keine Vorschau vorhanden.</p>";
        }

        function updatePreview(node) {
          function v(name) {
            return node.querySelector("[name='" + name + "']").value.trim();
          }

          var date = v("date");
          var title = v("title");
          var text = v("text");
          var publishedFrom = v("published_from");
          var publishedUntil = v("published_until");
          var flyerUrl = sanitizeUrl(v("flyer_url"));
          var flyerLabel = v("flyer_label") || "Flyer (PDF)";
          var flyerText = v("flyer_text");
          var stateEl = node.querySelector("[data-preview='state']");
          var publicationState = getPublicationState(
            publishedFrom,
            publishedUntil,
            node.dataset.legacyDraft === "true"
          );
          var stateLabels = {
            draft: "Entwurf",
            scheduled: "Geplant",
            expired: "Archiviert",
            invalid: "Datum prüfen",
          };

          node.querySelector("[data-preview='date']").textContent = date || "Datum";
          node.querySelector("[data-preview='title']").textContent = title || "Titel";
          node.querySelector("[data-preview='text']").innerHTML = renderMarkdown(text);
          stateEl.hidden = publicationState === "live";
          stateEl.textContent = stateLabels[publicationState] || "Entwurf";
          node.querySelector("[data-preview='actions']").innerHTML = flyerUrl
            ? '<span class="button-preview">' + escapeHtml(flyerLabel) + "</span>"
            : '<span class="muted">' + escapeHtml(flyerText || "Kein Flyer verlinkt") + "</span>";
        }

        function createItem(item) {
          var node = template.content.firstElementChild.cloneNode(true);
          var hasWindow = String(item.published_from || "").trim() || String(item.published_until || "").trim();
          node.querySelector("[name='date']").value = item.date || "";
          node.querySelector("[name='title']").value = item.title || "";
          node.querySelector("[name='text']").value = item.text || "";
          node.querySelector("[name='published_from']").value = toDateInputValue(item.published_from || "");
          node.querySelector("[name='published_until']").value = toDateInputValue(item.published_until || "");
          node.querySelector("[name='flyer_url']").value = item.flyer_url || "";
          node.querySelector("[name='flyer_label']").value = item.flyer_label || "";
          node.querySelector("[name='flyer_text']").value = item.flyer_text || "";
          node.dataset.legacyDraft = !hasWindow && isLegacyDraftValue(item.published) ? "true" : "false";

          Array.prototype.forEach.call(
            node.querySelectorAll("input, textarea"),
            function (field) {
              field.addEventListener("input", function () {
                if (field.name === "published_from" || field.name === "published_until") {
                  node.dataset.legacyDraft = "false";
                }
                updatePreview(node);
              });
            }
          );

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

          updatePreview(node);
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
            var publishedFrom = v("published_from");
            var publishedUntil = v("published_until");
            var flyerUrl = v("flyer_url");
            var flyerLabel = v("flyer_label");
            var flyerText = v("flyer_text");
            if (publishedFrom) item.published_from = publishedFrom;
            if (publishedUntil) item.published_until = publishedUntil;
            if (!publishedFrom && !publishedUntil && card.dataset.legacyDraft === "true") {
              item.published = false;
            }
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

        function postJson(url, payload) {
          return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload || {}),
          }).then(parseJsonResponse);
        }

        function load() {
          setStatus("Lade ...");
          fetch("api/news", { cache: "no-store" })
            .then(parseJsonResponse)
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
          return postJson("api/news", payload)
            .then(function (data) {
              setStatus(data.message || "Gespeichert");
              return data;
            })
            .catch(function (err) {
              setStatus("Fehler beim Speichern: " + err.message, true);
              throw err;
            });
        }

        function commitAndPush() {
          var message = window.prompt("Commit-Message", "Update news.json");
          if (message === null) {
            return;
          }

          message = message.trim();
          if (!message) {
            setStatus("Commit-Message fehlt.", true);
            return;
          }

          save()
            .then(function () {
              setStatus("Committe und pushe ...");
              return postJson("api/git-commit-push", { message: message });
            })
            .then(function (data) {
              setStatus(data.message || "Git-Push abgeschlossen");
            })
            .catch(function (err) {
              if (/^Fehler beim Speichern: /.test(statusEl.textContent)) {
                return;
              }
              setStatus("Fehler bei Git Commit & Push: " + err.message, true);
            });
        }

        function deployNews() {
          save()
            .then(function () {
              setStatus("Deploye news.json ...");
              return postJson("api/deploy", {});
            })
            .then(function (data) {
              setStatus(data.message || "Deploy abgeschlossen");
            })
            .catch(function (err) {
              if (/^Fehler beim Speichern: /.test(statusEl.textContent)) {
                return;
              }
              setStatus("Fehler beim Deploy: " + err.message, true);
            });
        }

        addBtn.addEventListener("click", function () {
          listEl.appendChild(createItem({}));
        });
        saveBtn.addEventListener("click", save);
        gitBtn.addEventListener("click", commitAndPush);
        deployBtn.addEventListener("click", deployNews);

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


def is_published_value(value):
    if value is False:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "nein", "off"}
    return value is not False


def normalize_items(items):
    allowed = {
        "date",
        "title",
        "text",
        "flyer_url",
        "flyer_label",
        "flyer_text",
        "published_from",
        "published_until",
    }
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
        if (
            "published_from" not in clean
            and "published_until" not in clean
            and not is_published_value(item.get("published", True))
        ):
            clean["published"] = False
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


def run_command(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(message or f"Command failed: {' '.join(cmd)}")
    return result


def find_git_root(path):
    directory = os.path.dirname(os.path.realpath(path)) or "."
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=directory,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(message or "Git-Repository nicht gefunden")
    return os.path.realpath(result.stdout.strip())


def git_commit_and_push(news_path, message):
    message = str(message or "").strip()
    if not message:
        raise ValueError("Commit-Message fehlt")

    news_path = os.path.realpath(news_path)
    repo_root = find_git_root(news_path)
    common_root = os.path.commonpath([news_path, repo_root])
    if common_root != repo_root:
        raise RuntimeError("news.json liegt nicht im Git-Repository")

    rel_path = os.path.relpath(news_path, repo_root)
    run_command(["git", "add", "--", rel_path], cwd=repo_root)
    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", rel_path],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if diff_result.returncode != 0:
        message_text = (diff_result.stderr or diff_result.stdout or "").strip()
        raise RuntimeError(message_text or "Git-Status konnte nicht geprüft werden")
    if not diff_result.stdout.strip():
        return "Keine Änderungen in news.json zum Committen."

    run_command(
        ["git", "commit", "--no-gpg-sign", "-m", message, "--only", "--", rel_path],
        cwd=repo_root,
    )
    run_command(["git", "push"], cwd=repo_root)
    return "news.json wurde committed und gepusht."


def deploy_news(news_path, deploy_dir):
    news_path = os.path.realpath(news_path)
    deploy_dir = os.path.realpath(deploy_dir)
    os.makedirs(deploy_dir, exist_ok=True)
    target_path = os.path.join(deploy_dir, "news.json")
    tmp_path = f"{target_path}.tmp"
    shutil.copyfile(news_path, tmp_path)
    os.replace(tmp_path, target_path)
    return f"news.json wurde nach {deploy_dir} deployt."


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
        content_length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(content_length)
        raw_text = body.decode("utf-8") if body else ""

        if self.path == "/api/news":
            try:
                data = json.loads(raw_text)
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
            return

        if self.path == "/api/git-commit-push":
            try:
                data = json.loads(raw_text or "{}")
                if not isinstance(data, dict):
                    raise ValueError("Ungültige Anfrage")
                result_message = git_commit_and_push(
                    self.server.news_file, data.get("message", "")
                )
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
            self.wfile.write(json.dumps({"message": result_message}).encode("utf-8"))
            return

        if self.path == "/api/deploy":
            try:
                result_message = deploy_news(
                    self.server.news_file, self.server.deploy_dir
                )
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
            self.wfile.write(json.dumps({"message": result_message}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, fmt, *args):
        return


def main(argv):
    parser = argparse.ArgumentParser(description="CRUD UI for static/news.json")
    parser.add_argument("--file", default=DEFAULT_NEWS_FILE, help="Path to news.json")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8765, help="Bind port")
    parser.add_argument(
        "--deploy-dir",
        default=DEFAULT_DEPLOY_DIR,
        help="Deploy target for news.json",
    )
    args = parser.parse_args(argv)

    server = HTTPServer((args.host, args.port), NewsHandler)
    server.news_file = os.path.abspath(args.file)
    server.deploy_dir = os.path.abspath(args.deploy_dir)
    print(f"News admin running on http://{args.host}:{args.port}")
    print(f"Editing: {server.news_file}")
    print(f"Deploy dir: {server.deploy_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main(sys.argv[1:])
