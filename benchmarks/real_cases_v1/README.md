# Real Cases v1

This suite is the repository's first **real-example-driven accuracy optimization** benchmark.

`snapshot_v0` proved that the artifact contract, baseline agent, evaluator, reward bundle, and graph analysis loop could all work together. `real_cases_v1` takes the next step: it broadens the task mix enough that we can start tuning the baseline against a more realistic, more varied suite instead of one or two handcrafted examples.

## What is in this suite

The suite currently includes five research-style tasks:

- `agentic_rl_stability_task`
- `agent_training_stack_task`
- `deep_search_reward_task`
- `computer_use_rl_task`
- `swe_agent_posttraining_task`

These tasks all stay within the same repository domain:

- agentic RL training stability
- agent-training frameworks
- deep search reward design
- computer-use agents
- software engineering agents

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

## Design note

The suite still uses paraphrased snapshot digests anchored to primary-source URLs. That keeps the repository lightweight and inspectable while pushing it into a more realistic tuning regime.
