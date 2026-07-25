/**
 * Fetches live verse text from the YouVersion Platform REST API and injects
 * it next to the static (book-verbatim) quote on each day page. This makes
 * every page view a real, countable call against the registered YV Platform
 * app — not just a static hyperlink out to bible.com.
 *
 * The API's CORS policy (access-control-allow-origin: *) allows direct
 * browser calls, so no server proxy is needed.
 */
(function () {
  var APP_KEY = "geVqn5fdPpaEp06QTEUAdJvzn8V2Sc1numq2LfwpJREmAS0X";
  var BIBLE_ID = "3034"; // Berean Standard Bible — freely licensed, no extra steps required
  var API_BASE = "https://api.youversion.com/v1/bibles/" + BIBLE_ID + "/passages/";

  function renderLive(container, data) {
    container.innerHTML =
      '<p class="live-scripture-text">&ldquo;' + data.content + '&rdquo;</p>' +
      '<p class="live-scripture-credit">' + data.reference + ' (BSB) &mdash; live from <strong>YouVersion Platform</strong></p>';
    container.classList.add("is-loaded");
  }

  function loadOne(container) {
    var ref = container.getAttribute("data-yv-ref");
    if (!ref) return;
    fetch(API_BASE + encodeURIComponent(ref), {
      headers: { "X-YVP-App-Key": APP_KEY },
    })
      .then(function (res) {
        if (!res.ok) throw new Error("YouVersion API error " + res.status);
        return res.json();
      })
      .then(function (data) {
        renderLive(container, data);
      })
      .catch(function () {
        // Fail silently — the static, book-verbatim quote above is still shown.
        container.style.display = "none";
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var nodes = document.querySelectorAll("[data-yv-ref]");
    nodes.forEach(loadOne);
  });
})();
