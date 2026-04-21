(function () {
  var script = document.currentScript;
  if (!script) return;

  var enabled = (script.dataset.enabled || "true").toLowerCase() === "true";
  if (!enabled) return;

  var endpoint = script.dataset.askAiEndpoint;
  var feedbackEndpoint = script.dataset.askAiFeedbackEndpoint;
  var apiKey = script.dataset.askAiApiKey;
  var userId = script.dataset.userId || "anonymous";
  var userRole = script.dataset.userRole || "anonymous";
  var plan = script.dataset.plan || "free";
  var lastExchange = null;

  if (!feedbackEndpoint && endpoint && endpoint.indexOf("/api/v1/ask") !== -1) {
    feedbackEndpoint = endpoint.replace("/api/v1/ask", "/api/v1/feedback");
  }

  if (!endpoint || !apiKey) {
    console.warn("Ask AI widget is missing endpoint or API key data attributes.");
    return;
  }

  var container = document.createElement("div");
  container.style.position = "fixed";
  container.style.right = "20px";
  container.style.bottom = "20px";
  container.style.width = "320px";
  container.style.background = "#0f172a";
  container.style.color = "#e2e8f0";
  container.style.border = "1px solid #334155";
  container.style.borderRadius = "10px";
  container.style.padding = "12px";
  container.style.fontFamily = "ui-sans-serif, system-ui, -apple-system";
  container.style.zIndex = "9999";
  container.innerHTML = ""
    + '<div style="font-weight:700;margin-bottom:8px;">Ask AI</div>'
    + '<textarea id="ask-ai-input" rows="3" style="width:100%;margin-bottom:8px;background:#111827;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:8px;" placeholder="Ask a docs question..."></textarea>'
    + '<button id="ask-ai-send" style="width:100%;background:#2563eb;color:#fff;border:none;border-radius:6px;padding:8px;cursor:pointer;">Send</button>'
    + '<pre id="ask-ai-output" style="margin-top:8px;white-space:pre-wrap;background:#111827;padding:8px;border-radius:6px;max-height:180px;overflow:auto;">Ready.</pre>'
    + '<div id="ask-ai-feedback-wrap" style="display:none;margin-top:8px;">'
    + '  <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">Was this answer helpful?</div>'
    + '  <div style="display:flex;gap:6px;">'
    + '    <button id="ask-ai-feedback-up" style="flex:1;background:#14532d;color:#dcfce7;border:1px solid #166534;border-radius:6px;padding:6px;cursor:pointer;">Helpful</button>'
    + '    <button id="ask-ai-feedback-down" style="flex:1;background:#7f1d1d;color:#fee2e2;border:1px solid #991b1b;border-radius:6px;padding:6px;cursor:pointer;">Not helpful</button>'
    + '  </div>'
    + '  <div id="ask-ai-feedback-status" style="font-size:12px;color:#94a3b8;margin-top:6px;"></div>'
    + '</div>';

  document.body.appendChild(container);

  var input = container.querySelector("#ask-ai-input");
  var button = container.querySelector("#ask-ai-send");
  var output = container.querySelector("#ask-ai-output");
  var feedbackWrap = container.querySelector("#ask-ai-feedback-wrap");
  var feedbackUp = container.querySelector("#ask-ai-feedback-up");
  var feedbackDown = container.querySelector("#ask-ai-feedback-down");
  var feedbackStatus = container.querySelector("#ask-ai-feedback-status");

  function setFeedbackVisible(visible) {
    if (!feedbackWrap) return;
    feedbackWrap.style.display = visible ? "block" : "none";
    if (visible && feedbackStatus) feedbackStatus.textContent = "";
  }

  function sendFeedback(helpful) {
    if (!feedbackEndpoint || !lastExchange) {
      if (feedbackStatus) feedbackStatus.textContent = "Feedback endpoint is not configured.";
      return;
    }
    if (feedbackStatus) feedbackStatus.textContent = "Saving feedback...";
    fetch(feedbackEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Ask-AI-Key": apiKey,
        "X-User-Id": userId,
        "X-User-Role": userRole,
        "X-User-Plan": plan
      },
      body: JSON.stringify({
        question: lastExchange.question,
        helpful: helpful,
        answer: lastExchange.answer,
        citations: lastExchange.citations || []
      })
    })
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) {
            throw new Error(data.detail || "Feedback request failed");
          }
          return data;
        });
      })
      .then(function () {
        if (feedbackStatus) feedbackStatus.textContent = "Thanks, feedback saved.";
      })
      .catch(function (err) {
        if (feedbackStatus) feedbackStatus.textContent = "Feedback error: " + err.message;
      });
  }

  button.addEventListener("click", function () {
    var question = input.value.trim();
    if (!question) {
      output.textContent = "Type a question first.";
      return;
    }

    output.textContent = "Thinking...";
    setFeedbackVisible(false);
    lastExchange = null;

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
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) {
            throw new Error(data.detail || "Request failed");
          }
          return data;
        });
      })
      .then(function (data) {
        var warnings = (data.warnings || []).map(function (w) {
          return "Warning: " + w;
        }).join("\n");
        var citations = (data.citations || []).map(function (c) {
          return "- " + (c.title || c.id || "source") + " (" + (c.source_file || "n/a") + ")";
        }).join("\n");
        var warningBlock = warnings ? warnings + "\n\n" : "";
        output.textContent = warningBlock + data.answer + (citations ? "\n\nSources:\n" + citations : "");
        lastExchange = {
          question: question,
          answer: data.answer || "",
          citations: data.citations || []
        };
        setFeedbackVisible(true);
      })
      .catch(function (err) {
        output.textContent = "Error: " + err.message;
        setFeedbackVisible(false);
      });
  });

  if (feedbackUp) {
    feedbackUp.addEventListener("click", function () {
      sendFeedback(true);
    });
  }
  if (feedbackDown) {
    feedbackDown.addEventListener("click", function () {
      sendFeedback(false);
    });
  }
})();
