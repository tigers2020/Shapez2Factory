(function () {
  var dialog = document.getElementById("gallery-viewer");
  if (!dialog || typeof dialog.showModal !== "function") {
    return;
  }
  var img = document.getElementById("gallery-viewer-img");
  var title = document.getElementById("gallery-viewer-title");
  var section = document.getElementById("gallery-viewer-section");
  var meta = document.getElementById("gallery-viewer-meta");
  var origin = document.getElementById("gallery-viewer-origin");
  var prevButton = document.getElementById("gallery-viewer-prev");
  var nextButton = document.getElementById("gallery-viewer-next");
  if (!img || !title || !section || !meta || !origin || !prevButton || !nextButton) {
    return;
  }

  var triggerMap = {};
  var activeGroup = null;
  var activeIndex = 0;

  function updateNavState() {
    var groupItems = triggerMap[activeGroup] || [];
    prevButton.disabled = activeIndex <= 0;
    nextButton.disabled = activeIndex >= groupItems.length - 1;
  }

  function renderTrigger(trigger) {
    var url = trigger.getAttribute("data-gallery-view");
    var alt = trigger.getAttribute("data-gallery-alt") || "";
    var imageTitle = trigger.getAttribute("data-gallery-title") || "Preview";
    var imageSection = trigger.getAttribute("data-gallery-section") || "Gallery";
    var filename = trigger.getAttribute("data-gallery-filename") || "";
    if (!url) {
      return;
    }
    img.removeAttribute("src");
    img.alt = alt;
    img.src = url;
    title.textContent = imageTitle;
    section.textContent = imageSection;
    meta.textContent = filename;
    origin.href = url;
    origin.setAttribute("aria-label", "Open original image for " + imageTitle);
    updateNavState();
  }

  function openFromTrigger(trigger) {
    activeGroup = trigger.getAttribute("data-gallery-group") || "default";
    activeIndex = Number(trigger.getAttribute("data-gallery-index") || "0");
    renderTrigger(trigger);
    dialog.showModal();
  }

  function step(delta) {
    var groupItems = triggerMap[activeGroup] || [];
    var nextIndex = activeIndex + delta;
    if (nextIndex < 0 || nextIndex >= groupItems.length) {
      return;
    }
    activeIndex = nextIndex;
    renderTrigger(groupItems[activeIndex]);
  }

  document.querySelectorAll("[data-gallery-view]").forEach(function (trigger) {
    var group = trigger.getAttribute("data-gallery-group") || "default";
    if (!triggerMap[group]) {
      triggerMap[group] = [];
    }
    triggerMap[group].push(trigger);
    trigger.addEventListener("click", function () {
      openFromTrigger(trigger);
    });
  });

  prevButton.addEventListener("click", function () {
    step(-1);
  });

  nextButton.addEventListener("click", function () {
    step(1);
  });

  dialog.addEventListener("click", function (e) {
    if (e.target === dialog) {
      dialog.close();
    }
  });

  dialog.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      step(-1);
    }
    if (e.key === "ArrowRight") {
      e.preventDefault();
      step(1);
    }
  });

  dialog.addEventListener("close", function () {
    img.removeAttribute("src");
    img.alt = "";
    title.textContent = "Preview";
    section.textContent = "Gallery";
    meta.textContent = "";
    origin.href = "#";
    prevButton.disabled = true;
    nextButton.disabled = true;
    activeGroup = null;
    activeIndex = 0;
  });
})();
