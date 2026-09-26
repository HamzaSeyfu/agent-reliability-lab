# Agent Reliability Lab

**Production-style evaluation and regression testing for AI-assisted decision systems.**

Agent Reliability Lab asks a practical question:

> When should an AI-assisted workflow be allowed to continue automatically, and when must it stop and ask for human review?

The project compares a naive **score-only baseline** with a deterministic **reliability gate** across clean and adversarial synthetic cases. It combines a reproducible Python benchmark, Promptfoo evaluations, CI quality gates, audit traces, and a recruiter-friendly static dashboard.

## Current benchmark

| Metric | Score-only baseline | Reliability gate |
|---|---:|---:|
| Scenarios | 44 | 44 |
| Decision accuracy | 54.55% | **100%** |
| Human-review recall | 28.57% | **100%** |
| Automation rate | 81.82% | 36.36% |
| Unsafe automatic decisions | **20** | **0** |

These are **synthetic software-evaluation results**, not clinical performance claims.

## What the benchmark attacks

- missing decision-critical evidence;
- conflicting payer/patient information;
- prompt-injection signals;
- low-confidence critical extraction;
- malformed confidence values;
- ambiguous duplicate evidence;
- clean high-confidence and single-source cases.

A high aggregate score is not treated as permission to ignore a hard safety failure.

## Stack

**Python · Promptfoo · Pytest · GitHub Actions · HTML/CSS/JavaScript · Vercel-ready static demo**

## Quick start

```bash
python scripts/run_benchmark.py
python scripts/run_benchmark.py --check
pytest -q
```

Promptfoo:

```bash
npx promptfoo@latest eval -c promptfooconfig.yaml
```

Static dashboard:

```bash
python scripts/run_benchmark.py --write dashboard/results.json
cd dashboard
python -m http.server 8080
```

Then open `http://localhost:8080`.

## Architecture

```text
Synthetic scenarios
       │
       ├──────────────► score-only baseline
       │
       └──────────────► reliability-gate candidate
                               │
                               ▼
                         audit trace JSON
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              Promptfoo eval        Python benchmark
                    │                     │
                    └──────────┬──────────┘
                               ▼
                        CI quality gate
                               │
                               ▼
                         static dashboard
```

## Companion open-source work

This lab grew out of a reliability/human-review contribution I built in my fork of AWS Samples' healthcare agents:

- Contribution PR: https://github.com/HamzaSeyfu/sample-healthcare-agents/pull/1
- Public fork: https://github.com/HamzaSeyfu/sample-healthcare-agents
- Live reliability-gate demo: https://prior-auth-reliability-demo.vercel.app/

Agent Reliability Lab is deliberately a **separate, reusable evaluation project**, rather than presenting the AWS sample codebase as my own work.

## Roadmap

- [x] Standalone deterministic reliability engine
- [x] 44-case adversarial A/B benchmark
- [x] Promptfoo custom Python provider
- [x] Custom decision assertion
- [x] CI regression gate
- [x] Static dashboard
- [ ] Public Vercel deployment
- [ ] Recorded end-to-end agent traces
- [ ] Tool-call success and citation-support metrics
- [ ] OpenTelemetry spans
- [ ] Optional OpenLIT trace visualization

## Scope

Synthetic data only. This repository is an AI software-engineering and evaluation demonstration, not clinical decision support, regulatory validation, or a production healthcare system.

## License

MIT.
