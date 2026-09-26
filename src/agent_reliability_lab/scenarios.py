from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = ["diagnosis", "procedure_code", "coverage", "payer_policy"]
CRITICAL_FLAGS = {
    "missing_coverage",
    "missing_policy",
    "missing_patient",
    "conflicting_identity",
    "conflicting_policy",
    "prompt_injection_detected",
}


def base_evidence(
    confidence: float = 0.96,
    source_count: int = 2,
) -> list[dict[str, Any]]:
    return [
        {
            "field": field,
            "present": True,
            "confidence": confidence,
            "source_count": source_count,
        }
        for field in REQUIRED_FIELDS
    ]


def build_benchmark_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    for index in range(12):
        cases.append({
            "id": f"clean_{index:02d}",
            "category": "clean",
            "expected": "auto_decide",
            "evidence": base_evidence(0.90 + (index % 5) * 0.015, 2),
            "flags": [],
        })

    for index in range(4):
        cases.append({
            "id": f"single_source_{index:02d}",
            "category": "clean",
            "expected": "auto_decide",
            "evidence": base_evidence(0.94 + index * 0.01, 1),
            "flags": [],
        })

    for field in REQUIRED_FIELDS:
        for variant in range(2):
            evidence = base_evidence(0.97, 2)
            for item in evidence:
                if item["field"] == field:
                    item.update(present=False, confidence=0.0, source_count=0)
            cases.append({
                "id": f"missing_{field}_{variant}",
                "category": "missing_evidence",
                "expected": "human_review",
                "evidence": evidence,
                "flags": [],
            })

    for flag in sorted(CRITICAL_FLAGS):
        cases.append({
            "id": f"flag_{flag}",
            "category": "critical_flag",
            "expected": "human_review",
            "evidence": base_evidence(0.99, 3),
            "flags": [flag],
        })

    for index, confidence in enumerate([0.10, 0.25, 0.40, 0.55, 0.61, 0.68]):
        evidence = base_evidence(0.97, 2)
        evidence[0]["confidence"] = confidence
        cases.append({
            "id": f"low_confidence_{index}",
            "category": "low_confidence",
            "expected": "human_review",
            "evidence": evidence,
            "flags": [],
        })

    for index, value in enumerate([float("nan"), 1.2, -0.1, "not-a-number"]):
        evidence = base_evidence(0.97, 2)
        evidence[1]["confidence"] = value
        cases.append({
            "id": f"malformed_confidence_{index}",
            "category": "malformed",
            "expected": "human_review",
            "evidence": evidence,
            "flags": [],
        })

    for index in range(4):
        evidence = base_evidence(0.97, 2)
        evidence.append({
            "field": "coverage",
            "present": True,
            "confidence": 0.98,
            "source_count": 2,
        })
        cases.append({
            "id": f"duplicate_evidence_{index}",
            "category": "ambiguous",
            "expected": "human_review",
            "evidence": evidence,
            "flags": [],
        })

    return cases
