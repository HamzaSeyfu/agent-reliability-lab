from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable

CRITICAL_FLAGS = {
    "missing_coverage",
    "missing_policy",
    "missing_patient",
    "conflicting_identity",
    "conflicting_policy",
    "prompt_injection_detected",
}

DECISION_CRITICAL_FIELDS = {
    "diagnosis",
    "procedure_code",
    "coverage",
    "payer_policy",
}


@dataclass(frozen=True)
class ReliabilityAssessment:
    safe_to_auto_decide: bool
    score: float
    reasons: list[str]
    missing_fields: list[str]
    conflict_flags: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _bounded_confidence(value: object) -> tuple[float, bool]:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0, False
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        return 0.0, False
    return confidence, True


def _source_count(value: object) -> tuple[int, bool]:
    if isinstance(value, bool):
        return 0, False
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0, False
    if not math.isfinite(numeric) or numeric < 0 or not numeric.is_integer():
        return 0, False
    return int(numeric), True


def assess_reliability(
    *,
    evidence_items: Iterable[dict],
    required_fields: Iterable[str],
    conflict_flags: Iterable[str] = (),
    min_score: float = 0.80,
    min_field_confidence: float = 0.70,
) -> ReliabilityAssessment:
    """Fail closed when critical evidence is weak, conflicting or malformed."""
    evidence = list(evidence_items)
    required = list(dict.fromkeys(required_fields))
    flags = sorted(set(conflict_flags))

    min_score_value, min_score_valid = _bounded_confidence(min_score)
    min_field_value, min_field_valid = _bounded_confidence(min_field_confidence)
    invalid_configuration: list[str] = []
    if not min_score_valid:
        invalid_configuration.append("min_score")
    if not min_field_valid:
        invalid_configuration.append("min_field_confidence")

    items_by_field: dict[str, list[dict]] = {}
    for item in evidence:
        field = item.get("field")
        if field:
            items_by_field.setdefault(field, []).append(item)

    duplicate_fields = sorted(
        field for field in required if len(items_by_field.get(field, [])) > 1
    )
    by_field = {field: items[0] for field, items in items_by_field.items()}
    missing = [
        field for field in required
        if not by_field.get(field, {}).get("present", False)
    ]

    confidence_values: list[float] = []
    corroboration_values: list[float] = []
    low_confidence_fields: list[str] = []
    malformed_fields: list[str] = []

    for field in required:
        item = by_field.get(field, {})
        if not item.get("present", False):
            continue

        confidence, confidence_valid = _bounded_confidence(item.get("confidence", 0.0))
        source_count, source_valid = _source_count(item.get("source_count", 1))
        if not confidence_valid or not source_valid:
            malformed_fields.append(field)

        confidence_values.append(confidence)
        if confidence < min_field_value:
            low_confidence_fields.append(field)
        corroboration_values.append(1.0 if source_count >= 2 else 0.5)

    completeness = (
        1.0 if not required else (len(required) - len(missing)) / len(required)
    )
    mean_confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values else 0.0
    )
    mean_corroboration = (
        sum(corroboration_values) / len(corroboration_values)
        if corroboration_values else 0.0
    )
    score = round(
        0.50 * completeness
        + 0.35 * mean_confidence
        + 0.15 * mean_corroboration,
        4,
    )

    reasons: list[str] = []
    critical_missing = sorted(set(missing) & DECISION_CRITICAL_FIELDS)
    critical_flags = sorted(set(flags) & CRITICAL_FLAGS)
    malformed_fields = sorted(set(malformed_fields))

    if invalid_configuration:
        reasons.append(
            "Invalid reliability configuration: " + ", ".join(invalid_configuration)
        )
    if critical_missing:
        reasons.append("Critical evidence missing: " + ", ".join(critical_missing))
    if critical_flags:
        reasons.append("Critical reliability flags: " + ", ".join(critical_flags))
    if duplicate_fields:
        reasons.append("Ambiguous duplicate evidence: " + ", ".join(duplicate_fields))
    if malformed_fields:
        reasons.append("Malformed reliability evidence: " + ", ".join(malformed_fields))
    if low_confidence_fields:
        reasons.append(
            "Low-confidence critical evidence: "
            + ", ".join(sorted(low_confidence_fields))
        )
    if min_score_valid and score < min_score_value:
        reasons.append(
            f"Reliability score {score:.2f} is below threshold {min_score_value:.2f}"
        )

    safe = (
        not invalid_configuration
        and not critical_missing
        and not critical_flags
        and not duplicate_fields
        and not malformed_fields
        and not low_confidence_fields
        and score >= min_score_value
    )

    if safe:
        reasons.append("Evidence quality is sufficient for automated decisioning")

    return ReliabilityAssessment(
        safe_to_auto_decide=safe,
        score=score,
        reasons=reasons,
        missing_fields=missing,
        conflict_flags=flags,
    )
