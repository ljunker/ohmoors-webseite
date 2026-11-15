(function () {
  var N = window.OhmoorsNews;
  var escapeHtml = N.escapeHtml;
  var sanitizeUrl = N.sanitizeUrl;
  var renderMarkdown = N.renderMarkdown;
  var isFeatured = N.isFeatured;
  var isPublished = N.isPublished;
  var defaultEl = document.getElementById("home-default");
  var featuredEl = document.getElementById("home-featured");

  function renderFeatured(newsItems) {
    var items = newsItems.filter(function (item) {
      return item && isFeatured(item) && isPublished(item);
    });

    if (!items.length) {
      return;
    }

    featuredEl.innerHTML = items
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
          : flyerText
            ? '<span class="muted">' + flyerText + "</span>"
            : "";

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
          (actionHtml ? '<div class="news-actions">' + actionHtml + "</div>" : "") +
          "</article>"
        );
      })
      .join("");
    defaultEl.hidden = true;
    featuredEl.hidden = false;
  }

  fetch("news.json", { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      if (Array.isArray(data)) {
        renderFeatured(data);
      }
    })
    .catch(function () {});
})();
