/*
 * Gemeinsamer Code fuer News-Rendering und Veroeffentlichungslogik.
 * Wird von index.html, news.html, class.html, schedule.html und der
 * News-Admin-Vorschau (scripts/news_admin.py) genutzt.
 * Exportiert genau ein Global: window.OhmoorsNews.
 */
(function (global) {
  "use strict";

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function unescapeHtml(value) {
    return String(value || "")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&amp;/g, "&");
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

  function renderInlineMarkdown(value, options) {
    var linkAttrs =
      options && options.externalLinks ? ' target="_blank" rel="noopener noreferrer"' : "";
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
      var safeUrl = sanitizeUrl(unescapeHtml(url));
      if (!safeUrl) {
        return label;
      }

      return stash('<a href="' + escapeHtml(safeUrl) + '"' + linkAttrs + ">" + label + "</a>");
    });

    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    text = text.replace(/\*([^*]+)\*/g, "<em>$1</em>");

    return restorePlaceholders(text, placeholders);
  }

  function renderMarkdown(value, options) {
    var lines = String(value || "")
      .replace(/\r\n?/g, "\n")
      .split("\n");
    var html = [];
    var paragraph = [];
    var listType = null;
    var listItems = [];

    function flushParagraph() {
      if (!paragraph.length) {
        return;
      }

      html.push("<p>" + renderInlineMarkdown(paragraph.join(" "), options) + "</p>");
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
              return "<li>" + renderInlineMarkdown(item, options) + "</li>";
            })
            .join("") +
          "</" +
          listType +
          ">",
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

    return html.join("") || "<p></p>";
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

  function isFeaturedValue(value) {
    if (value === true) {
      return true;
    }

    if (typeof value === "string") {
      return /^(true|1|yes|ja|on)$/i.test(value.trim());
    }

    return false;
  }

  function isLegacyDraft(item) {
    return isLegacyDraftValue(item && item.published);
  }

  function isFeatured(item) {
    return isFeaturedValue(item && item.featured);
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

    match = /^(\d{1,2})-(\d{1,2})-(\d{4})$/.exec(text);
    if (match) {
      return match[3] + "-" + pad2(match[2]) + "-" + pad2(match[1]);
    }

    return "";
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

  function isPublished(item, todayKey) {
    var fromRaw = item && item.published_from;
    var untilRaw = item && item.published_until;
    var from = parsePublicationDateKey(fromRaw);
    var until = parsePublicationDateKey(untilRaw);
    var hasWindow = String(fromRaw || "").trim() || String(untilRaw || "").trim();
    var hasInvalidDate =
      (String(fromRaw || "").trim() && !from) || (String(untilRaw || "").trim() && !until);
    var today = todayKey || getBerlinTodayKey();

    if (hasInvalidDate) {
      return false;
    }

    if (!hasWindow && isLegacyDraft(item)) {
      return false;
    }

    if (from && today < from) {
      return false;
    }

    if (until && today > until) {
      return false;
    }

    return true;
  }

  global.OhmoorsNews = {
    escapeHtml: escapeHtml,
    unescapeHtml: unescapeHtml,
    sanitizeUrl: sanitizeUrl,
    renderInlineMarkdown: renderInlineMarkdown,
    renderMarkdown: renderMarkdown,
    pad2: pad2,
    isLegacyDraftValue: isLegacyDraftValue,
    isFeaturedValue: isFeaturedValue,
    isLegacyDraft: isLegacyDraft,
    isFeatured: isFeatured,
    parsePublicationDateKey: parsePublicationDateKey,
    getBerlinTodayKey: getBerlinTodayKey,
    isPublished: isPublished,
  };
})(window);
