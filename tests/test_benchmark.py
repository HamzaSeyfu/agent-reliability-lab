from agent_reliability_lab.evaluate import (
    policy_report,
    run_candidate,
    run_score_only_baseline,
)
from agent_reliability_lab.scenarios import build_benchmark_cases


def test_benchmark_is_nontrivial():
    cases = build_benchmark_cases()
    assert len(cases) == 44
    categories = {case["category"] for case in cases}
    assert {
        "clean",
        "missing_evidence",
        "critical_flag",
        "low_confidence",
        "malformed",
        "ambiguous",
    } <= categories


def test_candidate_has_zero_unsafe_automation():
    report = policy_report(build_benchmark_cases(), run_candidate)
    assert report["unsafe_auto_decisions"] == 0
    assert report["human_review_recall"] == 1.0
    assert report["accuracy"] == 1.0


def test_candidate_outperforms_score_only_baseline():
    cases = build_benchmark_cases()
    baseline = policy_report(cases, run_score_only_baseline)
    candidate = policy_report(cases, run_candidate)
    assert candidate["accuracy"] > baseline["accuracy"]
    assert candidate["unsafe_auto_decisions"] < baseline["unsafe_auto_decisions"]
