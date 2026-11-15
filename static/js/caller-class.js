(function () {
  var escapeHtml = window.OhmoorsNews.escapeHtml;
  var STATUS_URL = "https://class.kryptikk.de/classes/1/status.json";
  var STORAGE_KEY = "ohmoors-caller-only-taught";
  var statusEl = document.getElementById("caller-status");
  var listEl = document.getElementById("caller-list");
  var nameEl = document.getElementById("caller-class-name");
  var standEl = document.getElementById("caller-stand");
  var countEl = document.getElementById("caller-count");
  var toggleEl = document.getElementById("caller-only-taught");
  var dateFormatter = new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });

  function parseDate(value) {
    if (!value) {
      return null;
    }

    var rawValue = String(value);
    var date = /^\d{4}-\d{2}-\d{2}$/.test(rawValue)
      ? new Date(rawValue + "T00:00:00")
      : new Date(rawValue);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function latestClassDate(startsOn, figures) {
    var latest = parseDate(startsOn);

    figures.forEach(function (figure) {
      [figure.first_taught, figure.last_taught, figure.last_reviewed].forEach(function (value) {
        var date = parseDate(value);
        if (date && (!latest || date > latest)) {
          latest = date;
        }
      });
    });

    return latest ? dateFormatter.format(latest) : "-";
  }

  function isTaught(figure) {
    return Boolean(figure.teached || figure.taught || figure.first_taught);
  }

  function groupFigures(figures) {
    var groups = [];
    var groupsByNumber = Object.create(null);

    figures.forEach(function (figure) {
      var number = String(figure.number || "");
      var group = groupsByNumber[number];

      if (!group) {
        group = { number: number, figures: [] };
        groupsByNumber[number] = group;
        groups.push(group);
      }

      group.figures.push(figure);
    });

    return groups;
  }

  function renderList(groups) {
    return groups
      .map(function (group) {
        return group.figures
          .map(function (figure, index) {
            return (
              '<li class="caller-fig ' +
              (isTaught(figure) ? "taught" : "open") +
              '"><span class="num">' +
              (index === 0 ? escapeHtml(group.number) : "") +
              '</span><span class="name">' +
              escapeHtml(figure.call_name || "") +
              "</span></li>"
            );
          })
          .join("");
      })
      .join("");
  }

  function applyOnlyTaught(on) {
    toggleEl.checked = on;
    listEl.classList.toggle("only-taught", on);
  }

  function restoreToggle() {
    var stored = null;
    try {
      stored = window.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      stored = null;
    }
    applyOnlyTaught(stored === "1");
  }

  toggleEl.addEventListener("change", function () {
    applyOnlyTaught(toggleEl.checked);
    try {
      window.localStorage.setItem(STORAGE_KEY, toggleEl.checked ? "1" : "0");
    } catch (error) {
      /* Speichern nicht moeglich, Ansicht funktioniert trotzdem. */
    }
  });

  restoreToggle();

  fetch(STATUS_URL, { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(function (data) {
      data = data || {};
      var classInfo = data.class || {};
      var figures = Array.isArray(data.figures) ? data.figures : [];
      var taught = figures.filter(isTaught).length;

      listEl.innerHTML = renderList(groupFigures(figures));
      nameEl.textContent = classInfo.name || "Class";
      standEl.textContent = "Stand: " + latestClassDate(classInfo.starts_on, figures);
      countEl.textContent = taught + " / " + figures.length + " gelernt";
      statusEl.textContent = "";
    })
    .catch(function () {
      statusEl.textContent = "Class-Fortschritt konnte nicht geladen werden.";
      listEl.innerHTML = "";
    });
})();
