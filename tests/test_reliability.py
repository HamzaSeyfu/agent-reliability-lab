from agent_reliability_lab.reliability import assess_reliability
from agent_reliability_lab.scenarios import REQUIRED_FIELDS, base_evidence


def test_clean_evidence_can_automate():
    result = assess_reliability(
        evidence_items=base_evidence(),
        required_fields=REQUIRED_FIELDS,
    )
    assert result.safe_to_auto_decide is True


def test_prompt_injection_forces_review_despite_high_score():
    result = assess_reliability(
        evidence_items=base_evidence(0.99, 3),
        required_fields=REQUIRED_FIELDS,
        conflict_flags=["prompt_injection_detected"],
    )
    assert result.safe_to_auto_decide is False
    assert result.score > 0.95


def test_duplicate_critical_evidence_fails_closed():
    evidence = base_evidence()
    evidence.append({
        "field": "coverage",
        "present": True,
        "confidence": 0.99,
        "source_count": 2,
    })
    result = assess_reliability(
        evidence_items=evidence,
        required_fields=REQUIRED_FIELDS,
    )
    assert result.safe_to_auto_decide is False
    assert any("duplicate" in reason.lower() for reason in result.reasons)
