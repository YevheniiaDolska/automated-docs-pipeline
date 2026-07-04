(function () {
  var script = document.currentScript;
  if (!script) return;

  var enabled = (script.dataset.enabled || "true").toLowerCase() === "true";
  if (!enabled) return;

  var endpoint = script.dataset.askAiEndpoint;
  var apiKey = script.dataset.askAiApiKey;
  var userId = script.dataset.userId || "anonymous";
  var userRole = script.dataset.userRole || "anonymous";
  var plan = script.dataset.plan || "free";
  var theme = (script.dataset.theme || "dark").toLowerCase() === "light" ? "light" : "dark";
  var title = script.dataset.title || "Ask AI";

  if (!endpoint || !apiKey) {
    console.warn("Ask AI widget is missing endpoint or API key data attributes.");
    return;
  }

  var feedbackEndpoint = endpoint.replace(/\/ask\/?$/, "/feedback");

  var colors = theme === "light"
    ? { bg: "#ffffff", fg: "#0f172a", border: "#cbd5e1", panel: "#f1f5f9", accent: "#2563eb", muted: "#64748b", code: "#e2e8f0" }
    : { bg: "#0f172a", fg: "#e2e8f0", border: "#334155", panel: "#111827", accent: "#2563eb", muted: "#94a3b8", code: "#1e293b" };

  function esc(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Minimal safe markdown: escape everything first, then re-introduce a small
  // whitelist of formatting. No raw HTML from the model ever reaches the DOM.
  function renderMarkdown(text) {
    var safe = esc(text);
    // fenced code blocks
    safe = safe.replace(/```([\s\S]*?)```/g, function (_m, code) {
      return '<pre style="background:' + colors.code + ';padding:8px;border-radius:6px;overflow:auto;font-size:12px;">' + code.replace(/^\n+|\n+$/g, "") + "</pre>";
    });
    // inline code
    safe = safe.replace(/`([^`\n]+)`/g, '<code style="background:' + colors.code + ';padding:1px 4px;border-radius:4px;font-size:12px;">$1</code>');
    // bold / italics
    safe = safe.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/(^|\s)\*([^*\n]+)\*/g, "$1<em>$2</em>");
    // markdown links [text](https://...)
    safe = safe.replace(/\[([^\]\n]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener" style="color:' + colors.accent + ';">$1</a>');
    // bullet lists
    safe = safe.replace(/(?:^|\n)[-*] (.+)/g, "\n&bull; $1");
    // paragraphs
    safe = safe.replace(/\n{2,}/g, "<br/><br/>").replace(/\n/g, "<br/>");
    return safe;
  }

  var container = document.createElement("div");
  container.style.cssText =
    "position:fixed;right:20px;bottom:20px;width:360px;max-height:70vh;display:flex;flex-direction:column;" +
    "background:" + colors.bg + ";color:" + colors.fg + ";border:1px solid " + colors.border + ";" +
    "border-radius:12px;padding:12px;font-family:ui-sans-serif,system-ui,-apple-system;z-index:9999;" +
    "box-shadow:0 8px 30px rgba(0,0,0,.25);font-size:14px;";
  container.innerHTML =
    '<div style="font-weight:700;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">' +
    '<span>' + esc(title) + '</span>' +
    '<button id="ask-ai-min" title="Minimize" style="background:none;border:none;color:' + colors.muted + ';cursor:pointer;font-size:16px;">&ndash;</button>' +
    "</div>" +
    '<div id="ask-ai-transcript" style="flex:1;overflow-y:auto;margin-bottom:8px;max-height:44vh;"></div>' +
    '<textarea id="ask-ai-input" rows="2" style="width:100%;box-sizing:border-box;margin-bottom:8px;background:' + colors.panel + ";color:" + colors.fg + ";border:1px solid " + colors.border + ';border-radius:6px;padding:8px;resize:vertical;font-family:inherit;font-size:13px;" placeholder="Ask a docs question..."></textarea>' +
    '<button id="ask-ai-send" style="width:100%;background:' + colors.accent + ';color:#fff;border:none;border-radius:6px;padding:9px;cursor:pointer;font-weight:600;">Send</button>';

  document.body.appendChild(container);

  var transcript = container.querySelector("#ask-ai-transcript");
  var input = container.querySelector("#ask-ai-input");
  var button = container.querySelector("#ask-ai-send");
  var minButton = container.querySelector("#ask-ai-min");
  var minimized = false;

  minButton.addEventListener("click", function () {
    minimized = !minimized;
    transcript.style.display = minimized ? "none" : "block";
    input.style.display = minimized ? "none" : "block";
    button.style.display = minimized ? "none" : "block";
    minButton.innerHTML = minimized ? "+" : "&ndash;";
  });

  function appendUserTurn(question) {
    var el = document.createElement("div");
    el.style.cssText = "margin:6px 0;padding:8px;border-radius:8px;background:" + colors.accent + "22;";
    el.innerHTML = '<div style="font-size:11px;color:' + colors.muted + ';margin-bottom:2px;">You</div>' + esc(question);
    transcript.appendChild(el);
    transcript.scrollTop = transcript.scrollHeight;
    return el;
  }

  function sendFeedback(questionId, helpful, statusEl) {
    fetch(feedbackEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Ask-AI-Key": apiKey },
      body: JSON.stringify({ question_id: questionId, helpful: helpful, comment: "" })
    })
      .then(function () { statusEl.textContent = "Thanks for the feedback!"; })
      .catch(function () { statusEl.textContent = "Could not send feedback."; });
  }

  function appendAnswerTurn(data) {
    var el = document.createElement("div");
    el.style.cssText = "margin:6px 0;padding:8px;border-radius:8px;background:" + colors.panel + ";";
    var html = '<div style="font-size:11px;color:' + colors.muted + ';margin-bottom:2px;">Assistant</div>';
    html += '<div style="line-height:1.45;">' + renderMarkdown(data.answer || "No answer.") + "</div>";

    var citations = Array.isArray(data.citations) ? data.citations.filter(function (c) { return c && (c.title || c.url); }) : [];
    if (citations.length) {
      html += '<div style="margin-top:8px;font-size:11px;color:' + colors.muted + ';">Sources</div><ul style="margin:4px 0 0 16px;padding:0;font-size:12px;">';
      var seen = {};
      citations.forEach(function (c) {
        var label = esc(c.title || c.source_file || c.id || "source");
        if (seen[label]) return;
        seen[label] = true;
        if (c.url) {
          html += '<li><a href="' + esc(c.url) + '" target="_blank" rel="noopener" style="color:' + colors.accent + ';">' + label + "</a></li>";
        } else {
          html += "<li>" + label + "</li>";
        }
      });
      html += "</ul>";
    }
    el.innerHTML = html;

    if (data.question_id) {
      var fb = document.createElement("div");
      fb.style.cssText = "margin-top:8px;font-size:12px;color:" + colors.muted + ";display:flex;gap:8px;align-items:center;";
      var up = document.createElement("button");
      var down = document.createElement("button");
      var status = document.createElement("span");
      [up, down].forEach(function (b) {
        b.style.cssText = "background:" + colors.code + ";border:1px solid " + colors.border + ";border-radius:6px;padding:2px 8px;cursor:pointer;color:" + colors.fg + ";font-size:12px;";
      });
      up.textContent = "👍";
      down.textContent = "👎";
      up.addEventListener("click", function () { sendFeedback(data.question_id, true, status); });
      down.addEventListener("click", function () { sendFeedback(data.question_id, false, status); });
      fb.appendChild(up);
      fb.appendChild(down);
      fb.appendChild(status);
      el.appendChild(fb);
    }

    transcript.appendChild(el);
    transcript.scrollTop = transcript.scrollHeight;
  }

  function appendNotice(text) {
    var el = document.createElement("div");
    el.style.cssText = "margin:6px 0;padding:8px;border-radius:8px;background:" + colors.panel + ";color:" + colors.muted + ";font-size:12px;";
    el.textContent = text;
    transcript.appendChild(el);
    transcript.scrollTop = transcript.scrollHeight;
    return el;
  }

  function submit() {
    var question = input.value.trim();
    if (!question) return;
    input.value = "";
    appendUserTurn(question);
    var pending = appendNotice("Thinking...");
    button.disabled = true;

    fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Ask-AI-Key": apiKey,
        "X-User-Id": userId,
        "X-User-Role": userRole,
        "X-User-Plan": plan
      },
      body: JSON.stringify({ question: question })
    })
      .then(function (resp) {
        if (!resp.ok) {
          return resp.json().then(
            function (err) { throw new Error(err.detail || ("HTTP " + resp.status)); },
            function () { throw new Error("HTTP " + resp.status); }
          );
        }
        return resp.json();
      })
      .then(function (data) {
        pending.remove();
        appendAnswerTurn(data);
      })
      .catch(function (err) {
        pending.textContent = "Error: " + err.message;
      })
      .then(function () {
        button.disabled = false;
        input.focus();
      });
  }

  button.addEventListener("click", submit);
  input.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      submit();
    }
  });
})();
