"""Cross-document consistency and evidence-integrity guards for the audit engine.

These tests lock two structural guarantees so the class of defects found in the
Chainlink report cannot silently return:

1. The executive PDF and the sales teardown never disagree on shared facts
   (example count / reliability, and the example finding's label), because both
   read those facts from one source of truth.
2. Every contradiction or code-hygiene finding ships a quote that literally
   contains the value it claims -- an owner can always confirm it on the page.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import generate_audit_scorecard as scorecard
from scripts import generate_executive_audit_pdf as pdf
from scripts import generate_public_docs_audit as audit


def _single_site_audit(reliability: float = 86.86, count: int = 5622) -> dict:
    """A realistic single-site audit payload (aggregate omits the example count,
    exactly as the shipped Chainlink payload did)."""
    return {
        "site_url": "https://docs.example.com/",
        "sites": [
            {
                "site_url": "https://docs.example.com/",
                "metrics": {
                    "crawl": {"pages_crawled": 1676, "crawl_coverage_pct": 100.0},
                    "links": {"confirmed_broken_links_count": 7, "unverified_links_count": 1},
                    "api_coverage": {"reference_coverage_pct": 33.33, "coverage_determined": True},
                    "examples": {
                        "total_code_examples": count,
                        "example_reliability_estimate_pct": reliability,
                    },
                    "freshness": {"last_updated_coverage_pct": 22.08},
                    "retrieval_readiness": {"answerability_pct": 42.3},
                },
            }
        ],
        "aggregate": {
            "metrics": {
                # Aggregate deliberately omits total_code_examples to exercise the
                # per-site fallback (this is what made the PDF say "no examples").
                "examples": {"example_reliability_estimate_pct": reliability},
                "freshness": {"last_updated_coverage_pct": 22.08},
            }
        },
    }


def _minimal_kpis(reliability: float = 86.86) -> dict:
    """KPI dict with every field _build_findings reads; measured evidence present
    so the seven real findings are produced (no 'report missing' placeholders)."""
    return {
        "api_coverage": {"undocumented_pct": 66.67},
        "example_reliability": {"example_reliability_pct": reliability, "report_found": True},
        "freshness": {"stale_docs_pct": 65.55, "dated_docs": 1},
        "drift": {"docs_contract_drift_pct": 5.7, "docs_contract_report_found": True},
        "layer_completeness": {"features_missing_required_layers_pct": 0.0},
        "terminology": {"terminology_violation_pct": 0.5, "forbidden_terms_count": 0},
        "retrieval_quality": {"report_found": True, "hallucination_rate": 0.1},
    }


# ---------------------------------------------------------------------------
# Guard 2: PDF <-> teardown consistency
# ---------------------------------------------------------------------------


def test_pdf_reports_examples_when_measured_via_per_site_fallback():
    """The PDF must never claim 'no code examples' while a reliability estimate
    exists. The count is recovered from per-site metrics when the aggregate omits it."""
    total, reliability = pdf._example_coverage(_single_site_audit())
    assert total == 5622
    assert reliability == 86.86


def test_pdf_only_says_no_examples_when_truly_absent():
    empty = {"sites": [{"metrics": {"examples": {}}}], "aggregate": {"metrics": {"examples": {}}}}
    total, reliability = pdf._example_coverage(empty)
    assert total == 0
    assert reliability == 0


def test_reliability_is_single_source_across_documents():
    """The reliability shown by the PDF equals the reliability the teardown uses:
    both derive from the same audit field, so the two documents cannot disagree."""
    audit_payload = _single_site_audit(reliability=86.86)
    _, pdf_reliability = pdf._example_coverage(audit_payload)
    teardown_reliability = scorecard._extract_public_audit_metrics(audit_payload)["example_reliability_pct"]
    assert pdf_reliability == teardown_reliability == 86.86


def test_examples_finding_is_labeled_as_non_runnable_share():
    """The teardown example finding must name the value it shows. Labeling the
    non-runnable share (100 - reliability) as 'Example reliability %' made the
    evidence read '13% reliability' next to '86.9% reliability' -- the exact
    contradiction this test forbids from returning."""
    findings = scorecard._build_findings(_minimal_kpis(86.86), scorecard.CostAssumptions())
    examples = next(f for f in findings if f["id"] == "F-EXAMPLES-RELIABILITY")
    assert examples["metric"] == "Non-runnable examples %"
    assert "reliability" not in examples["metric"].lower()
    assert examples["current_value"] == 13.14  # 100 - 86.86
    assert examples["unit"] == "%"
    # The teardown renders the evidence as "{metric}: {current} -> {target} {unit}".
    evidence = f"{examples['metric']}: {examples['current_value']} -> {examples['target_value']} {examples['unit']}"
    assert evidence == "Non-runnable examples %: 13.14 -> 5.0 %"


# ---------------------------------------------------------------------------
# Guard 1: evidence-integrity invariant
# ---------------------------------------------------------------------------


def test_quote_supports_value_positive_and_reformatted():
    assert audit._quote_supports_value('curl -H "Authorization: Token abc" https://x', "Authorization: Token")
    # Reformatting is tolerated: display "Node 20" is backed by "Node.js v20".
    assert audit._quote_supports_value("You need Node.js v20 or higher.", "Node 20")


def test_quote_supports_value_rejects_unbacked_quote():
    # The Chainlink failure: a page-intro quote that never contains the auth header.
    assert not audit._quote_supports_value(
        "The Chainlink Cross-Chain Interoperability Protocol is a secure protocol.",
        "Authorization: Token",
    )
    assert not audit._quote_supports_value("", "TODO")


def _page(url: str, text: str = "", code_blocks=None):
    return SimpleNamespace(url=url, text=text, code_blocks=code_blocks or [])


def test_genuine_contradiction_survives_and_every_quote_backs_its_value():
    pages = [
        _page("https://docs.example.com/a", text='Send header Authorization: Bearer <token> to authenticate.'),
        _page("https://docs.example.com/b", text='Use Authorization: Token <key> for the legacy endpoint.'),
    ]
    result = audit._cross_page_contradictions(pages)
    assert result["contradictions_count"] == 1
    # The invariant: every shipped quote literally backs its claimed value.
    for contradiction in result["contradictions"]:
        for ev in contradiction["evidence"]:
            assert audit._quote_supports_value(ev["quote"], ev["value"])


def test_financial_annualized_matches_teardown_source():
    """The PDF's base annualized headline equals the teardown's annualized figure:
    both are the base scenario's total_signal_usd x 12. Low/high scale x0.7/x1.4."""
    scenarios = {
        "conservative": {"total_signal_usd": 8769.6},
        "base": {"total_signal_usd": 12528.0},
        "aggressive": {"total_signal_usd": 17539.2},
    }
    low, base, high = pdf._scenario_monthly_signals(scenarios)
    assert (low, base, high) == (8769.6, 12528.0, 17539.2)
    # PDF base annualized == what the teardown annualizes from the same field.
    teardown_annual = round(scenarios["base"]["total_signal_usd"] * 12.0, 2)
    assert round(base * 12.0, 2) == teardown_annual == 150336.0


def test_financial_scenarios_fall_back_to_documented_multipliers():
    low, base, high = pdf._scenario_monthly_signals({"base": {"total_signal_usd": 10000.0}})
    assert base == 10000.0
    assert low == 7000.0   # x0.7
    assert high == 14000.0  # x1.4


def _broken_link_payload(provenance_refs):
    return {
        "verifiable_contradictions": [],
        "verifiable_defects": [],
        "sites": [
            {
                "metrics": {
                    "links": {
                        "_broken_link_provenance": {
                            "https://docs.example.com/dead": provenance_refs
                        }
                    }
                },
                "samples": {"docs_broken_link_samples": ["https://docs.example.com/dead"]},
            }
        ],
    }


def test_broken_link_verify_item_names_source_and_anchor():
    """A broken-link 'verify in 30s' item must show the referring doc and the exact
    anchor text, so the owner can open that page and fix the link immediately."""
    audit_payload = _broken_link_payload(
        [
            {
                "source_page": "https://docs.example.com/guide",
                "anchor_text": "Best Practices",
                "anchor_label": "Best Practices",
                "context": "",
                "locator_quality": "unique",
            }
        ]
    )
    items = scorecard._sales_verify_in_30s(audit_payload, {})
    broken = [it for it in items if it["kind"] == "broken_link"]
    assert len(broken) == 1
    refs = broken[0]["refs"]
    # First ref is the dead target; a later ref names the source page + anchor text.
    assert refs[0]["url"] == "https://docs.example.com/dead"
    source_refs = [r for r in refs if r.get("quote")]
    assert source_refs and source_refs[0]["url"] == "https://docs.example.com/guide"
    assert source_refs[0]["quote"] == "Best Practices"


def test_broken_link_never_quotes_an_ambiguous_anchor_as_a_locator():
    """Regression: docs.chain.link/builders-quick-links labels 89 different links
    "CCIP", the first of which works. Reporting 'linked as: CCIP' sent the reader to
    a working link, so a true finding looked like a false positive. An anchor label
    that does not resolve to one target must never be presented as a search target.

    Naming the row in the label is necessary but not sufficient: the quote slot
    renders as a code block and reads as "search for this", so an ambiguous label
    must stay out of it even when a row disambiguates the prose.
    """
    audit_payload = _broken_link_payload(
        [
            {
                "source_page": "https://docs.example.com/quick-links",
                "anchor_text": "CCIP",
                "anchor_label": "CCIP",
                "context": "Robinhood Chain",
                "locator_quality": "ambiguous",
            }
        ]
    )
    items = scorecard._sales_verify_in_30s(audit_payload, {})
    ref = [r for r in items[0]["refs"] if r.get("quote")][0]
    # The disambiguating row must appear, so the reader finds the right link.
    assert "Robinhood Chain" in ref["label"]
    # The column name may be named as navigation, but never as the search key.
    assert ref["quote"] == "/dead"
    assert "not the link text" in ref["label"]


def test_broken_link_prose_context_is_not_offered_as_a_locator():
    """Regression: the CCIP best-practices link's context was the 20-word sentence
    that preceded it, so the teardown told the reader to "find" a mid-clause prose
    fragment. Context only locates when it is a short row/card label; otherwise the
    ref must degrade to the exact target path.
    """
    prose = (
        ": Learn about the Cross-Chain Token (CCT) standard that enables secure "
        "token transfers across different blockchains."
    )
    audit_payload = _broken_link_payload(
        [
            {
                "source_page": "https://docs.example.com/concepts",
                "anchor_text": "Best Practices",
                "anchor_label": "Best Practices",
                "context": prose,
                "locator_quality": "ambiguous",
            }
        ]
    )
    items = scorecard._sales_verify_in_30s(audit_payload, {})
    ref = [r for r in items[0]["refs"] if r.get("quote")][0]
    assert "Cross-Chain Token" not in ref["label"]
    assert ref["quote"] == "/dead"


def test_usable_context_keeps_label_shaped_strings_only():
    assert scorecard._usable_context("Robinhood Chain") == "Robinhood Chain"
    assert scorecard._usable_context('  "Node.js"  ').strip('"') == "Node.js"
    assert scorecard._usable_context(": Learn about the CCT standard.") == ""
    assert scorecard._usable_context("word " * 12) == ""


def test_broken_link_with_ambiguous_anchor_and_no_context_matches_on_target():
    """With no context to disambiguate, fall back to the target path -- always exact --
    rather than quoting a label that resolves to several links."""
    audit_payload = _broken_link_payload(
        [
            {
                "source_page": "https://docs.example.com/quick-links",
                "anchor_text": "CCIP",
                "anchor_label": "CCIP",
                "context": "",
                "locator_quality": "ambiguous",
            }
        ]
    )
    items = scorecard._sales_verify_in_30s(audit_payload, {})
    ref = [r for r in items[0]["refs"] if r.get("quote")][0]
    assert ref["quote"] == "/dead"
    assert "not the link text" in ref["label"]


def test_broken_link_icon_only_link_is_not_quoted_as_visible_text():
    """An accessible name from <img alt> is not visible on the page: quoting it sends
    the reader looking for text that is not there."""
    audit_payload = _broken_link_payload(
        [
            {
                "source_page": "https://docs.example.com/quick-links",
                "anchor_text": "",
                "anchor_label": "Supported",
                "context": "Robinhood Chain",
                "locator_quality": "ambiguous",
            }
        ]
    )
    items = scorecard._sales_verify_in_30s(audit_payload, {})
    ref = [r for r in items[0]["refs"] if r.get("quote")][0]
    assert ref["quote"] == "/dead"
    assert "Supported" not in ref["label"]
    assert "icon-only" in ref["label"] and "Robinhood Chain" in ref["label"]


def test_broken_link_does_not_cite_the_same_page_twice():
    """Two anchors on one page is one piece of evidence, not two."""
    audit_payload = _broken_link_payload(
        [
            {
                "source_page": "https://docs.example.com/quick-links",
                "anchor_text": "",
                "anchor_label": "Supported",
                "context": "Robinhood Chain",
                "locator_quality": "ambiguous",
            },
            {
                "source_page": "https://docs.example.com/quick-links",
                "anchor_text": "CCIP",
                "anchor_label": "CCIP",
                "context": "Robinhood Chain",
                "locator_quality": "ambiguous",
            },
        ]
    )
    items = scorecard._sales_verify_in_30s(audit_payload, {})
    source_refs = [r for r in items[0]["refs"] if r.get("quote")]
    assert len(source_refs) == 1


def test_assumptions_auto_discovered_next_to_client_audit(tmp_path):
    """The cost model uses the client's LLM-generated assumptions
    (company_assumptions.autofill.json) co-located with the audit, not the generic
    default -- so the signal is client-derived and deterministic."""
    audit_dir = tmp_path / "acme"
    audit_dir.mkdir()
    audit_path = audit_dir / "public_docs_audit.json"
    audit_path.write_text("{}", encoding="utf-8")
    autofill = audit_dir / "company_assumptions.autofill.json"
    autofill.write_text("{}", encoding="utf-8")

    resolved = scorecard._resolve_assumptions_path("", audit_path, tmp_path)
    assert resolved == autofill

    # Explicit path always wins.
    assert scorecard._resolve_assumptions_path("x/y.json", audit_path, tmp_path) == Path("x/y.json")

    # No public audit -> built-in defaults (never auto-pick a client file).
    assert scorecard._resolve_assumptions_path("", None, tmp_path) is None


def test_context_todo_is_not_flagged_but_real_marker_is():
    clean = [_page("https://docs.example.com/go", code_blocks=[
        {"code": "client, err := rpc.DialOptions(context.TODO(), url, opts)"}])]
    assert audit._code_hygiene_defects(clean)["defects_count"] == 0

    leftover = [_page("https://docs.example.com/js", code_blocks=[
        {"code": "// TODO: replace the hardcoded key before shipping\nconst k = 1;"}])]
    result = audit._code_hygiene_defects(leftover)
    assert result["defects_count"] == 1
    ev = result["defects"][0]["evidence"][0]
    assert audit._quote_supports_value(ev["quote"], ev["value"])


# Every block below is shaped after a real quicknode.com guide that the engine flagged
# as a leftover marker. Each is a skeleton the guide hands the reader to fill in, so
# each is a finding the owner refutes in one click -- the exact failure that makes a
# true report read as a broken bot.
@pytest.mark.parametrize(
    "case,code",
    [
        ("empty-brace-body",
         "class ArbBot {\n  constructor(config: ArbBotConfig) {\n    // TODO\n  }\n}"),
        ("marker-plus-trivial-return",
         "pub fn init_token(ctx: Context<InitToken>) -> Result<()> {\n"
         "    // TODO Add init mint logic\n    Ok(())\n}"),
        ("several-markers-one-stub",
         "pub fn initialize(ctx: Context<Initialize>) -> Result<()> {\n"
         "    // TODO initialize switch\n    // TODO initialize thread\n    Ok(())\n}"),
        ("python-stub", "def handle_event(event):\n    # TODO\n    pass\n"),
    ],
)
def test_reader_placeholder_in_stub_body_is_not_a_defect(case, code):
    pages = [_page("https://www.quicknode.com/guides/" + case, code_blocks=[{"code": code}])]
    result = audit._code_hygiene_defects(pages)
    assert result["defects_count"] == 0
    assert result["reader_placeholders_skipped"] >= 1


def test_second_person_marker_is_a_placeholder_even_amid_real_code():
    pages = [_page("https://www.quicknode.com/guides/bot", code_blocks=[{"code":
        "async init() {\n  this.connection = new Connection(RPC_URL);\n"
        "  // TODO: implement your own trading strategy here\n}"}])]
    assert audit._code_hygiene_defects(pages)["defects_count"] == 0


def test_marker_is_a_placeholder_when_a_later_block_shows_the_same_fn_completed():
    pages = [_page("https://www.quicknode.com/guides/transfer", code_blocks=[
        {"code": "fn transfer(ctx: Context<Transfer>) -> Result<()> {\n"
                 "    let a = ctx.accounts.from;\n    // TODO\n    Ok(())\n}"},
        {"code": "fn transfer(ctx: Context<Transfer>) -> Result<()> {\n"
                 "    let a = ctx.accounts.from;\n    token::transfer(cpi, amount)?;\n    Ok(())\n}"},
    ])]
    assert audit._code_hygiene_defects(pages)["defects_count"] == 0


@pytest.mark.parametrize(
    "case,code",
    [
        # Working body, author-facing note, no completed twin: still the leftover the
        # detector exists to catch. Suppressing these would empty it out.
        ("todo-amid-working-code",
         "async function send(tx) {\n  const sig = await conn.sendTransaction(tx);\n"
         "  // TODO: fix the retry loop, it double-sends\n"
         "  await conn.confirmTransaction(sig);\n  return sig;\n}"),
        ("fixme-amid-working-code",
         'func Dial(u string) (*Client, error) {\n  c, err := rpc.Dial(u)\n'
         '  if err != nil { return nil, err }\n'
         '  // FIXME: leaks the connection on retry\n  return &Client{c}, nil\n}'),
    ],
)
def test_leftover_marker_in_a_working_body_is_still_a_defect(case, code):
    pages = [_page("https://docs.example.com/" + case, code_blocks=[{"code": code}])]
    result = audit._code_hygiene_defects(pages)
    assert result["defects_count"] == 1
    ev = result["defects"][0]["evidence"][0]
    assert audit._quote_supports_value(ev["quote"], ev["value"])


def test_placeholder_earlier_in_a_block_does_not_mask_a_later_leftover():
    """The scan is per-marker, not per-block: a stub must not shield the block."""
    pages = [_page("https://docs.example.com/mixed", code_blocks=[{"code":
        "fn setup(ctx: Context<Setup>) -> Result<()> {\n    // TODO\n    Ok(())\n}\n\n"
        "fn run(ctx: Context<Run>) -> Result<()> {\n    let a = load(ctx)?;\n"
        "    // TODO: this races with the scheduler, fix before release\n"
        "    execute(a)?;\n    Ok(())\n}"}])]
    result = audit._code_hygiene_defects(pages)
    assert result["defects_count"] == 1
    assert result["reader_placeholders_skipped"] == 1
    assert "races" in result["defects"][0]["evidence"][0]["quote"]
