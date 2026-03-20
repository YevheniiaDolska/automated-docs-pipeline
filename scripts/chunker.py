"""Token-aware text chunking for knowledge modules."""

from __future__ import annotations

from typing import Any

try:
    import tiktoken

    _HAS_TIKTOKEN = True
except ImportError:
    tiktoken = None  # type: ignore[assignment]
    _HAS_TIKTOKEN = False


def _get_encoder() -> Any:
    if not _HAS_TIKTOKEN:
        raise ImportError("tiktoken is required: pip install tiktoken>=0.7.0")
    return tiktoken.get_encoding("cl100k_base")


def _build_text(module: dict[str, Any]) -> str:
    parts = [
        str(module.get("title", "")),
        str(module.get("summary", "")),
        str(module.get("assistant_excerpt", "")),
        " ".join(str(v) for v in module.get("intents", [])),
    ]
    return " ".join(p for p in parts if p.strip())


def chunk_module(
    module: dict[str, Any],
    max_tokens: int = 750,
    overlap_tokens: int = 100,
) -> list[dict[str, Any]]:
    """Split a knowledge module into token-sized chunks.

    If the module text fits within *max_tokens*, a single chunk is returned
    (no splitting).  Otherwise the text is split on whitespace boundaries so
    that each chunk is at most *max_tokens* tokens long, with *overlap_tokens*
    tokens of overlap between consecutive chunks.

    Returns a list of chunk dicts with keys:
        chunk_id, parent_id, chunk_index, text, title, source_file
    """
    enc = _get_encoder()
    parent_id = str(module.get("id", "")).strip()
    title = str(module.get("title", ""))
    source_file = str(module.get("source_file", ""))
    text = _build_text(module)
    tokens = enc.encode(text)

    if len(tokens) <= max_tokens:
        return [
            {
                "chunk_id": parent_id,
                "parent_id": parent_id,
                "chunk_index": 0,
                "text": text,
                "title": title,
                "source_file": source_file,
            }
        ]

    step = max(max_tokens - overlap_tokens, 1)
    chunks: list[dict[str, Any]] = []
    idx = 0
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_text = enc.decode(tokens[start:end])
        chunks.append(
            {
                "chunk_id": f"{parent_id}__chunk_{idx}",
                "parent_id": parent_id,
                "chunk_index": idx,
                "text": chunk_text,
                "title": title,
                "source_file": source_file,
            }
        )
        idx += 1
        start += step
        if end >= len(tokens):
            break

    return chunks
