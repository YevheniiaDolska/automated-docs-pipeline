(function initApiPlayground() {
  var root = document.getElementById('api-playground-root');
  if (!root) {
    return;
  }

  function parseBool(value, fallback) {
    if (value === undefined || value === null || value === '') {
      return fallback;
    }
    return String(value).toLowerCase() === 'true';
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = resolve;
      script.onerror = function () {
        reject(new Error('Failed to load script: ' + src));
      };
      document.head.appendChild(script);
    });
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
    '/api/openapi.yaml';

  var codeFirstSpecUrl =
    root.dataset.codeFirstSpecUrl ||
    (playgroundConfig.source && playgroundConfig.source.code_first_spec_url) ||
    '/api/openapi-generated.yaml';

  var rawSpecUrl = strategy === 'code-first' ? codeFirstSpecUrl : apiFirstSpecUrl;

  // Resolve spec URL against site base path (handles GitHub Pages subdirectory deploys).
  // Absolute URLs (https://...) pass through unchanged.
  // Relative paths are resolved against the site root derived from <link rel="canonical">.
  var specUrl = (function resolveSpecUrl(raw) {
    if (/^https?:\/\//.test(raw)) {
      return raw;
    }
    // Derive site root from canonical link (MkDocs Material always emits one)
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
      try {
        var href = canonical.getAttribute('href');
        // Remove page-specific path segments to get site root
        // canonical example: https://host/base-path/reference/page-name/
        // site root: https://host/base-path/
        var siteRoot = href.replace(/[^/]*\/[^/]*\/?$/, '');
        var cleanRaw = raw.replace(/^\//, '');
        return siteRoot + cleanRaw;
      } catch (e) { /* fall through */ }
    }
    return raw;
  })(rawSpecUrl);

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
    var targetBase = '';
    if (mode === 'real-api') {
      targetBase = productionBaseUrl;
    } else {
      targetBase = sandboxBaseUrl;
    }

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
    root.innerHTML = '<p><strong>API playground failed to load:</strong> ' + message + '</p>';
  }

  function renderEndpointSwitcher() {
    if (tryItMode !== 'mixed') {
      return;
    }

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

  renderEndpointSwitcher();

  if (provider === 'redoc') {
    loadScript('https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js')
      .then(function () {
        if (!window.Redoc) {
          throw new Error('Redoc library is unavailable');
        }
        window.Redoc.init(
          specUrl,
          {
            hideDownloadButton: false,
            scrollYOffset: 80,
          },
          root
        );
      })
      .catch(function (error) {
        renderError(error.message);
      });
    return;
  }

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
})();
