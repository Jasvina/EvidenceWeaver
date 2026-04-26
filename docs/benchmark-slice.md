# Proposed Benchmark Slice

This document sketches the first benchmark slice EvidenceWeaver should target.

The point of the first slice is not to be comprehensive. The point is to be:

- realistic enough to matter
- narrow enough to reproduce
- structured enough to support evidence-centric evaluation

## Principles

The first benchmark slice should:

1. require multi-step information gathering
2. require synthesis rather than single-fact lookup
3. support citation-grounded answers
4. be stable enough to compare runs over time

## Recommended Starting Shape

The most practical starting point is a **snapshot-based deep research benchmark**:

- each task comes with a fixed query
- the environment exposes a bounded collection of pages or documents
- the agent must browse, read, and answer with citations
- evaluation scores both answer quality and citation quality

This is less glamorous than full live-web evaluation, but it is much easier to reproduce and debug.

## Why Snapshot-Based First

Live web evaluation is attractive, but it creates problems early:

- page content changes over time
- site availability adds noise
- retrieval can break for reasons unrelated to policy quality
- reward debugging becomes harder

A fixed-snapshot benchmark gives us a stable target while the training loop is still young.

## Candidate Task Types

The first slice should mix tasks like:

- compare two competing technical approaches
- synthesize a timeline from multiple sources
- answer a multi-hop factual question with explicit support
- identify contradictions across sources
- write a short research note with cited claims

## Minimal Evaluation Bundle

Each task should ideally include:

- prompt or query
- document or page bundle
- reference answer or rubric
- list of key claims expected in a strong answer
- citation expectations for those claims

## Current Repository Artifact

The repository now ships a tiny synthetic benchmark artifact that exercises the full `v0` path:

- task bundle: [`examples/tasks/synthetic_delay_task.json`](../examples/tasks/synthetic_delay_task.json)
- good run: [`examples/runs/synthetic_delay_good_run.json`](../examples/runs/synthetic_delay_good_run.json)
- weak run: [`examples/runs/synthetic_delay_weak_run.json`](../examples/runs/synthetic_delay_weak_run.json)
- schemas: [`schemas/task-bundle.v0.json`](../schemas/task-bundle.v0.json) and [`schemas/run-artifact.v0.json`](../schemas/run-artifact.v0.json)

This is intentionally small. It exists to make the interfaces, scoring assumptions, and test path concrete before the first real benchmark slice is locked down.

## First More Realistic Slice

The repository now also includes a first lightweight realistic slice under [`benchmarks/snapshot_v0/`](../benchmarks/snapshot_v0/README.md).

That slice is still small, but it is a real step up from the synthetic task because:

- the questions are research-style synthesis prompts rather than fabricated release-note summaries
- the documents are paraphrased digests anchored to real primary-source URLs
- the tasks already exercise comparison, stability analysis, and reward-design reasoning

Current seed tasks:

- `agentic_rl_stability_task`
- `agent_training_stack_task`
- `deep_search_reward_task`

This benchmark layer is meant to be the bridge between interface prototyping and a richer frozen-web benchmark.

The repository can already run the baseline closed loop on these tasks:

```bash
PYTHONPATH=src python3 -m evidenceweaver.agent.baseline \
  benchmarks/snapshot_v0/tasks/agent_training_stack_task.json \
  --output /tmp/evidenceweaver_run.json

PYTHONPATH=src python3 -m evidenceweaver.eval.offline \
  benchmarks/snapshot_v0/tasks/agent_training_stack_task.json \
  /tmp/evidenceweaver_run.json \
  --emit-scored-run /tmp/evidenceweaver_scored_run.json
```

The current baseline is no longer purely one-shot. On tasks with enough budget it can:

- search once
- build a partial evidence graph
- derive open questions from uncovered prompt-focus tokens
- issue a follow-up search query
- open an additional source
- produce a richer scored artifact

## Real-example-driven optimization stage

The repository has now entered a more serious tuning phase with [`benchmarks/real_cases_v1/`](../benchmarks/real_cases_v1/README.md).

This suite is different from `snapshot_v0` in purpose:

- `snapshot_v0` exists to prove the loop works
- `real_cases_v1` exists to compare candidate baseline configurations against a broader task set

The current sweep output is saved in:

- [`benchmarks/real_cases_v1/results/baseline_sweep.json`](../benchmarks/real_cases_v1/results/baseline_sweep.json)

The current signal from that sweep is:

- the best-performing baseline opens more documents on the first pass
- the current baseline is strong across all eight real-case tasks
- the best average `overall_score` on expanded `real_cases_v1` is now about `0.9724`
- after targeted tuning, all current real-case tasks score at least `0.95`
- the optimizer now emits failure summaries so the suite can drive the next optimization step directly

## Metrics

At minimum, the first benchmark slice should report:

- answer score
- citation precision
- citation coverage
- unsupported-claim rate
- source diversity
- tool budget

## What to Delay Until Later

The first benchmark does not need:

- full live-web browsing
- very large task counts
- multimodal browsing
- multi-agent collaboration
- learned reward models

Those can come later once the basic system is trustworthy.
