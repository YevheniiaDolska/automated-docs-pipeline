/*
 * API Playground loader for MkDocs Material and Docusaurus.
 *
 * Supports MkDocs Material "instant loading" (SPA navigation) by
 * re-initialising on every page change instead of relying on a one-shot IIFE.
 */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ */
  /*  Helpers                                                            */
  /* ------------------------------------------------------------------ */

  function parseBool(value, fallback) {
    if (value === undefined || value === null || value === '') {
      return fallback;
    }
    return String(value).toLowerCase() === 'true';
  }

  var _loadedScripts = {};

  function loadScript(src) {
    if (_loadedScripts[src]) {
      return _loadedScripts[src];
    }
    _loadedScripts[src] = new Promise(function (resolve, reject) {
      var existing = document.querySelector('script[src="' + src + '"]');
      if (existing) {
        resolve();
        return;
      }
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = function () {
        delete _loadedScripts[src];
        reject(new Error('Failed to load script: ' + src));
      };
      document.head.appendChild(script);
    });
    return _loadedScripts[src];
  }

  function loadCss(href) {
    if (document.querySelector('link[data-playground="' + href + '"]')) {
      return;
    }
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    link.setAttribute('data-playground', href);
    document.head.appendChild(link);
  }

  /**
   * Resolve a spec path to a full URL.
   *
   * Strategy:
   * 1. Absolute URLs (https://...) pass through unchanged.
   * 2. Relative paths are resolved against the site root.
   *    Site root is derived from <base href> (Docusaurus) or
   *    <link rel="canonical"> (MkDocs Material).
   *    As a last resort, fall back to window.location with path reset.
   */
  function resolveSpecUrl(raw) {
    if (!raw) {
      return raw;
    }
    // Already absolute
    if (/^https?:\/\//i.test(raw)) {
      return raw;
    }

    // Try <base href> (Docusaurus sets this)
    var base = document.querySelector('base[href]');
    if (base) {
      try {
        return new URL(raw, base.href).href;
      } catch (e) { /* fall through */ }
    }

    // Try canonical link (MkDocs Material always emits one).
    // canonical: https://host/base-path/section/page-name/
    // We need:   https://host/base-path/
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
      try {
        var href = canonical.getAttribute('href');
        var parsed = new URL(href);
        // Walk up from the canonical path to find the base path.
        // The site_url from mkdocs.yml is embedded in every canonical.
        // Strategy: try to fetch the spec from progressively shorter base paths.
        // Simpler: use site_url if available via meta tag, otherwise strip
        // known doc sections from the canonical path.
        var pathParts = parsed.pathname.replace(/\/+$/, '').split('/');
        // For a canonical like /automated-docs-pipeline/reference/api-playground/
        // we want /automated-docs-pipeline/
        // Heuristic: keep only the first path segment after root (the repo name).
        // More robust: look for the raw spec path within the pathname.
        // Most robust: the spec path (like "assets/api/...") is never a prefix
        // of a page path, so we just need the base path.

        // Use the full origin + whatever prefix comes before known doc sections.
        var siteRoot = parsed.origin + '/';
        var knownSections = [
          'reference/', 'how-to/', 'getting-started/', 'concepts/',
          'troubleshooting/', 'search', 'tags', 'en/', 'ru/'
        ];
        var fullPath = parsed.pathname;
        for (var i = 0; i < knownSections.length; i++) {
          var idx = fullPath.indexOf(knownSections[i]);
          if (idx > 0) {
            siteRoot = parsed.origin + fullPath.substring(0, idx);
            break;
          }
        }

        var cleanRaw = raw.replace(/^\//, '');
        return siteRoot + cleanRaw;
      } catch (e) { /* fall through */ }
    }

    // Last resort: resolve against origin
    try {
      return new URL(raw, window.location.origin + '/').href;
    } catch (e) {
      return raw;
    }
  }

  /* ------------------------------------------------------------------ */
  /*  Main init                                                          */
  /* ------------------------------------------------------------------ */

  function initPlayground() {
    var root = document.getElementById('api-playground-root');
    if (!root) {
      return;
    }

    // Prevent double-init (inline scripts set swaggerLoaded, this file sets playgroundInit)
    if (root.dataset.playgroundInit === 'true' || root.dataset.swaggerLoaded === '1') {
      return;
    }
    root.dataset.playgroundInit = 'true';

    var legacyConfig = window.API_PLAYGROUND_CONFIG || {};
    var plgConfig = window.DOCS_PLG_CONFIG || {};
    var playgroundConfig = plgConfig.api_playground || {};

    var provider = (
      root.dataset.provider ||
      playgroundConfig.provider ||
      legacyConfig.provider ||
      'swagger-ui'
    ).toLowerCase();

    var strategy = (
      root.dataset.sourceStrategy ||
      (playgroundConfig.source && playgroundConfig.source.strategy) ||
      'api-first'
    ).toLowerCase();

    var apiFirstSpecUrl =
      root.dataset.apiFirstSpecUrl ||
      (playgroundConfig.source && playgroundConfig.source.api_first_spec_url) ||
      legacyConfig.spec_url ||
      'assets/api/openapi.bundled.json';

    var codeFirstSpecUrl =
      root.dataset.codeFirstSpecUrl ||
      (playgroundConfig.source && playgroundConfig.source.code_first_spec_url) ||
      'assets/api/openapi-generated.yaml';

    var rawSpecUrl = strategy === 'code-first' ? codeFirstSpecUrl : apiFirstSpecUrl;
    var specUrl = resolveSpecUrl(rawSpecUrl);

    var tryItEnabled = parseBool(
      root.dataset.tryItEnabled !== undefined
        ? root.dataset.tryItEnabled
        : playgroundConfig.try_it_enabled,
      false
    );

    var tryItMode = (
      root.dataset.tryItMode ||
      playgroundConfig.try_it_mode ||
      'sandbox-only'
    ).toLowerCase();

    var sandboxBaseUrl =
      root.dataset.sandboxBaseUrl ||
      (playgroundConfig.endpoints && playgroundConfig.endpoints.sandbox_base_url) ||
      legacyConfig.sandbox_base_url ||
      '';

    var productionBaseUrl =
      root.dataset.productionBaseUrl ||
      (playgroundConfig.endpoints && playgroundConfig.endpoints.production_base_url) ||
      '';

    var selectedEndpointMode = tryItMode === 'mixed' ? 'sandbox-only' : tryItMode;

    function normalizeUrl(url, mode) {
      var targetBase = mode === 'real-api' ? productionBaseUrl : sandboxBaseUrl;
      if (!targetBase) {
        return url;
      }
      try {
        var parsedRequestUrl = new URL(url, window.location.origin);
        var parsedTargetUrl = new URL(targetBase, window.location.origin);
        parsedRequestUrl.protocol = parsedTargetUrl.protocol;
        parsedRequestUrl.hostname = parsedTargetUrl.hostname;
        parsedRequestUrl.port = parsedTargetUrl.port;
        return parsedRequestUrl.toString();
      } catch (error) {
        return url;
      }
    }

    function renderError(message) {
      root.innerHTML =
        '<p style="color:#c00"><strong>API playground failed to load:</strong> ' +
        message + '</p>';
    }

    // Endpoint switcher (mixed mode)
    if (tryItMode === 'mixed') {
      var wrapper = document.createElement('div');
      wrapper.style.marginBottom = '12px';
      var label = document.createElement('label');
      label.textContent = 'Request target:';
      label.style.marginRight = '8px';
      var select = document.createElement('select');
      select.id = 'api-playground-target-mode';
      var sandboxOption = document.createElement('option');
      sandboxOption.value = 'sandbox-only';
      sandboxOption.textContent = 'Sandbox';
      select.appendChild(sandboxOption);
      var realOption = document.createElement('option');
      realOption.value = 'real-api';
      realOption.textContent = 'Real API';
      select.appendChild(realOption);
      select.value = selectedEndpointMode;
      select.addEventListener('change', function () {
        selectedEndpointMode = select.value;
      });
      wrapper.appendChild(label);
      wrapper.appendChild(select);
      root.parentNode.insertBefore(wrapper, root);
    }

    // -- Redoc provider ---------------------------------------------------
    if (provider === 'redoc') {
      loadScript('https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js')
        .then(function () {
          if (!window.Redoc) {
            throw new Error('Redoc library is unavailable');
          }
          window.Redoc.init(
            specUrl,
            { hideDownloadButton: false, scrollYOffset: 80 },
            root
          );
        })
        .catch(function (error) {
          renderError(error.message);
        });
      return;
    }

    // -- Swagger UI provider (default) ------------------------------------
    loadCss('https://unpkg.com/swagger-ui-dist/swagger-ui.css');
    loadScript('https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js')
      .then(function () {
        if (!window.SwaggerUIBundle) {
          throw new Error('Swagger UI library is unavailable');
        }
        window.SwaggerUIBundle({
          url: specUrl,
          dom_id: '#api-playground-root',
          deepLinking: true,
          docExpansion: 'list',
          defaultModelsExpandDepth: 1,
          supportedSubmitMethods: tryItEnabled
            ? ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']
            : [],
          requestInterceptor: function (request) {
            request.url = normalizeUrl(request.url, selectedEndpointMode);
            return request;
          },
        });
      })
      .catch(function (error) {
        renderError(error.message);
      });
  }

  /* ------------------------------------------------------------------ */
  /*  Bootstrap: run on first load AND on MkDocs instant navigation      */
  /* ------------------------------------------------------------------ */

  // Initial run (covers full page loads and Docusaurus)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPlayground);
  } else {
    initPlayground();
  }

  // MkDocs Material instant loading fires a custom "DOMContentLoaded"
  // equivalent via location$.subscribe. The public hook is the
  // document$ observable, but we can also listen for these events:
  //   - 'DOMContentSwitch' (older Material versions)
  //   - location change via the Navigation API or popstate
  // The simplest universal approach: use a MutationObserver on <main>
  // or listen for the MkDocs Material content swap event.

  // MkDocs Material >=9.x emits a custom event when content is swapped:
  document.addEventListener('DOMContentSwitch', initPlayground);

  // For MkDocs Material that uses the subscription model, observe the
  // main content area for child replacement (instant navigation swaps
  // the <article> content).
  if (typeof MutationObserver !== 'undefined') {
    var observer = new MutationObserver(function () {
      var root = document.getElementById('api-playground-root');
      if (root && root.dataset.playgroundInit !== 'true') {
        initPlayground();
      }
    });

    function observeContent() {
      // MkDocs Material uses <article> or [data-md-component="content"]
      var target =
        document.querySelector('[data-md-component="content"]') ||
        document.querySelector('article') ||
        document.body;
      observer.observe(target, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', observeContent);
    } else {
      observeContent();
    }
  }
})();
