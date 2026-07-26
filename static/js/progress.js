(function () {
  "use strict";
  var STORAGE_KEY = "yesToJesus.completedDays";

  function getCompleted() {
    try {
      return new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]"));
    } catch (e) {
      return new Set();
    }
  }

  function setCompleted(set) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(set)));
    } catch (e) {
      /* localStorage unavailable (private browsing, etc.) — fail silently */
    }
  }

  function initToggle(completed) {
    var btn = document.querySelector(".complete-toggle");
    if (!btn) return;
    var slug = btn.getAttribute("data-day-slug");
    var label = btn.querySelector(".complete-toggle-label");

    function render() {
      var isDone = completed.has(slug);
      btn.classList.toggle("is-complete", isDone);
      btn.setAttribute("aria-pressed", String(isDone));
      label.textContent = isDone ? "Day Complete" : "Mark as Complete";
    }

    btn.addEventListener("click", function () {
      if (completed.has(slug)) {
        completed.delete(slug);
      } else {
        completed.add(slug);
      }
      setCompleted(completed);
      render();
    });

    render();
  }

  function initDayGrid(completed) {
    var cards = document.querySelectorAll(".day-card[data-day-slug]");
    cards.forEach(function (card) {
      if (completed.has(card.getAttribute("data-day-slug"))) {
        card.classList.add("is-complete");
      }
    });
  }

  function init() {
    var completed = getCompleted();
    initToggle(completed);
    initDayGrid(completed);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
