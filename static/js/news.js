(function () {
  var N = window.OhmoorsNews;
  var escapeHtml = N.escapeHtml;
  var sanitizeUrl = N.sanitizeUrl;
  var renderMarkdown = N.renderMarkdown;
  var parsePublicationDateKey = N.parsePublicationDateKey;
  var statusEl = document.getElementById("news-status");
  var listEl = document.getElementById("news-list");
  var debugParam = new URLSearchParams(window.location.search).get("debug") || "";

  function formatDateKeyForDebug(value) {
    var match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || "");
    if (!match) {
      return "";
    }

    return Number(match[3]) + "." + Number(match[2]) + "." + match[1];
  }

  function getDebugState(value) {
    var text = String(value || "").trim();
    var simulatedDate = parsePublicationDateKey(text);

    if (/^(1|true|yes|on)$/i.test(text)) {
      return {
        showAll: true,
        simulatedDate: "",
      };
    }

    if (simulatedDate) {
      return {
        showAll: false,
        simulatedDate: simulatedDate,
      };
    }

    return {
      showAll: false,
      simulatedDate: "",
    };
  }

  var debugState = getDebugState(debugParam);

  function isPublished(item) {
    return N.isPublished(item, debugState.simulatedDate);
  }

  function render(newsItems) {
    var publishedItems = debugState.showAll ? newsItems : newsItems.filter(isPublished);

    if (!publishedItems.length) {
      statusEl.textContent = debugState.simulatedDate
        ? "Debug-Datum aktiv: " + formatDateKeyForDebug(debugState.simulatedDate) + "."
        : "";
      listEl.innerHTML = "<p>Keine News vorhanden.</p>";
      return;
    }

    listEl.innerHTML = publishedItems
      .map(function (item) {
        var date = escapeHtml(item.date || "");
        var title = escapeHtml(item.title || "");
        var text = renderMarkdown(item.text || "");
        var flyerUrl = sanitizeUrl(item.flyer_url || "");
        var flyerLabel = escapeHtml(item.flyer_label || "Flyer (PDF)");
        var flyerText = escapeHtml(item.flyer_text || "");
        var actionHtml = flyerUrl
          ? '<a class="button" href="' +
            escapeHtml(flyerUrl) +
            '">' +
            flyerLabel +
            "</a>"
          : '<span class="muted">' + flyerText + "</span>";

        return (
          '<article class="news-card">' +
          '<div class="news-meta">' +
          date +
          "</div>" +
          "<h2>" +
          title +
          "</h2>" +
          '<div class="news-body">' +
          text +
          "</div>" +
          '<div class="news-actions">' +
          actionHtml +
          "</div>" +
          "</article>"
        );
      })
      .join("");
    statusEl.textContent = debugState.showAll
      ? "Debug-Modus aktiv: alle News werden angezeigt."
      : debugState.simulatedDate
        ? "Debug-Datum aktiv: " + formatDateKeyForDebug(debugState.simulatedDate) + "."
      : "";
  }

  fetch("news.json", { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      if (!Array.isArray(data)) {
        throw new Error("news.json hat kein Array-Format");
      }
      render(data);
    })
    .catch(function () {
      statusEl.textContent = "News konnten nicht geladen werden.";
      listEl.innerHTML = "";
    });
})();
