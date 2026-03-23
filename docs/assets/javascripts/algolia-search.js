/**
 * Algolia-powered search overlay for MkDocs Material.
 *
 * Replaces the built-in search dialog with an Algolia InstantSearch
 * modal.  Reads credentials from the `extra.algolia` block in
 * mkdocs.yml (injected by the macros plugin as global template vars).
 *
 * Dependencies loaded from CDN at runtime:
 *   - algoliasearch/lite (search client)
 *   - instantsearch.js   (UI widgets)
 */

(function () {
  "use strict";

  /* ---- Configuration --------------------------------------------------- */

  // MkDocs Material injects `extra` vars on window.__md_extra or on the
  // page as <script id="__config"> JSON.  We read from the latter.
  function getAlgoliaConfig() {
    try {
      var el = document.getElementById("__config");
      if (el) {
        var cfg = JSON.parse(el.textContent);
        var a = (cfg.extra || {}).algolia || {};
        if (a.app_id && a.api_key && a.index_name) return a;
      }
    } catch (_) {
      // ignore
    }
    return null;
  }

  var CONF = getAlgoliaConfig();
  if (!CONF) return; // Algolia not configured -- do nothing

  /* ---- Lazy-load Algolia libs ------------------------------------------ */

  var LOADED = false;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function loadCSS(href) {
    var l = document.createElement("link");
    l.rel = "stylesheet";
    l.href = href;
    document.head.appendChild(l);
  }

  function ensureLibs() {
    if (LOADED) return Promise.resolve();
    loadCSS(
      "https://cdn.jsdelivr.net/npm/instantsearch.css@8/themes/reset-min.css"
    );
    return Promise.all([
      loadScript(
        "https://cdn.jsdelivr.net/npm/algoliasearch@4/dist/algoliasearch-lite.umd.js"
      ),
      loadScript(
        "https://cdn.jsdelivr.net/npm/instantsearch.js@4/dist/instantsearch.production.min.js"
      ),
    ]).then(function () {
      LOADED = true;
    });
  }

  /* ---- Modal DOM ------------------------------------------------------- */

  function createModal() {
    var overlay = document.createElement("div");
    overlay.id = "algolia-search-overlay";
    overlay.innerHTML = [
      '<div id="algolia-search-modal">',
      '  <div id="algolia-search-header">',
      '    <div id="algolia-searchbox"></div>',
      '    <button id="algolia-search-close" aria-label="Close search">&times;</button>',
      "  </div>",
      '  <div id="algolia-search-body">',
      '    <div id="algolia-hits"></div>',
      '    <div id="algolia-no-results" style="display:none">',
      "      <p>No results found. Try different keywords.</p>",
      "    </div>",
      "  </div>",
      '  <div id="algolia-search-footer">',
      '    <div id="algolia-stats"></div>',
      '    <a href="https://www.algolia.com" target="_blank" rel="noopener"',
      '       class="algolia-brand">Search by Algolia</a>',
      "  </div>",
      "</div>",
    ].join("\n");

    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeModal();
    });

    document.body.appendChild(overlay);
    return overlay;
  }

  var modal = null;
  var searchInstance = null;

  function openModal() {
    ensureLibs().then(function () {
      if (!modal) {
        modal = createModal();
        initInstantSearch();
      }
      modal.classList.add("active");
      document.body.style.overflow = "hidden";
      setTimeout(function () {
        var input = modal.querySelector(".ais-SearchBox-input");
        if (input) input.focus();
      }, 100);
    });
  }

  function closeModal() {
    if (modal) {
      modal.classList.remove("active");
      document.body.style.overflow = "";
    }
  }

  /* ---- InstantSearch --------------------------------------------------- */

  function initInstantSearch() {
    /* global algoliasearch, instantsearch */
    var client = algoliasearch(CONF.app_id, CONF.api_key);

    searchInstance = instantsearch({
      indexName: CONF.index_name,
      searchClient: client,
      searchFunction: function (helper) {
        var container = document.getElementById("algolia-no-results");
        helper.search();
        helper.once("result", function (content) {
          if (container) {
            container.style.display =
              helper.state.query && content.results.nbHits === 0
                ? "block"
                : "none";
          }
        });
      },
    });

    searchInstance.addWidgets([
      instantsearch.widgets.searchBox({
        container: "#algolia-searchbox",
        placeholder: "Search documentation...",
        autofocus: true,
        showReset: true,
        showSubmit: false,
        cssClasses: { input: "algolia-input" },
      }),

      instantsearch.widgets.hits({
        container: "#algolia-hits",
        templates: {
          item: function (hit) {
            var title =
              instantsearch.highlight({
                attribute: "title",
                hit: hit,
              }) || hit.title;

            var heading = hit.heading
              ? instantsearch.highlight({ attribute: "heading", hit: hit })
              : "";

            var snippet = hit._snippetResult && hit._snippetResult.content
              ? hit._snippetResult.content.value
              : (hit.description || "").substring(0, 120);

            var url = hit.url || "#";
            // Fix relative URLs for MkDocs sub-site deployments
            var baseUrl = (document.querySelector('link[rel="canonical"]') || {}).href || "";
            if (baseUrl && url.startsWith("/")) {
              try {
                var base = new URL(baseUrl);
                url = base.origin + base.pathname.replace(/\/[^/]*$/, "") + url;
              } catch (_) {
                // keep original
              }
            }

            var badges = [];
            if (hit.content_type) badges.push(hit.content_type);
            if (hit.product && hit.product !== "both") badges.push(hit.product);

            var badgeHtml = badges
              .map(function (b) {
                return '<span class="algolia-badge">' + b + "</span>";
              })
              .join(" ");

            return [
              '<a class="algolia-hit" href="' + url + '">',
              '  <div class="algolia-hit-title">' + title + "</div>",
              heading
                ? '  <div class="algolia-hit-heading">' + heading + "</div>"
                : "",
              '  <div class="algolia-hit-snippet">' + snippet + "</div>",
              badgeHtml
                ? '  <div class="algolia-hit-badges">' + badgeHtml + "</div>"
                : "",
              "</a>",
            ].join("\n");
          },
          empty: "",
        },
      }),

      instantsearch.widgets.stats({
        container: "#algolia-stats",
        templates: {
          text: function (data) {
            return data.nbHits + " result" + (data.nbHits !== 1 ? "s" : "") +
              " in " + data.processingTimeMS + "ms";
          },
        },
      }),
    ]);

    searchInstance.start();
  }

  /* ---- Hook into MkDocs Material search button ------------------------- */

  function interceptSearch() {
    // MkDocs Material uses a <label> with for="__search" to toggle search.
    // We intercept clicks on that label and open Algolia instead.
    document.addEventListener("click", function (e) {
      var target = e.target.closest('[for="__search"], .md-search__icon');
      if (target) {
        e.preventDefault();
        e.stopPropagation();
        openModal();
      }
    });

    // Also intercept the keyboard shortcut (Material uses 's' or '/')
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" || e.key === "s") {
        // Only if not typing in an input
        var tag = (e.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea" || tag === "select") return;
        if (e.target.isContentEditable) return;
        e.preventDefault();
        openModal();
      }
      if (e.key === "Escape") {
        closeModal();
      }
    });

    // Close button
    document.addEventListener("click", function (e) {
      if (e.target.id === "algolia-search-close") {
        closeModal();
      }
    });
  }

  /* ---- Init ------------------------------------------------------------ */

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", interceptSearch);
  } else {
    interceptSearch();
  }
})();
