# EvidenceWeaver Progress and Roadmap

Status date: 2026-04-21

This document records the current repository state, what has been implemented, what the latest real-case benchmark says, and how future optimization should proceed. It is intended for humans and future AI agents that need to understand the project without reading the full session history.

## Current Stage

EvidenceWeaver has moved from idea-stage documentation into a working pre-alpha research scaffold.

The current loop is:

```text
task bundle
  -> baseline agent
  -> evidence graph
  -> diagnostics
  -> reward bundle
  -> graph analysis
  -> optimizer sweep
```

The project is now in a **real-example-driven accuracy optimization** stage. The main work is no longer only building interfaces; it is using real public-source benchmark tasks to expose weaknesses, tune the baseline, and record the results.

## Implemented Components

### Documentation and research framing

- `README.md` presents the project thesis and quickstart.
- `docs/related-work.md` tracks the agentic RL landscape.
- `docs/research-agenda.md` records hypotheses and experiment stages.
- `docs/reward-design.md` explains the decomposed reward idea.
- `docs/benchmark-slice.md` describes benchmark design and current suites.
- `docs/interfaces.md` records the v0 interface contract.
- `paper/draft.md` is a pre-results working draft.
- `codex_work` is the chronological handoff log for future Codex/AI agents.

### Core code

- `src/evidenceweaver/models.py`
  - task bundles
  - run artifacts
  - provenance metadata
  - diagnostics
  - reward bundles
- `src/evidenceweaver/agent/baseline.py`
  - deterministic search-read-write baseline
  - graph-aware state
  - follow-up search on open questions
  - task-family-aware duplicate suppression
- `src/evidenceweaver/eval/offline.py`
  - offline evaluator
  - scored-run emission
- `src/evidenceweaver/graph/core.py`
  - source nodes
  - claim nodes
  - open questions
  - support and simple claim-to-claim edges
- `src/evidenceweaver/graph/analyze.py`
  - graph summary CLI
- `src/evidenceweaver/reward/compose.py`
  - reward composition module and CLI
- `src/evidenceweaver/optimize/accuracy.py`
  - real-case suite optimizer
  - candidate baseline sweeps
  - failure summaries

### Tests

The current test suite covers:

- task and run loading
- evaluator behavior
- baseline agent CLI
- graph-aware run artifacts
- reward module and reward CLI
- graph analysis CLI
- real-case optimizer CLI
- provenance coverage for real-case tasks

Latest verified test count: 18 tests.

## Current Benchmarks

### Synthetic example

Location:

- `examples/tasks/synthetic_delay_task.json`
- `examples/runs/`

Purpose:

- keeps schemas and evaluator behavior easy to debug
- not intended as a serious benchmark

### Snapshot v0

Location:

- `benchmarks/snapshot_v0/`

Purpose:

- first paraphrased-snapshot benchmark seed
- proves the core loop works on research-style tasks

Current task themes:

- agentic RL stability
- agent training stack comparison
- deep search reward design

### Real Cases v1

Location:

- `benchmarks/real_cases_v1/`

Purpose:

- current real-example-driven accuracy optimization suite
- uses paraphrased public-source snapshots with embedded provenance metadata
- drives baseline tuning and weakest-task analysis

Current task count: 8

Current tasks:

- `agent-training-stack-task`
- `agentic-rl-stability-task`
- `browser-agent-environment-task`
- `computer-use-rl-task`
- `deep-search-reward-task`
- `swe-agent-posttraining-task`
- `terminal-agent-rl-task`
- `tool-user-interaction-task`

## Latest Real-Case Results

Saved result:

- `benchmarks/real_cases_v1/results/baseline_sweep.json`

Latest best average `overall_score`: `0.9724`

Per-task scores under the current best config:

| Task | Overall score |
| --- | ---: |
| `agent-training-stack-task` | `1.0` |
| `agentic-rl-stability-task` | `0.95` |
| `browser-agent-environment-task` | `1.0` |
| `computer-use-rl-task` | `0.95` |
| `deep-search-reward-task` | `0.9667` |
| `swe-agent-posttraining-task` | `1.0` |
| `terminal-agent-rl-task` | `0.9625` |
| `tool-user-interaction-task` | `0.95` |

Current weakest scores are no longer catastrophic. The next meaningful progress should come from adding harder tasks and improving failure analysis rather than over-tuning the current eight examples.

## What Improved During This Stage

The real-case suite initially exposed several weak task families:

- SWE post-training was weak because the agent missed multi-sentence evidence about tool-augmented post-training.
- Computer-use was weak because duplicate short claims inflated unsupported-claim rate.
- Tool-agent-user tasks were weak because tau2-bench generalization sentences were selected before core tau-bench evidence.
- Browser-agent tasks were weak because the agent missed environment/API integration evidence.
- Terminal-agent tasks were weak because it missed task-dataset and execution-harness evidence.

Fixes applied:

- multi-sentence candidate generation
- richer signal fragments for task families
- task-family-aware duplicate suppression
- expanded real-case suite
- optimizer failure summaries
- provenance metadata on real-case tasks

## Current Known Limitations

- The real-case benchmark uses paraphrased digests, not full frozen web snapshots.
- The optimizer is deterministic and heuristic, not learned.
- Current scores are high on only eight tasks, so overfitting risk remains.
- The evaluator is keyword/citation based and should not be treated as a human-quality reward model.
- Graph relationships are still heuristic; `contradicts` is not yet implemented.
- There is no RL trainer integration yet.

## Recommended Next Optimization Steps

### 1. Expand harder real-case tasks

Add tasks from more domains before tuning further:

- multi-hop research QA
- scientific paper synthesis
- retrieval with conflicting sources
- safety/policy/tool-use tasks
- long-horizon browser workflows
- API-heavy customer-support agents
- multi-modal or GUI-adjacent tasks

Goal:

- prevent overfitting the current eight-task suite
- force the optimizer to reveal new weaknesses

### 2. Add source snapshot sidecars

Move beyond paraphrased digests by adding source sidecars:

```text
benchmarks/real_cases_v1/sources/<task_id>/
  source_manifest.json
  source_*.md
```

Goal:

- preserve richer source context
- make provenance auditable
- prepare for frozen-web style evaluation

### 3. Improve failure summaries

The current optimizer gives weakest task and broad recommendations. Next, add:

- missed required claims
- unsupported generated claims
- missing source IDs
- duplicate / redundant claim count
- graph edge statistics
- proposed next heuristic or reward change

Goal:

- make each optimizer run directly actionable

### 4. Deepen graph semantics

Add and test:

- `contradicts`
- `derived_from`
- `duplicates`
- `requires`
- `resolves_open_question`

Goal:

- make graph analysis useful for reward shaping and debugging

### 5. Separate reward from evaluator further

Current reward composition still depends heavily on evaluator metrics. Next:

- add explicit reward configs
- support multiple reward profiles
- emit reward traces
- compare outcome-only reward vs evidence-aware reward

Goal:

- prepare for RL training without hiding reward assumptions

### 6. Add trainer-readiness artifacts

Before integrating a full RL trainer, add:

- rollout JSONL format
- batch evaluator
- baseline run cache
- train/dev split for real-case tasks
- optimizer report export

Goal:

- make future RL integration less chaotic

## Suggested Near-Term Milestone

The next useful milestone is:

> EvidenceWeaver v0.2: a 15-20 task public-source real-case suite with source sidecars, richer failure summaries, and a stable graph/reward artifact contract.

Acceptance criteria:

- at least 15 real-case tasks
- all tasks have provenance metadata
- at least 5 tasks have source sidecars
- optimizer emits per-claim failure summaries
- test suite covers the optimizer, graph analysis, reward composition, and provenance validation
- README and paper draft reflect the real-case optimization results

## Handoff Notes

Future agents should:

1. Read `codex_work` first.
2. Read this file second.
3. Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m evidenceweaver.optimize.accuracy benchmarks/real_cases_v1/tasks
```

4. Add new real-case tasks before over-tuning current ones.
5. Always update `benchmarks/real_cases_v1/results/baseline_sweep.json` after benchmark or baseline changes.
6. Always append major work to `codex_work`.
