from __future__ import annotations

from collections import Counter
import math
from typing import Any, Callable

from .reliability import assess_reliability
from .scenarios import REQUIRED_FIELDS


def _safe_number(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) and 0 <= number <= 1 else 0.0


def _safe_sources(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        return 0
    return int(number)


def run_score_only_baseline(
    case: dict[str, Any],
    min_score: float = 0.80,
) -> dict[str, Any]:
    """Naive comparison policy: aggregate a score and ignore hard safety flags."""
    by_field: dict[str, dict[str, Any]] = {}
    for item in case["evidence"]:
        field = item.get("field")
        if field and field not in by_field:
            by_field[field] = item

    missing = [
        field for field in REQUIRED_FIELDS
        if not by_field.get(field, {}).get("present", False)
    ]
    confidences: list[float] = []
    corroboration: list[float] = []

    for field in REQUIRED_FIELDS:
        item = by_field.get(field, {})
        if not item.get("present", False):
            continue
        confidences.append(_safe_number(item.get("confidence", 0.0)))
        sources = _safe_sources(item.get("source_count", 1))
        corroboration.append(1.0 if sources >= 2 else 0.5)

    completeness = (len(REQUIRED_FIELDS) - len(missing)) / len(REQUIRED_FIELDS)
    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    mean_corroboration = (
        sum(corroboration) / len(corroboration) if corroboration else 0.0
    )
    score = round(
        0.50 * completeness
        + 0.35 * mean_confidence
        + 0.15 * mean_corroboration,
        4,
    )
    safe = not missing and score >= min_score

    return {
        "policy": "score_only_baseline",
        "decision": "auto_decide" if safe else "human_review",
        "score": score,
        "reasons": [
            "Aggregate score meets threshold"
            if safe
            else "Aggregate score or completeness below threshold"
        ],
    }


def run_candidate(case: dict[str, Any]) -> dict[str, Any]:
    result = assess_reliability(
        evidence_items=case["evidence"],
        required_fields=REQUIRED_FIELDS,
        conflict_flags=case.get("flags", []),
    )
    return {
        "policy": "reliability_gate_candidate",
        "decision": "auto_decide" if result.safe_to_auto_decide else "human_review",
        "score": result.score,
        "reasons": result.reasons,
        "missing_fields": result.missing_fields,
        "conflict_flags": result.conflict_flags,
    }


def make_trace(case: dict[str, Any], outcome: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "step": "evidence_ingestion",
            "status": "ok",
            "items": len(case["evidence"]),
        },
        {
            "step": "quality_policy",
            "status": "ok",
            "policy": outcome["policy"],
            "score": outcome["score"],
        },
        {
            "step": "decision",
            "status": outcome["decision"],
            "reasons": outcome["reasons"],
        },
    ]


def serialize_case(case: dict[str, Any], outcome: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": case["id"],
        "category": case["category"],
        "expected": case["expected"],
        "predicted": outcome["decision"],
        "correct": case["expected"] == outcome["decision"],
        "score": outcome["score"],
        "reasons": outcome["reasons"],
        "trace": make_trace(case, outcome),
    }


def policy_report(
    cases: list[dict[str, Any]],
    runner: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    results = [serialize_case(case, runner(case)) for case in cases]
    total = len(results)
    expected_review = [row for row in results if row["expected"] == "human_review"]
    automated = [row for row in results if row["predicted"] == "auto_decide"]
    unsafe_auto = [
        row for row in results
        if row["expected"] == "human_review"
        and row["predicted"] == "auto_decide"
    ]

    correct = sum(row["correct"] for row in results)
    review_caught = sum(
        row["predicted"] == "human_review" for row in expected_review
    )

    return {
        "cases": total,
        "accuracy": round(correct / total, 4),
        "human_review_recall": round(review_caught / len(expected_review), 4),
        "automation_rate": round(len(automated) / total, 4),
        "unsafe_auto_decisions": len(unsafe_auto),
        "category_counts": dict(Counter(row["category"] for row in results)),
        "results": results,
    }
