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
DEFAULT_TEMPLATES_FILE = os.path.join(BASE_DIR, "static", "news_templates.json")
DEFAULT_DEPLOY_DIR = "/var/www/ohmoors.de/html"


HTML_PAGE = r"""<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8" />
    <title>News Admin</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root {
        color-scheme: light;
        --bg: #f3f5f8;
        --surface: #ffffff;
        --surface-soft: #f8fafc;
        --text: #111827;
        --muted: #6b7280;
        --border: #dbe2ea;
        --accent: #419545;
        --accent-soft: #edf7ee;
        --danger-bg: #fff1f2;
        --danger-text: #9f1239;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Manrope", "Avenir Next", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        color: var(--text);
        background: var(--bg);
      }
      button,
      input,
      textarea {
        font: inherit;
      }
      .container {
        width: min(1240px, 96vw);
        margin: 20px auto 36px;
      }
      .topbar {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
      }
      .topbar-main {
        display: flex;
        align-items: flex-start;
        gap: 12px;
      }
      h1 {
        margin: 0;
        font-size: 28px;
      }
      h2,
      h3 {
        margin: 0;
      }
      .muted {
        color: var(--muted);
      }
      .intro {
        margin: 6px 0 0;
      }
      .controls {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }
      .mobile-nav-toggle,
      .nav-close {
        display: none;
        align-items: center;
        justify-content: center;
        width: 44px;
        min-width: 44px;
        height: 44px;
        padding: 0;
      }
      .mobile-nav-toggle-bars,
      .nav-close-bars {
        display: grid;
        gap: 4px;
        width: 18px;
      }
      .mobile-nav-toggle-bars span,
      .nav-close-bars span {
        display: block;
        height: 2px;
        background: currentColor;
        border-radius: 999px;
      }
      .nav-close-bars {
        position: relative;
        width: 18px;
        height: 18px;
        display: block;
      }
      .nav-close-bars span {
        position: absolute;
        top: 8px;
        left: 0;
        width: 18px;
      }
      .nav-close-bars span:first-child {
        transform: rotate(45deg);
      }
      .nav-close-bars span:last-child {
        transform: rotate(-45deg);
      }
      button {
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        padding: 10px 12px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
      }
      button.primary {
        background: var(--accent);
        color: #fff;
        border-color: var(--accent);
      }
      button.danger {
        background: var(--danger-bg);
        color: var(--danger-text);
        border-color: #fecdd3;
      }
      button:disabled {
        opacity: 0.55;
        cursor: default;
      }
      .status {
        margin-top: 12px;
        min-height: 24px;
        font-weight: 600;
      }
      .workspace {
        display: grid;
        grid-template-columns: minmax(260px, 320px) minmax(0, 1fr);
        gap: 16px;
        margin-top: 12px;
        align-items: start;
      }
      .sidebar,
      .editor-shell {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
      }
      .sidebar {
        overflow: hidden;
      }
      .sidebar-head,
      .editor-head {
        padding: 16px 16px 14px;
        border-bottom: 1px solid var(--border);
      }
      .sidebar-note,
      .editor-note {
        margin: 6px 0 0;
        font-size: 14px;
      }
      .sidebar-body {
        padding: 12px;
        display: grid;
        gap: 14px;
      }
      .nav-section {
        display: grid;
        gap: 8px;
      }
      .nav-section-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 12px;
      }
      .nav-section-head h3 {
        font-size: 16px;
      }
      .nav-count {
        font-size: 13px;
        color: var(--muted);
      }
      .nav-list {
        display: grid;
        gap: 6px;
      }
      .nav-item {
        width: 100%;
        text-align: left;
        padding: 10px 12px;
        border-radius: 8px;
        background: var(--surface-soft);
      }
      .nav-item.active {
        border-color: var(--accent);
        background: var(--accent-soft);
      }
      .nav-title {
        display: block;
        white-space: normal;
        overflow-wrap: anywhere;
        line-height: 1.3;
      }
      .nav-meta {
        display: block;
        margin-top: 4px;
        font-size: 13px;
        color: var(--muted);
        white-space: normal;
        overflow-wrap: anywhere;
        line-height: 1.35;
      }
      .nav-empty {
        margin: 0;
        padding: 12px;
        border: 1px dashed var(--border);
        border-radius: 8px;
        color: var(--muted);
        background: var(--surface-soft);
        font-size: 14px;
      }
      .editor-shell {
        min-height: 640px;
      }
      .nav-backdrop {
        display: none;
      }
      .editor-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
      }
      .editor-tag {
        display: inline-flex;
        align-items: center;
        min-height: 30px;
        padding: 0 10px;
        border-radius: 999px;
        background: var(--surface-soft);
        border: 1px solid var(--border);
        color: var(--muted);
        font-size: 13px;
        font-weight: 700;
      }
      .editor-body {
        padding: 16px;
      }
      .card {
        display: grid;
        gap: 16px;
      }
      .item-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .item-actions {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        justify-content: flex-end;
      }
      .row {
        display: grid;
        grid-template-columns: 140px minmax(0, 1fr);
        gap: 12px;
        align-items: start;
      }
      label {
        padding-top: 10px;
        font-weight: 600;
      }
      input,
      textarea {
        width: 100%;
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 10px 12px;
        background: #fff;
        color: var(--text);
      }
      textarea {
        min-height: 200px;
        resize: vertical;
      }
      .field-note {
        margin-top: 6px;
        font-size: 13px;
        color: var(--muted);
      }
      .preview-block {
        padding-top: 16px;
        border-top: 1px solid var(--border);
      }
      .preview-label {
        margin: 0 0 10px;
        font-size: 13px;
        font-weight: 700;
        color: var(--muted);
      }
      .preview-card {
        background: var(--surface-soft);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 18px 20px;
      }
      .preview-meta-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }
      .preview-meta {
        font-size: 12px;
        color: var(--muted);
      }
      .preview-state {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 0 10px;
        border-radius: 999px;
        border: 1px solid #fbcfe8;
        background: var(--danger-bg);
        color: var(--danger-text);
        font-size: 12px;
        font-weight: 700;
      }
      .preview-card h2 {
        margin: 10px 0 8px;
        font-size: 22px;
      }
      .preview-body > :first-child { margin-top: 0; }
      .preview-body > :last-child { margin-bottom: 0; }
      .preview-body ul,
      .preview-body ol {
        margin: 10px 0;
        padding-left: 22px;
      }
      .preview-body li + li {
        margin-top: 6px;
      }
      .preview-body code {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
        font-size: 0.95em;
        background: #eef3ea;
        border-radius: 6px;
        padding: 0.12em 0.4em;
      }
      .preview-body a {
        color: var(--accent);
        text-decoration: underline;
        text-decoration-thickness: 1.5px;
        text-underline-offset: 2px;
        font-weight: 600;
      }
      .preview-actions {
        margin-top: 14px;
      }
      .button-preview {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        padding: 0 18px;
        border-radius: 999px;
        background: var(--accent);
        color: #fff;
        font-weight: 600;
      }
      .empty-editor {
        padding: 36px 20px;
        text-align: center;
        color: var(--muted);
      }
      .empty-editor p {
        margin: 0;
      }
      @media (max-width: 960px) {
        .workspace {
          grid-template-columns: 1fr;
        }
        .editor-shell {
          min-height: 0;
        }
      }
      @media (max-width: 720px) {
        body.nav-open {
          overflow: hidden;
        }
        .container {
          width: min(100vw - 20px, 100%);
          margin: 10px auto 24px;
        }
        .topbar-main {
          width: 100%;
          justify-content: space-between;
        }
        .mobile-nav-toggle,
        .nav-close {
          display: inline-flex;
        }
        .topbar,
        .editor-head,
        .item-header,
        .row {
          grid-template-columns: 1fr;
          display: grid;
        }
        .topbar {
          gap: 12px;
        }
        .controls {
          width: 100%;
          justify-content: stretch;
        }
        .controls {
          padding-top: 0;
        }
        .controls button {
          flex: 1 1 calc(50% - 8px);
        }
        .sidebar {
          position: fixed;
          top: 0;
          left: 0;
          bottom: 0;
          z-index: 30;
          width: min(88vw, 360px);
          border-radius: 0 8px 8px 0;
          transform: translateX(calc(-100% - 12px));
          transition: transform 160ms ease;
          overflow: auto;
        }
        body.nav-open .sidebar {
          transform: translateX(0);
        }
        .nav-backdrop {
          position: fixed;
          inset: 0;
          z-index: 20;
          background: rgba(17, 24, 39, 0.36);
        }
        body.nav-open .nav-backdrop {
          display: block;
        }
        .sidebar-head {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
          position: sticky;
          top: 0;
          background: var(--surface);
          z-index: 1;
        }
        .sidebar-body {
          padding-bottom: 20px;
        }
        .row {
          gap: 8px;
        }
        label {
          padding-top: 0;
        }
        .item-actions {
          justify-content: stretch;
        }
        .item-actions button {
          flex: 1 1 calc(50% - 6px);
        }
        .preview-card {
          padding: 16px;
        }
        .preview-meta-row {
          align-items: flex-start;
          flex-direction: column;
        }
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="topbar">
        <div class="topbar-main">
          <div>
            <h1>News Admin</h1>
          </div>
          <button id="nav-toggle" class="mobile-nav-toggle" type="button" aria-label="Eintragsmenü öffnen" aria-expanded="false" aria-controls="sidebar">
            <span class="mobile-nav-toggle-bars" aria-hidden="true"><span></span><span></span><span></span></span>
          </button>
        </div>
        <div class="controls">
          <button id="add-news-btn">News neu</button>
          <button id="add-template-btn">Vorlage neu</button>
          <button id="save-btn" class="primary">Alles speichern</button>
          <button id="git-btn">Git Commit & Push</button>
          <button id="deploy-btn">Deploy news.json</button>
        </div>
      </div>
      <div id="status" class="status muted"></div>

      <div class="workspace">
        <aside id="sidebar" class="sidebar">
          <div class="sidebar-head">
            <div>
              <h2>Einträge</h2>
            </div>
            <button id="nav-close" class="nav-close" type="button" aria-label="Eintragsmenü schließen">
              <span class="nav-close-bars" aria-hidden="true"><span></span><span></span></span>
            </button>
          </div>
          <div class="sidebar-body">
            <section class="nav-section">
              <div class="nav-section-head">
                <h3>News</h3>
                <span id="news-count" class="nav-count"></span>
              </div>
              <div id="news-nav" class="nav-list"></div>
            </section>
            <section class="nav-section">
              <div class="nav-section-head">
                <h3>Vorlagen</h3>
                <span id="templates-count" class="nav-count"></span>
              </div>
              <div id="template-nav" class="nav-list"></div>
            </section>
          </div>
        </aside>

        <main class="editor-shell">
          <div class="editor-head">
            <div>
              <h2 id="editor-title">Eintrag bearbeiten</h2>
              <p id="editor-note" class="editor-note muted">Wähle einen Eintrag in der Navigation aus.</p>
            </div>
            <div id="editor-kind" class="editor-tag">Keine Auswahl</div>
          </div>
          <div id="editor" class="editor-body">
            <div class="empty-editor">
              <p>Es ist noch kein Eintrag ausgewählt.</p>
            </div>
          </div>
        </main>
      </div>
    </div>
    <div id="nav-backdrop" class="nav-backdrop" hidden></div>

    <template id="editor-template">
      <div class="card">
        <div class="item-header">
          <strong data-role="kind-label">News</strong>
          <div class="item-actions">
            <button data-action="copy-to-news" data-role="template-action">In News kopieren</button>
            <button data-action="copy-to-template" data-role="news-action">Als Vorlage</button>
            <button data-action="up">Hoch</button>
            <button data-action="down">Runter</button>
            <button data-action="delete" class="danger">Löschen</button>
          </div>
        </div>
        <div class="row">
          <label for="editor-date">Datum</label>
          <input id="editor-date" name="date" placeholder="z.B. 16. Feb. 2026" />
        </div>
        <div class="row">
          <label for="editor-title-input">Titel</label>
          <input id="editor-title-input" name="title" placeholder="Titel" />
        </div>
        <div class="row">
          <label for="editor-text">Text</label>
          <div>
            <textarea id="editor-text" name="text" placeholder="Kurztext in Markdown"></textarea>
            <div class="field-note">Markdown: Absätze, Listen, Links, <code>**fett**</code>, <code>*kursiv*</code>, <code>`code`</code></div>
          </div>
        </div>
        <div class="row">
          <label for="editor-published-from">Veröffentlicht ab</label>
          <div>
            <input id="editor-published-from" name="published_from" type="date" />
            <div class="field-note">Leer = sofort sichtbar. Die Auswahl nutzt den Kalender des Browsers und wird als Datum gespeichert.</div>
          </div>
        </div>
        <div class="row">
          <label for="editor-published-until">Veröffentlicht bis</label>
          <div>
            <input id="editor-published-until" name="published_until" type="date" />
            <div class="field-note">Leer = unbegrenzt sichtbar. Mit beiden Feldern entsteht ein Veröffentlichungszeitraum.</div>
          </div>
        </div>
        <div class="row">
          <label for="editor-flyer-url">Flyer URL</label>
          <input id="editor-flyer-url" name="flyer_url" placeholder="2026-Rosenmontag.pdf" />
        </div>
        <div class="row">
          <label for="editor-flyer-label">Flyer Label</label>
          <input id="editor-flyer-label" name="flyer_label" placeholder="Flyer (PDF)" />
        </div>
        <div class="row">
          <label for="editor-flyer-text">Flyer Text (ohne URL)</label>
          <input id="editor-flyer-text" name="flyer_text" placeholder="Flyer folgt" />
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
        var newsNavEl = document.getElementById("news-nav");
        var templateNavEl = document.getElementById("template-nav");
        var newsCountEl = document.getElementById("news-count");
        var templatesCountEl = document.getElementById("templates-count");
        var editorEl = document.getElementById("editor");
        var editorTitleEl = document.getElementById("editor-title");
        var editorNoteEl = document.getElementById("editor-note");
        var editorKindEl = document.getElementById("editor-kind");
        var statusEl = document.getElementById("status");
        var navToggleBtn = document.getElementById("nav-toggle");
        var navCloseBtn = document.getElementById("nav-close");
        var navBackdropEl = document.getElementById("nav-backdrop");
        var addNewsBtn = document.getElementById("add-news-btn");
        var addTemplateBtn = document.getElementById("add-template-btn");
        var saveBtn = document.getElementById("save-btn");
        var gitBtn = document.getElementById("git-btn");
        var deployBtn = document.getElementById("deploy-btn");
        var editorTemplate = document.getElementById("editor-template");
        var state = {
          news: [],
          templates: [],
          selectedKind: "",
          selectedIndex: -1,
        };

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

        function cloneItem(item) {
          return {
            date: item.date || "",
            title: item.title || "",
            text: item.text || "",
            flyer_url: item.flyer_url || "",
            flyer_label: item.flyer_label || "",
            flyer_text: item.flyer_text || "",
            published_from: item.published_from || "",
            published_until: item.published_until || "",
            __legacyDraft: Boolean(item.__legacyDraft),
          };
        }

        function toEditableItem(item) {
          var copy = cloneItem(item || {});
          var hasWindow = String(copy.published_from || "").trim() || String(copy.published_until || "").trim();
          copy.__legacyDraft = !hasWindow && isLegacyDraftValue(item && item.published);
          return copy;
        }

        function toPersistedItem(item) {
          var clean = {};
          var fields = [
            "date",
            "title",
            "text",
            "flyer_url",
            "flyer_label",
            "flyer_text",
            "published_from",
            "published_until",
          ];

          fields.forEach(function (key) {
            var value = String(item[key] || "").trim();
            if (value) {
              clean[key] = value;
            }
          });

          if (
            !clean.published_from &&
            !clean.published_until &&
            item.__legacyDraft
          ) {
            clean.published = false;
          }

          return clean;
        }

        function getItems(kind) {
          return kind === "template" ? state.templates : state.news;
        }

        function isMobileLayout() {
          return window.innerWidth <= 720;
        }

        function setNavOpen(isOpen) {
          if (isMobileLayout() && isOpen) {
            document.body.classList.add("nav-open");
            navBackdropEl.hidden = false;
            navToggleBtn.setAttribute("aria-expanded", "true");
            return;
          }

          document.body.classList.remove("nav-open");
          navBackdropEl.hidden = true;
          navToggleBtn.setAttribute("aria-expanded", "false");
        }

        function closeNavIfMobile() {
          if (isMobileLayout()) {
            setNavOpen(false);
          }
        }

        function hasAnyItems() {
          return state.news.length || state.templates.length;
        }

        function getSelectedItem() {
          if (!state.selectedKind || state.selectedIndex < 0) {
            return null;
          }

          return getItems(state.selectedKind)[state.selectedIndex] || null;
        }

        function ensureSelection() {
          var selectedItems;

          if (state.selectedKind) {
            selectedItems = getItems(state.selectedKind);
            if (state.selectedIndex >= 0 && state.selectedIndex < selectedItems.length) {
              return;
            }
          }

          if (state.news.length) {
            state.selectedKind = "news";
            state.selectedIndex = 0;
            return;
          }

          if (state.templates.length) {
            state.selectedKind = "template";
            state.selectedIndex = 0;
            return;
          }

          state.selectedKind = "";
          state.selectedIndex = -1;
        }

        function navTitle(item, kind, index) {
          var title = String(item.title || "").trim();
          if (title) {
            return title;
          }
          return (kind === "template" ? "Vorlage" : "News") + " " + (index + 1);
        }

        function navMeta(item) {
          var parts = [];
          var date = String(item.date || "").trim();
          var from = String(item.published_from || "").trim();
          var until = String(item.published_until || "").trim();

          if (date) {
            parts.push(date);
          }
          if (from || until) {
            parts.push((from || "sofort") + " bis " + (until || "offen"));
          }
          return parts.join(" | ");
        }

        function renderNavList(container, items, kind) {
          container.innerHTML = "";

          if (!items.length) {
            container.innerHTML = "<p class='nav-empty'>Keine Einträge vorhanden.</p>";
            return;
          }

          items.forEach(function (item, index) {
            var button = document.createElement("button");
            var meta = navMeta(item);
            button.type = "button";
            button.className = "nav-item";
            if (state.selectedKind === kind && state.selectedIndex === index) {
              button.className += " active";
            }
            button.innerHTML =
              '<span class="nav-title">' + escapeHtml(navTitle(item, kind, index)) + "</span>" +
              '<span class="nav-meta">' + escapeHtml(meta || (kind === "template" ? "Vorlage" : "News")) + "</span>";
            button.addEventListener("click", function () {
              state.selectedKind = kind;
              state.selectedIndex = index;
              renderAll();
              closeNavIfMobile();
            });
            container.appendChild(button);
          });
        }

        function renderCounts() {
          newsCountEl.textContent = state.news.length + (state.news.length === 1 ? " Eintrag" : " Einträge");
          templatesCountEl.textContent =
            state.templates.length + (state.templates.length === 1 ? " Eintrag" : " Einträge");
        }

        function updatePreview(node, item) {
          var flyerUrl = sanitizeUrl(item.flyer_url || "");
          var flyerLabel = String(item.flyer_label || "").trim() || "Flyer (PDF)";
          var flyerText = String(item.flyer_text || "").trim();
          var stateEl = node.querySelector("[data-preview='state']");
          var publicationState = getPublicationState(
            item.published_from,
            item.published_until,
            item.__legacyDraft
          );
          var stateLabels = {
            draft: "Entwurf",
            scheduled: "Geplant",
            expired: "Archiviert",
            invalid: "Datum prüfen",
          };

          node.querySelector("[data-preview='date']").textContent = String(item.date || "").trim() || "Datum";
          node.querySelector("[data-preview='title']").textContent = String(item.title || "").trim() || "Titel";
          node.querySelector("[data-preview='text']").innerHTML = renderMarkdown(item.text || "");
          stateEl.hidden = publicationState === "live";
          stateEl.textContent = stateLabels[publicationState] || "Entwurf";
          node.querySelector("[data-preview='actions']").innerHTML = flyerUrl
            ? '<span class="button-preview">' + escapeHtml(flyerLabel) + "</span>"
            : '<span class="muted">' + escapeHtml(flyerText || "Kein Flyer verlinkt") + "</span>";
        }

        function bindEditorInputs(node, item) {
          Array.prototype.forEach.call(node.querySelectorAll("input, textarea"), function (field) {
            field.addEventListener("input", function () {
              item[field.name] = field.value;
              if (field.name === "published_from" || field.name === "published_until") {
                item.__legacyDraft = false;
              }
              updatePreview(node, item);
              renderSidebar();
            });
          });
        }

        function deleteSelected() {
          var items = getItems(state.selectedKind);

          if (!items.length || state.selectedIndex < 0) {
            return;
          }

          items.splice(state.selectedIndex, 1);
          if (state.selectedIndex >= items.length) {
            state.selectedIndex = items.length - 1;
          }
          ensureSelection();
          renderAll();
        }

        function moveSelected(delta) {
          var items = getItems(state.selectedKind);
          var index = state.selectedIndex;
          var nextIndex = index + delta;
          var item;

          if (index < 0 || nextIndex < 0 || nextIndex >= items.length) {
            return;
          }

          item = items[index];
          items.splice(index, 1);
          items.splice(nextIndex, 0, item);
          state.selectedIndex = nextIndex;
          renderAll();
        }

        function copySelectedTo(targetKind) {
          var item = getSelectedItem();
          var targetItems;

          if (!item) {
            return;
          }

          targetItems = getItems(targetKind);
          targetItems.push(cloneItem(item));
          state.selectedKind = targetKind;
          state.selectedIndex = targetItems.length - 1;
          renderAll();
          setStatus(
            (targetKind === "news" ? "Vorlage in News kopiert." : "News als Vorlage kopiert.") +
              " Speichern nicht vergessen."
          );
        }

        function renderEditor() {
          var item = getSelectedItem();
          var kind = state.selectedKind;
          var node;
          var label;

          editorEl.innerHTML = "";

          if (!item) {
            editorTitleEl.textContent = "Eintrag bearbeiten";
            editorNoteEl.textContent = hasAnyItems()
              ? "Wähle einen Eintrag in der Navigation aus."
              : "Lege zuerst News oder Vorlagen an.";
            editorKindEl.textContent = "Keine Auswahl";
            editorEl.innerHTML =
              '<div class="empty-editor"><p>' +
              escapeHtml(hasAnyItems() ? "Es ist noch kein Eintrag ausgewählt." : "Noch keine Einträge vorhanden.") +
              "</p></div>";
            return;
          }

          label = kind === "template" ? "Vorlage" : "News";
          editorTitleEl.textContent = navTitle(item, kind, state.selectedIndex);
          editorNoteEl.textContent = kind === "template"
            ? "Vorlagen werden in news_templates.json gespeichert und können direkt in die News kopiert werden."
            : "News werden in news.json gespeichert und können von hier aus als Vorlage dupliziert werden.";
          editorKindEl.textContent = label;

          node = editorTemplate.content.firstElementChild.cloneNode(true);
          node.querySelector("[data-role='kind-label']").textContent = label;
          node.querySelector("[data-role='template-action']").hidden = kind !== "template";
          node.querySelector("[data-role='news-action']").hidden = kind !== "news";
          node.querySelector("[name='date']").value = item.date || "";
          node.querySelector("[name='title']").value = item.title || "";
          node.querySelector("[name='text']").value = item.text || "";
          node.querySelector("[name='published_from']").value = toDateInputValue(item.published_from || "");
          node.querySelector("[name='published_until']").value = toDateInputValue(item.published_until || "");
          node.querySelector("[name='flyer_url']").value = item.flyer_url || "";
          node.querySelector("[name='flyer_label']").value = item.flyer_label || "";
          node.querySelector("[name='flyer_text']").value = item.flyer_text || "";

          node.addEventListener("click", function (e) {
            var action = e.target && e.target.getAttribute("data-action");
            if (!action) return;
            e.preventDefault();

            if (action === "delete") {
              deleteSelected();
            } else if (action === "copy-to-news") {
              copySelectedTo("news");
            } else if (action === "copy-to-template") {
              copySelectedTo("template");
            } else if (action === "up") {
              moveSelected(-1);
            } else if (action === "down") {
              moveSelected(1);
            }
          });

          bindEditorInputs(node, item);
          updatePreview(node, item);
          editorEl.appendChild(node);
        }

        function renderSidebar() {
          renderCounts();
          renderNavList(newsNavEl, state.news, "news");
          renderNavList(templateNavEl, state.templates, "template");
        }

        function renderAll() {
          ensureSelection();
          renderSidebar();
          renderEditor();
        }

        function createNew(kind) {
          var items = getItems(kind);
          items.push(toEditableItem({}));
          state.selectedKind = kind;
          state.selectedIndex = items.length - 1;
          renderAll();
        }

        function postJson(url, payload) {
          return fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload || {}),
          }).then(parseJsonResponse);
        }

        function saveNews() {
          return postJson(
            "api/news",
            state.news.map(toPersistedItem)
          );
        }

        function saveTemplates() {
          return postJson(
            "api/templates",
            state.templates.map(toPersistedItem)
          );
        }

        function load() {
          setStatus("Lade ...");
          Promise.all([
            fetch("api/news", { cache: "no-store" }).then(parseJsonResponse),
            fetch("api/templates", { cache: "no-store" }).then(parseJsonResponse),
          ])
            .then(function (results) {
              var news = results[0];
              var templates = results[1];
              if (!Array.isArray(news)) throw new Error("news.json hat kein Array-Format");
              if (!Array.isArray(templates)) throw new Error("news_templates.json hat kein Array-Format");
              state.news = news.map(toEditableItem);
              state.templates = templates.map(toEditableItem);
              ensureSelection();
              renderAll();
              setStatus("");
            })
            .catch(function (err) {
              setStatus("Fehler beim Laden: " + err.message, true);
            });
        }

        function save() {
          setStatus("Speichere ...");
          return Promise.all([saveNews(), saveTemplates()])
            .then(function (data) {
              setStatus("Gespeichert");
              return data;
            })
            .catch(function (err) {
              setStatus("Fehler beim Speichern: " + err.message, true);
              throw err;
            });
        }

        function commitAndPush() {
          var message = window.prompt(
            "Commit-Message",
            "News aktualisieren\n\n- news.json aktualisiert\n- news_templates.json aktualisiert"
          );
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

        addNewsBtn.addEventListener("click", function () {
          createNew("news");
          closeNavIfMobile();
        });
        addTemplateBtn.addEventListener("click", function () {
          createNew("template");
          closeNavIfMobile();
        });
        navToggleBtn.addEventListener("click", function () {
          setNavOpen(!document.body.classList.contains("nav-open"));
        });
        navCloseBtn.addEventListener("click", function () {
          setNavOpen(false);
        });
        navBackdropEl.addEventListener("click", function () {
          setNavOpen(false);
        });
        window.addEventListener("resize", function () {
          if (!isMobileLayout()) {
            setNavOpen(false);
          }
        });
        saveBtn.addEventListener("click", save);
        gitBtn.addEventListener("click", commitAndPush);
        deployBtn.addEventListener("click", deployNews);

        setNavOpen(false);
        load();
      })();
    </script>
  </body>
</html>
"""


def load_items(path, label):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{label} must be a list")
    return data


def load_news(path):
    return load_items(path, "news.json")


def load_templates(path):
    return load_items(path, "news_templates.json")


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


def write_items(path, items):
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


def write_news(path, items):
    write_items(path, items)


def write_templates(path, items):
    write_items(path, items)


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


def git_commit_and_push(news_path, templates_path, message):
    message = str(message or "").strip()
    if not message:
        raise ValueError("Commit-Message fehlt")

    news_path = os.path.realpath(news_path)
    templates_path = os.path.realpath(templates_path)
    repo_root = find_git_root(news_path)
    for path, label in (
        (news_path, "news.json"),
        (templates_path, "news_templates.json"),
    ):
        common_root = os.path.commonpath([path, repo_root])
        if common_root != repo_root:
            raise RuntimeError(f"{label} liegt nicht im Git-Repository")

    rel_paths = [
        os.path.relpath(news_path, repo_root),
        os.path.relpath(templates_path, repo_root),
    ]
    run_command(["git", "add", "--", *rel_paths], cwd=repo_root)
    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", *rel_paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if diff_result.returncode != 0:
        message_text = (diff_result.stderr or diff_result.stdout or "").strip()
        raise RuntimeError(message_text or "Git-Status konnte nicht geprüft werden")
    if not diff_result.stdout.strip():
        return "Keine Änderungen in news.json oder news_templates.json zum Committen."

    run_command(
        ["git", "commit", "--no-gpg-sign", "-m", message, "--only", "--", *rel_paths],
        cwd=repo_root,
    )
    run_command(["git", "push"], cwd=repo_root)
    return "news.json und news_templates.json wurden committed und gepusht."


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

        if self.path == "/api/templates":
            try:
                data = load_templates(self.server.templates_file)
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

        if self.path == "/api/templates":
            try:
                data = json.loads(raw_text)
                if not isinstance(data, list):
                    raise ValueError("news_templates.json must be a list")
                items = normalize_items(data)
                write_templates(self.server.templates_file, items)
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
            self.wfile.write(json.dumps({"message": "Vorlagen gespeichert"}).encode("utf-8"))
            return

        if self.path == "/api/git-commit-push":
            try:
                data = json.loads(raw_text or "{}")
                if not isinstance(data, dict):
                    raise ValueError("Ungültige Anfrage")
                result_message = git_commit_and_push(
                    self.server.news_file,
                    self.server.templates_file,
                    data.get("message", ""),
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
    parser = argparse.ArgumentParser(
        description="CRUD UI for static/news.json and static/news_templates.json"
    )
    parser.add_argument("--file", default=DEFAULT_NEWS_FILE, help="Path to news.json")
    parser.add_argument(
        "--templates-file",
        default=DEFAULT_TEMPLATES_FILE,
        help="Path to news_templates.json",
    )
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
    server.templates_file = os.path.abspath(args.templates_file)
    server.deploy_dir = os.path.abspath(args.deploy_dir)
    print(f"News admin running on http://{args.host}:{args.port}")
    print(f"Editing: {server.news_file}")
    print(f"Templates: {server.templates_file}")
    print(f"Deploy dir: {server.deploy_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main(sys.argv[1:])
