"""Tests for llms.txt / llms-full.txt / llms-ctx generation from modules."""

from __future__ import annotations

from scripts import generate_llms_txt as mod


def _module(mid: str, *, url: str, title: str, priority: int, channels: list[str], intents: list[str], body: str = "") -> dict:
    return {
        "id": mid,
        "title": title,
        "summary": f"summary for {title}",
        "intents": intents,
        "channels": channels,
        "priority": priority,
        "status": "active",
        "metadata": {"url": url},
        "content": {"docs_markdown": body, "assistant_context": ""},
    }


def test_strip_badges() -> None:
    text = (
        "<!-- VERIDOC_POWERED_BADGE:START -->\n[![x](y)](z)\n<!-- VERIDOC_POWERED_BADGE:END -->\n\n## Real\n\nBody."
    )
    out = mod.strip_badges(text)
    assert "VERIDOC" not in out
    assert out.startswith("## Real")


def test_llms_txt_dedups_chunks_and_strips_part_suffix() -> None:
    modules = [
        _module("a-1", url="https://d/x/", title="Configure X", priority=60, channels=["docs"], intents=["configure"]),
        _module("a-2", url="https://d/x/", title="Configure X (Part 2)", priority=60, channels=["docs"], intents=["configure"]),
        _module("b-1", url="https://d/y/", title="Fix Y", priority=50, channels=["docs"], intents=["troubleshoot"]),
    ]
    out = mod.build_llms_txt(modules, product_name="P", tagline="tag", min_priority=1)
    assert out.count("https://d/x/") == 1          # chunk collapsed to one entry
    assert "(Part 2)" not in out                    # suffix stripped
    assert "## Configure" in out and "## Troubleshoot" in out


def test_llms_txt_respects_priority_and_channel() -> None:
    modules = [
        _module("low", url="https://d/a/", title="Low", priority=10, channels=["docs"], intents=["configure"]),
        _module("nodocs", url="https://d/b/", title="NoDocs", priority=90, channels=["assistant"], intents=["configure"]),
    ]
    out = mod.build_llms_txt(modules, product_name="P", tagline="", min_priority=30)
    assert "https://d/a/" not in out   # below priority threshold
    assert "https://d/b/" not in out   # not a docs-channel module


def test_llms_full_assistant_only_and_token_split() -> None:
    big = "word " * 500  # ~2500 chars ~= 625 tokens
    modules = [
        _module("m1", url="https://d/1/", title="One", priority=90, channels=["assistant"], intents=["configure"], body=big),
        _module("m2", url="https://d/2/", title="Two", priority=80, channels=["assistant"], intents=["configure"], body=big),
        _module("m3", url="https://d/3/", title="Three", priority=70, channels=["docs"], intents=["configure"], body=big),
    ]
    parts, manifest = mod.build_llms_full(
        modules, product_name="P", assistant_only=True, max_tokens_per_part=700, chars_per_token=4
    )
    # docs-only module excluded; two assistant modules split across parts by budget.
    ids = {e["id"] for e in manifest}
    assert ids == {"m1", "m2"}
    assert len(parts) >= 2
    assert all("tokens" in e and "part" in e for e in manifest)


def test_llms_full_orders_by_priority() -> None:
    modules = [
        _module("low", url="https://d/l/", title="Low", priority=10, channels=["assistant"], intents=["x"], body="a"),
        _module("high", url="https://d/h/", title="High", priority=99, channels=["assistant"], intents=["x"], body="b"),
    ]
    _parts, manifest = mod.build_llms_full(
        modules, product_name="P", assistant_only=True, max_tokens_per_part=100000, chars_per_token=4
    )
    assert [e["id"] for e in manifest] == ["high", "low"]
