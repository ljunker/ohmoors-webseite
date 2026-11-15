(function () {
  var statusEl = document.getElementById("gallery-status");
  var grid = document.getElementById("gallery-grid");
  var lightbox = document.getElementById("gallery-lightbox");
  var image = document.getElementById("gallery-lightbox-image");
  var caption = document.getElementById("gallery-lightbox-caption");
  var prevBtn = document.querySelector(".gallery-prev");
  var nextBtn = document.querySelector(".gallery-next");
  var closeBtn = document.querySelector(".gallery-close");
  var links = [];
  var currentIndex = 0;
  if (!statusEl || !grid || !lightbox || !image || !caption || !prevBtn || !nextBtn || !closeBtn) return;

  function updateStatus(text) {
    statusEl.textContent = text || "";
  }

  function bindGalleryLinks() {
    links = Array.prototype.slice.call(document.querySelectorAll(".gallery-item"));
    links.forEach(function (link, index) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        showAt(index);
        lightbox.showModal();
      });
    });
  }

  function renderGallery(items) {
    grid.innerHTML = "";
    items.forEach(function (item) {
      if (!item || !item.src) return;
      var link = document.createElement("a");
      var thumb = document.createElement("img");
      link.className = "gallery-item";
      link.href = item.src;
      link.setAttribute("data-caption", item.caption || "");
      thumb.className = "gallery-thumb";
      thumb.src = item.src;
      thumb.alt = item.alt || item.caption || "";
      thumb.loading = "lazy";
      link.appendChild(thumb);
      grid.appendChild(link);
    });

    bindGalleryLinks();
    if (!links.length) {
      updateStatus("Keine Bilder im Ordner gallery-pics gefunden.");
    } else {
      updateStatus("");
    }
  }

  function showAt(index) {
    if (!links.length) return;
    if (index < 0) index = links.length - 1;
    if (index >= links.length) index = 0;
    currentIndex = index;
    var link = links[currentIndex];
    image.src = link.getAttribute("href");
    image.alt = link.getAttribute("data-caption") || "";
    caption.textContent = link.getAttribute("data-caption") || "";
  }

  prevBtn.addEventListener("click", function () {
    showAt(currentIndex - 1);
  });

  nextBtn.addEventListener("click", function () {
    showAt(currentIndex + 1);
  });

  closeBtn.addEventListener("click", function () {
    lightbox.close();
  });

  document.addEventListener("keydown", function (e) {
    if (!lightbox.open) return;
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      showAt(currentIndex - 1);
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      showAt(currentIndex + 1);
    } else if (e.key === "Escape") {
      lightbox.close();
    }
  });

  lightbox.addEventListener("click", function (e) {
    var rect = lightbox.getBoundingClientRect();
    var inside =
      rect.top <= e.clientY &&
      e.clientY <= rect.top + rect.height &&
      rect.left <= e.clientX &&
      e.clientX <= rect.left + rect.width;
    if (!inside) lightbox.close();
  });

  fetch("gallery-pics/gallery.json", { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    })
    .then(function (data) {
      if (!Array.isArray(data)) throw new Error("gallery.json hat kein Array-Format");
      renderGallery(data);
    })
    .catch(function () {
      updateStatus("Galerie konnte nicht geladen werden.");
      grid.innerHTML = "";
    });
})();
