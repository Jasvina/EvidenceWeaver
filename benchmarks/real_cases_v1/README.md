# Real Cases v1

This suite is the repository's first **real-example-driven accuracy optimization** benchmark.

`snapshot_v0` proved that the artifact contract, baseline agent, evaluator, reward bundle, and graph analysis loop could all work together. `real_cases_v1` takes the next step: it broadens the task mix enough that we can start tuning the baseline against a more realistic, more varied suite instead of one or two handcrafted examples.

## What is in this suite

The suite currently includes twelve research-style tasks:

- `agentic_rl_stability_task`
- `agent_training_stack_task`
- `agent_diagnostics_reliability_task`
- `benchmark_reproducibility_task`
- `browser_agent_environment_task`
- `computer_use_rl_task`
- `deep_search_reward_task`
- `swe_agent_posttraining_task`
- `terminal_agent_rl_task`
- `tool_user_interaction_task`
- `trajectory_credit_assignment_task`
- `verifiable_environment_feedback_task`

These tasks stay within the same evidence-centric agent domain while covering a broader operating surface:

- agentic RL training stability
- agent-training frameworks
- diagnostics and repeated-trial reliability
- benchmark reproducibility surfaces
- browser-agent environments and integrations
- deep search reward design
- computer-use agents
- software engineering agents
- terminal-centric agents
- tool-user interaction benchmarks
- trajectory-level credit assignment
- verifiable environment feedback across domains

Each task now includes a `provenance` section with:

- `snapshot_style`
- `primary_urls`
- `refresh_hint`
- `notes`

That metadata is intentionally small, but it gives the suite a more durable source-of-truth contract than bare task text alone.

## Source sidecars

Every real-case task now also has a sidecar directory under `benchmarks/real_cases_v1/sources/<task_id>/` with:

- `source_manifest.json`
- one `source_<doc_id>.md` file per snapshot digest

These sidecars keep the benchmark lightweight while making provenance more auditable and easier to inspect task by task.

## Why this suite exists

The goal is not to claim benchmark completeness. The goal is to create a practical, real-example-driven loop for:

- measuring baseline accuracy on a broader suite
- tuning deterministic retrieval and claim-selection heuristics
- spotting which task families break first
- making future RL improvements compare against something stronger than a toy seed set

## How to run the optimization sweep

```bash
PYTHONPATH=src python3 -m evidenceweaver.optimize.accuracy \
  benchmarks/real_cases_v1/tasks
```

The optimizer evaluates a small set of baseline configurations and returns:

- the best config
- ranked candidate configs
- per-task metrics for each config
- failure summaries with the weakest task, missed claim IDs, missing source IDs, and suggested next moves

## Design note

The suite still uses paraphrased snapshot digests anchored to primary-source URLs. That keeps the repository lightweight and inspectable while pushing it into a more realistic tuning regime.

## Canonical first run

If you are new to the repo, the simplest artifact path is:

1. Run the baseline on `benchmarks/snapshot_v0/tasks/agent_training_stack_task.json`.
2. Score the resulting run with `evidenceweaver.eval.offline`.
3. Inspect `/tmp/evidenceweaver_scored_run.json` plus `python3 -m evidenceweaver.graph.analyze /tmp/evidenceweaver_scored_run.json`.

This gives you one readable task, one trajectory, one scored artifact, and one graph summary before you move on to the full suite.

