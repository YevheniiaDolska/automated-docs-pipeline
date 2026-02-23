#!/usr/bin/env python3
"""
GUI Configurator Generator

Generates a self-contained HTML file that lets users configure the
Auto-Doc Pipeline through a browser-based wizard. Same pattern as
generate_kpi_wall.py -> wow-dashboard.html.

Reads at generation time:
- policy_packs/*.yml
- docs/_variables.yml
- docs-schema.yml

Embeds everything as inline JSON so the HTML has zero external dependencies.

Usage:
    python3 scripts/generate_configurator.py
    python3 scripts/generate_configurator.py --output reports/pipeline-configurator.html
    python3 scripts/generate_configurator.py --serve  # optional local HTTP server
"""

from __future__ import annotations

import argparse
import http.server
import json
import threading
import webbrowser
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_policy_packs(packs_dir: Path) -> dict:
    """Load all policy packs keyed by name."""
    packs = {}
    if not packs_dir.exists():
        return packs
    for yf in sorted(packs_dir.glob("*.yml")):
        data = _load_yaml(yf)
        name = data.get("name", yf.stem)
        packs[name] = data
    return packs


def load_variables(variables_path: Path) -> dict:
    return _load_yaml(variables_path)


def load_schema(schema_path: Path) -> dict:
    return _load_yaml(schema_path)


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def generate_html(policy_packs: dict, variables: dict, schema: dict) -> str:
    """Generate the self-contained configurator HTML."""

    packs_json = json.dumps(policy_packs, indent=2, ensure_ascii=False)
    vars_json = json.dumps(variables, indent=2, ensure_ascii=False)
    schema_json = json.dumps(schema, indent=2, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Auto-Doc Pipeline Configurator</title>
<style>
/* ------------------------------------------------------------------ */
/* Reset & base                                                        */
/* ------------------------------------------------------------------ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:      #0f172a;
  --surface: #1e293b;
  --card:    #334155;
  --border:  #475569;
  --text:    #e2e8f0;
  --muted:   #94a3b8;
  --accent:  #a78bfa;
  --accent2: #7c3aed;
  --green:   #10b981;
  --yellow:  #f59e0b;
  --red:     #ef4444;
  --blue:    #3b82f6;
  --radius:  8px;
}}

body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}}

/* ------------------------------------------------------------------ */
/* Layout                                                              */
/* ------------------------------------------------------------------ */
.container {{
  max-width: 960px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}}

h1 {{
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: var(--accent);
}}

.subtitle {{
  color: var(--muted);
  margin-bottom: 2rem;
}}

/* ------------------------------------------------------------------ */
/* Stepper                                                             */
/* ------------------------------------------------------------------ */
.stepper {{
  display: flex;
  gap: 0.25rem;
  margin-bottom: 2rem;
  overflow-x: auto;
}}

.step-indicator {{
  flex: 1;
  min-width: 100px;
  text-align: center;
  padding: 0.5rem 0.25rem;
  font-size: 0.75rem;
  border-bottom: 3px solid var(--border);
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}}

.step-indicator.active {{
  border-color: var(--accent);
  color: var(--text);
  font-weight: 600;
}}

.step-indicator.done {{
  border-color: var(--green);
  color: var(--green);
}}

/* ------------------------------------------------------------------ */
/* Step panels                                                         */
/* ------------------------------------------------------------------ */
.step-panel {{
  display: none;
  animation: fadeIn 0.3s ease;
}}

.step-panel.active {{
  display: block;
}}

@keyframes fadeIn {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

/* ------------------------------------------------------------------ */
/* Cards                                                               */
/* ------------------------------------------------------------------ */
.cards {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}}

.card {{
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}}

.card:hover {{
  border-color: var(--accent);
}}

.card.selected {{
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.3);
}}

.card h3 {{
  font-size: 1rem;
  margin-bottom: 0.5rem;
}}

.card p {{
  font-size: 0.85rem;
  color: var(--muted);
}}

.card .thresholds {{
  margin-top: 0.75rem;
  font-size: 0.8rem;
  color: var(--muted);
}}

.card .thresholds span {{
  display: inline-block;
  background: var(--card);
  padding: 2px 8px;
  border-radius: 4px;
  margin: 2px 4px 2px 0;
}}

/* ------------------------------------------------------------------ */
/* Form fields                                                         */
/* ------------------------------------------------------------------ */
.form-group {{
  margin-bottom: 1rem;
}}

.form-group label {{
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}}

.form-group .hint {{
  font-size: 0.75rem;
  color: var(--muted);
  margin-bottom: 0.25rem;
}}

input[type="text"], input[type="number"], input[type="url"], input[type="email"],
select, textarea {{
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  font-size: 0.9rem;
  font-family: inherit;
}}

input:focus, select:focus, textarea:focus {{
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.2);
}}

textarea {{
  min-height: 120px;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 0.8rem;
  resize: vertical;
}}

.form-row {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}}

/* ------------------------------------------------------------------ */
/* Radio cards (generator choice)                                      */
/* ------------------------------------------------------------------ */
.radio-cards {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.5rem;
}}

.radio-card {{
  background: var(--surface);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  cursor: pointer;
  transition: border-color 0.2s;
  text-align: center;
}}

.radio-card:hover {{ border-color: var(--accent); }}
.radio-card.selected {{
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.3);
}}

.radio-card h3 {{ font-size: 1.1rem; margin-bottom: 0.5rem; }}
.radio-card ul {{
  text-align: left;
  font-size: 0.8rem;
  color: var(--muted);
  margin-top: 0.75rem;
  padding-left: 1.25rem;
}}

/* ------------------------------------------------------------------ */
/* Sliders                                                             */
/* ------------------------------------------------------------------ */
.slider-group {{
  margin-bottom: 1.25rem;
}}

.slider-group label {{
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}}

.slider-group label .value {{
  color: var(--accent);
  font-family: monospace;
}}

input[type="range"] {{
  width: 100%;
  accent-color: var(--accent);
  cursor: pointer;
}}

/* ------------------------------------------------------------------ */
/* Preview                                                             */
/* ------------------------------------------------------------------ */
.preview-tabs {{
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}}

.preview-tab {{
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}}

.preview-tab.active {{
  background: var(--accent2);
  border-color: var(--accent2);
  color: #fff;
}}

.preview-code {{
  background: #0d1117;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
  color: #c9d1d9;
}}

/* ------------------------------------------------------------------ */
/* Export buttons                                                       */
/* ------------------------------------------------------------------ */
.export-section {{
  margin-top: 1.5rem;
}}

.btn {{
  display: inline-block;
  padding: 0.6rem 1.5rem;
  border: none;
  border-radius: var(--radius);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.1s;
  text-decoration: none;
}}

.btn:active {{ transform: scale(0.98); }}

.btn-primary {{
  background: var(--accent2);
  color: #fff;
}}

.btn-primary:hover {{ background: var(--accent); }}

.btn-secondary {{
  background: var(--card);
  color: var(--text);
  border: 1px solid var(--border);
}}

.btn-secondary:hover {{ background: var(--border); }}

.btn-group {{
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 1rem;
}}

/* ------------------------------------------------------------------ */
/* Navigation buttons                                                  */
/* ------------------------------------------------------------------ */
.nav-buttons {{
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}}

/* ------------------------------------------------------------------ */
/* Comparison table                                                    */
/* ------------------------------------------------------------------ */
.compare-table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  font-size: 0.85rem;
}}

.compare-table th, .compare-table td {{
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
}}

.compare-table th {{
  color: var(--muted);
  font-weight: 600;
}}

.check {{ color: var(--green); }}
.cross {{ color: var(--red); }}
</style>
</head>
<body>

<div class="container">
  <h1>Auto-Doc Pipeline Configurator</h1>
  <p class="subtitle">Configure your documentation pipeline in 6 steps</p>

  <!-- Stepper -->
  <div class="stepper">
    <div class="step-indicator active" data-step="0">1. Policy Pack</div>
    <div class="step-indicator" data-step="1">2. Variables</div>
    <div class="step-indicator" data-step="2">3. Generator</div>
    <div class="step-indicator" data-step="3">4. KPI Thresholds</div>
    <div class="step-indicator" data-step="4">5. Preview</div>
    <div class="step-indicator" data-step="5">6. Export</div>
  </div>

  <!-- Step 1: Policy Pack -->
  <div class="step-panel active" id="step-0">
    <h2>Choose a policy pack</h2>
    <p style="color:var(--muted);margin-bottom:1rem;">Policy packs define quality thresholds, contract rules, and drift detection patterns.</p>
    <div class="cards" id="policy-cards"></div>
  </div>

  <!-- Step 2: Product Variables -->
  <div class="step-panel" id="step-1">
    <h2>Product variables</h2>
    <p style="color:var(--muted);margin-bottom:1rem;">These values are used across all generated documentation.</p>
    <div class="form-row">
      <div class="form-group">
        <label>Product name</label>
        <input type="text" id="var-product_name" placeholder="Acme API">
      </div>
      <div class="form-group">
        <label>Company name</label>
        <input type="text" id="var-company_name" placeholder="Acme Corp">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Documentation URL</label>
        <input type="url" id="var-docs_url" placeholder="https://docs.example.com">
      </div>
      <div class="form-group">
        <label>Cloud / SaaS URL</label>
        <input type="url" id="var-cloud_url" placeholder="https://app.example.com">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>GitHub URL</label>
        <input type="url" id="var-github_url" placeholder="https://github.com/org/repo">
      </div>
      <div class="form-group">
        <label>Support email</label>
        <input type="email" id="var-support_email" placeholder="support@example.com">
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Current version</label>
        <input type="text" id="var-current_version" placeholder="1.0.0">
      </div>
      <div class="form-group">
        <label>Default port</label>
        <input type="number" id="var-default_port" placeholder="8080">
      </div>
    </div>
  </div>

  <!-- Step 3: Generator -->
  <div class="step-panel" id="step-2">
    <h2>Site generator</h2>
    <p style="color:var(--muted);margin-bottom:1rem;">Choose which static site generator to use for building documentation.</p>
    <div class="radio-cards">
      <div class="radio-card selected" data-gen="mkdocs">
        <h3>MkDocs Material</h3>
        <p style="color:var(--muted);font-size:0.85rem;">Python-based, feature-rich, widely adopted</p>
        <ul>
          <li>Built-in search</li>
          <li>Admonitions, tabs, Mermaid</li>
          <li>YAML configuration</li>
          <li>mkdocs-macros for variables</li>
        </ul>
      </div>
      <div class="radio-card" data-gen="docusaurus">
        <h3>Docusaurus</h3>
        <p style="color:var(--muted);font-size:0.85rem;">React-based, MDX support, versioning</p>
        <ul>
          <li>MDX components</li>
          <li>Doc versioning built-in</li>
          <li>JS/React ecosystem</li>
          <li>Algolia search integration</li>
        </ul>
      </div>
    </div>
    <table class="compare-table">
      <thead>
        <tr><th>Feature</th><th>MkDocs Material</th><th>Docusaurus</th></tr>
      </thead>
      <tbody>
        <tr><td>Language</td><td>Python</td><td>Node.js / React</td></tr>
        <tr><td>Config format</td><td>YAML</td><td>JavaScript</td></tr>
        <tr><td>Variables</td><td class="check">mkdocs-macros</td><td class="check">Preprocessor</td></tr>
        <tr><td>Admonitions</td><td class="check">!!!</td><td class="check">:::</td></tr>
        <tr><td>Tabs</td><td class="check">=== syntax</td><td class="check">MDX Tabs</td></tr>
        <tr><td>Doc versioning</td><td class="cross">Plugin needed</td><td class="check">Built-in</td></tr>
        <tr><td>MDX support</td><td class="cross">No</td><td class="check">Native</td></tr>
        <tr><td>Theme ecosystem</td><td class="check">Large</td><td class="check">Large</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Step 4: KPI Thresholds -->
  <div class="step-panel" id="step-3">
    <h2>KPI thresholds</h2>
    <p style="color:var(--muted);margin-bottom:1rem;">Adjust quality thresholds. Pre-filled from your selected policy pack.</p>
    <div class="slider-group">
      <label>Minimum quality score <span class="value" id="val-min_quality_score">80</span></label>
      <input type="range" id="kpi-min_quality_score" min="50" max="100" value="80">
    </div>
    <div class="slider-group">
      <label>Maximum stale docs (%) <span class="value" id="val-max_stale_pct">15</span></label>
      <input type="range" id="kpi-max_stale_pct" min="0" max="50" value="15">
    </div>
    <div class="slider-group">
      <label>Max high-priority gaps <span class="value" id="val-max_high_priority_gaps">8</span></label>
      <input type="range" id="kpi-max_high_priority_gaps" min="0" max="30" value="8">
    </div>
    <div class="slider-group">
      <label>Max quality score drop <span class="value" id="val-max_quality_score_drop">5</span></label>
      <input type="range" id="kpi-max_quality_score_drop" min="0" max="20" value="5">
    </div>
  </div>

  <!-- Step 5: Preview -->
  <div class="step-panel" id="step-4">
    <h2>Live preview</h2>
    <p style="color:var(--muted);margin-bottom:1rem;">Real-time preview of your configuration files.</p>
    <div class="preview-tabs">
      <button class="preview-tab active" data-preview="variables">_variables.yml</button>
      <button class="preview-tab" data-preview="policy">policy_pack.yml</button>
      <button class="preview-tab" data-preview="config">Site config</button>
    </div>
    <pre class="preview-code" id="preview-content"></pre>
  </div>

  <!-- Step 6: Export -->
  <div class="step-panel" id="step-5">
    <h2>Export configuration</h2>
    <p style="color:var(--muted);margin-bottom:1rem;">Download individual files or everything as a ZIP.</p>
    <div class="export-section">
      <p style="margin-bottom:0.75rem;">Download individual files:</p>
      <div class="btn-group">
        <button class="btn btn-secondary" onclick="downloadFile('variables')">_variables.yml</button>
        <button class="btn btn-secondary" onclick="downloadFile('policy')">policy_pack.yml</button>
        <button class="btn btn-secondary" onclick="downloadFile('config')">Site config</button>
      </div>
      <div class="btn-group" style="margin-top:1.5rem;">
        <button class="btn btn-primary" onclick="downloadZip()">Download All as ZIP</button>
      </div>
    </div>
  </div>

  <!-- Navigation -->
  <div class="nav-buttons">
    <button class="btn btn-secondary" id="btn-prev" onclick="navigate(-1)" style="visibility:hidden;">Previous</button>
    <button class="btn btn-primary" id="btn-next" onclick="navigate(1)">Next</button>
  </div>
</div>

<script>
// ====================================================================
// Embedded data (generated at build time)
// ====================================================================
const POLICY_PACKS = {packs_json};
const DEFAULT_VARIABLES = {vars_json};
const DOCS_SCHEMA = {schema_json};

// ====================================================================
// State
// ====================================================================
let currentStep = 0;
const totalSteps = 6;
let state = {{
  policyPack: Object.keys(POLICY_PACKS)[0] || 'minimal',
  generator: 'mkdocs',
  variables: JSON.parse(JSON.stringify(DEFAULT_VARIABLES)),
  kpi: {{ min_quality_score: 80, max_stale_pct: 15, max_high_priority_gaps: 8, max_quality_score_drop: 5 }},
}};

// ====================================================================
// Initialization
// ====================================================================
function init() {{
  renderPolicyCards();
  populateVariableFields();
  syncKpiFromPack();
  bindSliders();
  bindGeneratorCards();
  bindPreviewTabs();
  bindStepIndicators();
  updatePreview();
}}

// ====================================================================
// Policy pack cards
// ====================================================================
function renderPolicyCards() {{
  const container = document.getElementById('policy-cards');
  container.innerHTML = '';
  const descriptions = {{
    minimal: 'Core quality gates only. Fast onboarding with essential checks.',
    'api-first': 'Strict API documentation governance. Contract enforcement, drift detection.',
    monorepo: 'Multi-service repository support. Cross-service documentation tracking.',
    'multi-product': 'Multiple product lines with shared standards and independent thresholds.',
    plg: 'Product-led growth focus. Value-first documentation with interactive sandbox.',
  }};

  for (const [name, pack] of Object.entries(POLICY_PACKS)) {{
    const sla = pack.kpi_sla || {{}};
    const card = document.createElement('div');
    card.className = 'card' + (name === state.policyPack ? ' selected' : '');
    card.dataset.pack = name;
    card.innerHTML = `
      <h3>${{name}}</h3>
      <p>${{descriptions[name] || 'Policy pack for ' + name}}</p>
      <div class="thresholds">
        ${{sla.min_quality_score ? `<span>Score >= ${{sla.min_quality_score}}</span>` : ''}}
        ${{sla.max_stale_pct != null ? `<span>Stale <= ${{sla.max_stale_pct}}%</span>` : ''}}
        ${{sla.max_high_priority_gaps != null ? `<span>Gaps <= ${{sla.max_high_priority_gaps}}</span>` : ''}}
      </div>
    `;
    card.addEventListener('click', () => selectPack(name));
    container.appendChild(card);
  }}
}}

function selectPack(name) {{
  state.policyPack = name;
  document.querySelectorAll('#policy-cards .card').forEach(c => {{
    c.classList.toggle('selected', c.dataset.pack === name);
  }});
  syncKpiFromPack();
  updatePreview();
}}

// ====================================================================
// Variables
// ====================================================================
function populateVariableFields() {{
  const fields = ['product_name','company_name','docs_url','cloud_url','github_url','support_email','current_version','default_port'];
  for (const f of fields) {{
    const el = document.getElementById('var-' + f);
    if (el && state.variables[f] != null) {{
      el.value = state.variables[f];
    }}
    if (el) {{
      el.addEventListener('input', () => {{
        let val = el.value;
        if (el.type === 'number') val = parseInt(val) || 0;
        state.variables[f] = val;
        updatePreview();
      }});
    }}
  }}
}}

// ====================================================================
// Generator
// ====================================================================
function bindGeneratorCards() {{
  document.querySelectorAll('.radio-card[data-gen]').forEach(card => {{
    card.addEventListener('click', () => {{
      state.generator = card.dataset.gen;
      document.querySelectorAll('.radio-card[data-gen]').forEach(c => {{
        c.classList.toggle('selected', c.dataset.gen === state.generator);
      }});
      updatePreview();
    }});
  }});
}}

// ====================================================================
// KPI sliders
// ====================================================================
function syncKpiFromPack() {{
  const pack = POLICY_PACKS[state.policyPack] || {{}};
  const sla = pack.kpi_sla || {{}};
  state.kpi.min_quality_score = sla.min_quality_score || 80;
  state.kpi.max_stale_pct = sla.max_stale_pct || 15;
  state.kpi.max_high_priority_gaps = sla.max_high_priority_gaps || 8;
  state.kpi.max_quality_score_drop = sla.max_quality_score_drop || 5;

  for (const [key, val] of Object.entries(state.kpi)) {{
    const slider = document.getElementById('kpi-' + key);
    const display = document.getElementById('val-' + key);
    if (slider) slider.value = val;
    if (display) display.textContent = val;
  }}
}}

function bindSliders() {{
  for (const key of Object.keys(state.kpi)) {{
    const slider = document.getElementById('kpi-' + key);
    const display = document.getElementById('val-' + key);
    if (slider) {{
      slider.addEventListener('input', () => {{
        const v = parseFloat(slider.value);
        state.kpi[key] = v;
        if (display) display.textContent = v;
        updatePreview();
      }});
    }}
  }}
}}

// ====================================================================
// Preview
// ====================================================================
let activePreview = 'variables';

function bindPreviewTabs() {{
  document.querySelectorAll('.preview-tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
      activePreview = tab.dataset.preview;
      document.querySelectorAll('.preview-tab').forEach(t => t.classList.toggle('active', t.dataset.preview === activePreview));
      updatePreview();
    }});
  }});
}}

function updatePreview() {{
  const el = document.getElementById('preview-content');
  if (!el) return;

  if (activePreview === 'variables') {{
    el.textContent = generateVariablesYaml();
  }} else if (activePreview === 'policy') {{
    el.textContent = generatePolicyYaml();
  }} else if (activePreview === 'config') {{
    el.textContent = state.generator === 'mkdocs' ? generateMkdocsYaml() : generateDocusaurusConfig();
  }}
}}

function generateVariablesYaml() {{
  const v = state.variables;
  return `# Auto-Doc Pipeline - Product Variables
# Generated by Pipeline Configurator

product_name: "${{v.product_name || 'ProductName'}}"
product_full_name: "${{v.product_name || 'ProductName'}} platform"
company_name: "${{v.company_name || 'Your Company'}}"

current_version: "${{v.current_version || '1.0.0'}}"
api_version: "v1"

cloud_url: "${{v.cloud_url || 'https://app.example.com'}}"
docs_url: "${{v.docs_url || 'https://docs.example.com'}}"
github_url: "${{v.github_url || 'https://github.com/org/repo'}}"

support_email: "${{v.support_email || 'support@example.com'}}"

default_port: ${{v.default_port || 8080}}

env_vars:
  port: "${{(v.product_name || 'PRODUCT').toUpperCase().replace(/\\s+/g, '_')}}_PORT"
  webhook_url: "WEBHOOK_URL"
`;
}}

function generatePolicyYaml() {{
  const pack = POLICY_PACKS[state.policyPack] || {{}};
  const k = state.kpi;
  return `# Policy pack: ${{state.policyPack}}
# Customized via Pipeline Configurator

kpi_sla:
  min_quality_score: ${{k.min_quality_score}}
  max_stale_pct: ${{k.max_stale_pct}}.0
  max_high_priority_gaps: ${{k.max_high_priority_gaps}}
  max_quality_score_drop: ${{k.max_quality_score_drop}}

${{pack.docs_contract ? `docs_contract:
  interface_patterns:
${{(pack.docs_contract.interface_patterns || []).map(p => '    - "' + p + '"').join('\\n')}}
  doc_patterns:
${{(pack.docs_contract.doc_patterns || []).map(p => '    - "' + p + '"').join('\\n')}}` : ''}}

${{pack.drift ? `drift:
  openapi_patterns:
${{(pack.drift.openapi_patterns || []).map(p => '    - "' + p + '"').join('\\n')}}
  sdk_patterns:
${{(pack.drift.sdk_patterns || []).map(p => '    - "' + p + '"').join('\\n')}}
  reference_doc_patterns:
${{(pack.drift.reference_doc_patterns || []).map(p => '    - "' + p + '"').join('\\n')}}` : ''}}
`;
}}

function generateMkdocsYaml() {{
  const v = state.variables;
  const name = v.product_name || 'Documentation';
  return `site_name: "${{name}} Documentation"
site_url: "${{v.docs_url || 'https://docs.example.com'}}"

theme:
  name: material
  language: en
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest
    - content.tabs.link
    - content.code.copy

plugins:
  - search
  - tags
  - macros:
      include_yaml:
        - docs/_variables.yml

markdown_extensions:
  - admonition
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight
  - attr_list
  - tables
  - toc:
      permalink: true

nav:
  - Home: index.md
  - Getting Started:
    - getting-started/index.md
  - How-To Guides:
    - how-to/index.md
  - Concepts:
    - concepts/index.md
  - Reference:
    - reference/index.md
  - Troubleshooting:
    - troubleshooting/index.md
`;
}}

function generateDocusaurusConfig() {{
  const v = state.variables;
  const name = v.product_name || 'Documentation';
  const escaped = name.replace(/'/g, "\\\\'");
  return `// @ts-check
/** @type {{import('@docusaurus/types').Config}} */
const config = {{
  title: '${{escaped}}',
  url: '${{v.docs_url || 'https://docs.example.com'}}',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  presets: [
    [
      'classic',
      ({{
        docs: {{
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: '${{v.github_url || 'https://github.com/org/repo'}}/edit/main/',
        }},
        blog: false,
        theme: {{
          customCss: require.resolve('./src/css/custom.css'),
        }},
      }}),
    ],
  ],

  themeConfig: ({{
    navbar: {{
      title: '${{escaped}}',
      items: [
        {{ type: 'docSidebar', sidebarId: 'docs', position: 'left', label: 'Docs' }},
      ],
    }},
  }}),
}};

module.exports = config;
`;
}}

// ====================================================================
// Navigation
// ====================================================================
function navigate(direction) {{
  goToStep(currentStep + direction);
}}

function goToStep(step) {{
  if (step < 0 || step >= totalSteps) return;

  // Mark current as done if going forward
  const indicators = document.querySelectorAll('.step-indicator');
  if (step > currentStep) {{
    indicators[currentStep].classList.add('done');
    indicators[currentStep].classList.remove('active');
  }}

  currentStep = step;

  // Update panels
  document.querySelectorAll('.step-panel').forEach((panel, i) => {{
    panel.classList.toggle('active', i === currentStep);
  }});

  // Update indicators
  indicators.forEach((ind, i) => {{
    if (i === currentStep) {{
      ind.classList.add('active');
      ind.classList.remove('done');
    }} else if (i < currentStep) {{
      ind.classList.add('done');
      ind.classList.remove('active');
    }} else {{
      ind.classList.remove('active', 'done');
    }}
  }});

  // Nav buttons
  document.getElementById('btn-prev').style.visibility = currentStep === 0 ? 'hidden' : 'visible';
  const nextBtn = document.getElementById('btn-next');
  if (currentStep === totalSteps - 1) {{
    nextBtn.style.visibility = 'hidden';
  }} else {{
    nextBtn.style.visibility = 'visible';
    nextBtn.textContent = 'Next';
  }}

  updatePreview();
}}

function bindStepIndicators() {{
  document.querySelectorAll('.step-indicator').forEach(ind => {{
    ind.addEventListener('click', () => {{
      goToStep(parseInt(ind.dataset.step));
    }});
  }});
}}

// ====================================================================
// Export / download
// ====================================================================
function downloadText(filename, content) {{
  const blob = new Blob([content], {{ type: 'text/plain' }});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}}

function downloadFile(type) {{
  if (type === 'variables') {{
    downloadText('_variables.yml', generateVariablesYaml());
  }} else if (type === 'policy') {{
    downloadText(state.policyPack + '.yml', generatePolicyYaml());
  }} else if (type === 'config') {{
    if (state.generator === 'mkdocs') {{
      downloadText('mkdocs.yml', generateMkdocsYaml());
    }} else {{
      downloadText('docusaurus.config.js', generateDocusaurusConfig());
    }}
  }}
}}

function downloadZip() {{
  // Simple multi-file download without JSZip -- create files one by one
  downloadFile('variables');
  setTimeout(() => downloadFile('policy'), 200);
  setTimeout(() => downloadFile('config'), 400);
}}

// ====================================================================
// Boot
// ====================================================================
document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the Auto-Doc Pipeline GUI configurator"
    )
    parser.add_argument(
        "--output",
        default="reports/pipeline-configurator.html",
        help="Output HTML file (default: reports/pipeline-configurator.html)",
    )
    parser.add_argument(
        "--policy-packs-dir",
        default="policy_packs",
        help="Policy packs directory (default: policy_packs)",
    )
    parser.add_argument(
        "--variables",
        default="docs/_variables.yml",
        help="Variables file (default: docs/_variables.yml)",
    )
    parser.add_argument(
        "--schema",
        default="docs-schema.yml",
        help="Schema file (default: docs-schema.yml)",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start a local HTTP server and open in browser",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Port for --serve mode (default: 8765)",
    )

    args = parser.parse_args()

    # Load data
    packs = load_policy_packs(Path(args.policy_packs_dir))
    variables = load_variables(Path(args.variables))
    schema = load_schema(Path(args.schema))

    # Generate
    html = generate_html(packs, variables, schema)

    # Write
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(f"Generated: {output}")

    # Optional serve
    if args.serve:
        serve_dir = str(output.parent)
        filename = output.name

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *a, **kw):
                super().__init__(*a, directory=serve_dir, **kw)

        server = http.server.HTTPServer(("127.0.0.1", args.port), Handler)
        url = f"http://127.0.0.1:{args.port}/{filename}"
        print(f"Serving at {url}")

        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            server.server_close()


if __name__ == "__main__":
    main()
