# Snapshot Benchmark v0

This directory contains the first more realistic snapshot-style benchmark seeds for EvidenceWeaver.

The goal is not to claim a finished benchmark. The goal is to move one step beyond a fully synthetic toy example and provide a **small, reproducible, domain-relevant task set** that a baseline agent can already run against.

## What is in here

- `tasks/agentic_rl_stability_task.json`
- `tasks/agent_training_stack_task.json`
- `tasks/deep_search_reward_task.json`

Each task is a `task-bundle.v0` artifact with:

- a research-style prompt
- a compact set of snapshot documents
- required claims for evaluation
- an explicit step budget

## Provenance model

These tasks use **paraphrased snapshot digests** anchored to primary sources such as:

- arXiv abstract pages
- official GitHub repositories

Why paraphrased digests instead of raw scraped pages?

- they keep the benchmark lightweight
- they avoid copying large web pages into the repo
- they make it easier to reason about what the agent actually saw

The tradeoff is realism: these are more realistic than a toy synthetic task, but less realistic than a full frozen-web snapshot benchmark.

## Current task themes

### 1. Stability in agentic RL

Asks the agent to explain why recent work treats stability as a first-class problem and to cite concrete failure modes or stabilization mechanisms.

Primary sources:

- `RAGEN-2` — https://arxiv.org/abs/2604.06268
- `ARLArena` — https://arxiv.org/abs/2602.21534
- `RAGEN` — https://arxiv.org/abs/2504.20073

### 2. Agent training stack comparison

Asks the agent to compare how `Agent Lightning`, `AgentRL`, and `rLLM` structure training pipelines.

Primary sources:

- `Agent Lightning` — https://arxiv.org/abs/2508.03680
- `AgentRL` — https://github.com/THUDM/AgentRL
- `rLLM` — https://github.com/rllm-org/rllm

### 3. Evidence-sensitive reward design for deep search

Asks the agent to explain why deep search agents need evidence-sensitive reward signals beyond outcome-only success.

Primary sources:

- `ASearcher / Beyond Ten Turns` — https://arxiv.org/abs/2508.07976
- `DeepDive` — https://github.com/THUDM/DeepDive
- `CaRR` — https://github.com/THUDM/CaRR

## How to run the baseline agent

```bash
PYTHONPATH=src python3 -m evidenceweaver.agent.baseline \
  benchmarks/snapshot_v0/tasks/agentic_rl_stability_task.json
```

Then evaluate the generated run:

```bash
PYTHONPATH=src python3 -m evidenceweaver.agent.baseline \
  benchmarks/snapshot_v0/tasks/agentic_rl_stability_task.json \
  --output /tmp/ew_run.json

PYTHONPATH=src python3 -m evidenceweaver.eval.offline \
  benchmarks/snapshot_v0/tasks/agentic_rl_stability_task.json \
  /tmp/ew_run.json
```

## Next benchmark steps

- replace some paraphrased digests with richer frozen-page snapshots
- add more heterogeneous task families
- attach provenance metadata and refresh scripts
- add held-out tasks for ablation and regression checks
