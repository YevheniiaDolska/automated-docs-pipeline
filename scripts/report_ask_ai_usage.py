#!/usr/bin/env python3
"""Summarize Ask AI usage logs into an analytics report and doc-gap signals.

Reads the JSONL usage log written by the Ask AI runtime
(reports/ask_ai_usage.jsonl by default) and produces:

1. A summary report (JSON): volume, top questions, zero-citation questions,
   feedback statistics, and doc-gap candidates.
2. Optionally, a CSV in the Algolia search-analytics shape (query,count,results)
   so unanswered assistant questions flow into the existing gap detector via
   its --algolia-csv input -- no new plumbing.

Usage:
  python3 scripts/report_ask_ai_usage.py \
    --usage-log reports/ask_ai_usage.jsonl \
    --report reports/ask_ai_usage_report.json \
    --gaps-csv reports/ask_ai_gaps.csv --since-days 7
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _parse_ts(raw: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def load_events(path: Path, since_days: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days) if since_days > 0 else None
    events: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if cutoff is not None:
            ts = _parse_ts(str(event.get("ts", "")))
            if ts is not None and ts < cutoff:
                continue
        events.append(event)
    return events


def _normalize_question(text: str) -> str:
    return " ".join(str(text).lower().split())[:300]


def _event_day(event: dict[str, Any]) -> str:
    ts = _parse_ts(str(event.get("ts", "")))
    return ts.date().isoformat() if ts else "unknown"


def build_report(events: list[dict[str, Any]], since_days: int) -> dict[str, Any]:
    questions = [e for e in events if e.get("type") == "question"]
    feedback = [e for e in events if e.get("type") == "feedback"]

    question_counts: Counter[str] = Counter()
    zero_citation_counts: Counter[str] = Counter()
    citations_by_question: dict[str, int] = {}
    module_hits: Counter[str] = Counter()
    answered_questions = 0
    # Per-day buckets for the volume and coverage trend charts.
    daily_questions: Counter[str] = Counter()
    daily_zero_citation: Counter[str] = Counter()
    for event in questions:
        day = _event_day(event)
        daily_questions[day] += 1
        for module_id in event.get("retrieved_ids", []) or []:
            if str(module_id).strip():
                module_hits[str(module_id)] += 1
        norm = _normalize_question(str(event.get("question", "")))
        if not norm:
            continue
        question_counts[norm] += 1
        citations = int(event.get("citations_count", 0) or 0)
        citations_by_question[norm] = max(citations_by_question.get(norm, 0), citations)
        if citations == 0:
            zero_citation_counts[norm] += 1
            daily_zero_citation[day] += 1
        else:
            answered_questions += 1

    helpful = sum(1 for e in feedback if bool(e.get("helpful")))
    unhelpful = len(feedback) - helpful
    unhelpful_ids = {str(e.get("question_id", "")) for e in feedback if not bool(e.get("helpful"))}
    daily_helpful: Counter[str] = Counter()
    daily_unhelpful: Counter[str] = Counter()
    for event in feedback:
        day = _event_day(event)
        if bool(event.get("helpful")):
            daily_helpful[day] += 1
        else:
            daily_unhelpful[day] += 1
    unhelpful_questions: Counter[str] = Counter()
    for event in questions:
        if str(event.get("question_id", "")) in unhelpful_ids:
            unhelpful_questions[_normalize_question(str(event.get("question", "")))] += 1

    # Doc-gap candidates: questions retrieval could not ground (no citations)
    # or that users explicitly marked unhelpful.
    gap_candidates = [
        {"question": q, "count": c, "reason": "no_citations"}
        for q, c in zero_citation_counts.most_common(50)
    ] + [
        {"question": q, "count": c, "reason": "marked_unhelpful"}
        for q, c in unhelpful_questions.most_common(50)
        if q not in zero_citation_counts
    ]

    zero_citation_total = sum(zero_citation_counts.values())
    all_days = sorted(
        d for d in set(daily_questions) | set(daily_helpful) | set(daily_unhelpful)
        if d != "unknown"
    )
    daily = [
        {
            "date": day,
            "questions": daily_questions.get(day, 0),
            "zero_citation": daily_zero_citation.get(day, 0),
            "helpful": daily_helpful.get(day, 0),
            "unhelpful": daily_unhelpful.get(day, 0),
        }
        for day in all_days
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "window_days": since_days,
        "totals": {
            "questions": len(questions),
            "unique_questions": len(question_counts),
            "answered_questions": answered_questions,
            "answer_rate": round(answered_questions / len(questions), 3) if questions else None,
            "feedback_events": len(feedback),
            "helpful": helpful,
            "unhelpful": unhelpful,
            "helpful_rate": round(helpful / len(feedback), 3) if feedback else None,
            "feedback_rate": round(len(feedback) / len(questions), 3) if questions else None,
            "zero_citation_questions": zero_citation_total,
            "zero_citation_rate": round(zero_citation_total / len(questions), 3) if questions else None,
        },
        "daily": daily,
        "top_questions": [
            {"question": q, "count": c, "max_citations": citations_by_question.get(q, 0)}
            for q, c in question_counts.most_common(25)
        ],
        "top_retrieved_modules": [
            {"id": mid, "count": c} for mid, c in module_hits.most_common(15)
        ],
        "doc_gap_candidates": gap_candidates,
    }


def write_gaps_csv(report: dict[str, Any], path: Path) -> int:
    """Write gap candidates in the Algolia analytics CSV shape.

    Columns query,count,results match scripts/gap_detection/algolia_parser.py,
    so the file feeds the gap detector via --algolia-csv unchanged. Candidates
    are emitted with results=0 (treated as searches with no answer).
    """
    rows = report.get("doc_gap_candidates", [])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["query", "count", "results"])
        for row in rows:
            writer.writerow([row["question"], row["count"], 0])
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Ask AI usage into analytics + doc-gap signals")
    parser.add_argument("--usage-log", default="reports/ask_ai_usage.jsonl")
    parser.add_argument("--report", default="reports/ask_ai_usage_report.json")
    parser.add_argument("--gaps-csv", default="", help="Optional Algolia-shaped CSV for gap_detector --algolia-csv")
    parser.add_argument("--since-days", type=int, default=7, help="0 = all history")
    args = parser.parse_args()

    events = load_events(Path(args.usage_log), args.since_days)
    report = build_report(events, args.since_days)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    totals = report["totals"]
    print(
        f"[ask-ai-usage] questions={totals['questions']} unique={totals['unique_questions']} "
        f"zero-citation={totals['zero_citation_questions']} "
        f"helpful-rate={totals['helpful_rate'] if totals['helpful_rate'] is not None else 'n/a'}"
    )
    print(f"[ask-ai-usage] report: {report_path}")

    if str(args.gaps_csv).strip():
        gap_count = write_gaps_csv(report, Path(args.gaps_csv))
        print(f"[ask-ai-usage] gap candidates CSV ({gap_count} rows): {args.gaps_csv}")
        print("[ask-ai-usage] feed into gap detection with: python3 scripts/gap_detector.py --algolia-csv " + str(args.gaps_csv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
