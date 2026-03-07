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
    + '<pre id="ask-ai-output" style="margin-top:8px;white-space:pre-wrap;background:#111827;padding:8px;border-radius:6px;max-height:180px;overflow:auto;">Ready.</pre>';

  document.body.appendChild(container);

  var input = container.querySelector("#ask-ai-input");
  var button = container.querySelector("#ask-ai-send");
  var output = container.querySelector("#ask-ai-output");

  button.addEventListener("click", function () {
    var question = input.value.trim();
    if (!question) {
      output.textContent = "Type a question first.";
      return;
    }

    output.textContent = "Thinking...";

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
        var citations = (data.citations || []).map(function (c) {
          return "- " + (c.title || c.id || "source") + " (" + (c.source_file || "n/a") + ")";
        }).join("\n");
        output.textContent = data.answer + (citations ? "\n\nSources:\n" + citations : "");
      })
      .catch(function (err) {
        output.textContent = "Error: " + err.message;
      });
  });
})();
