# Proposed v0 Interfaces

This document sketches the minimal interfaces that could make EvidenceWeaver usable without prematurely over-engineering the stack.

The keyword is `minimal`.

We want interfaces that are:

- small enough to implement quickly
- explicit enough to inspect
- stable enough to support early experiments

## 1. Agent Interface

The agent should expose a single step interface and a final report interface.

```text
AgentState -> Action
AgentState -> FinalAnswer
```

At minimum, `AgentState` should contain:

- task or query
- trajectory so far
- evidence graph snapshot
- budget counters

The `Action` space can start very small:

- `search(query)`
- `open(document_id)`
- `quote(span)`
- `write_claim(text, citations)`
- `finish(answer)`

## 2. Environment Interface

The environment should be responsible for executing actions and returning observations.

```text
step(action) -> observation, reward_stub, done, info
reset(task_id) -> initial_state
```

For the first version, `reward_stub` can stay sparse and lightweight. The heavy scoring logic should live in the reward server or evaluator.

## 3. Evidence Graph Interface

The evidence graph should remain deliberately simple.

### Core node types

- `ClaimNode`
- `SourceNode`
- `PassageNode`

### Core edge types

- `supports`
- `contradicts`
- `derived_from`
- `duplicates`

### Minimal operations

- add a claim
- attach evidence to a claim
- mark contradiction or duplication
- list unsupported claims
- export a compact trace

Current repository status:

- implemented as `src/evidenceweaver/graph/`
- current node types are `SourceNode`, `ClaimNode`, and `OpenQuestion`
- current edge type is `supports`
- the baseline agent already emits an `evidence_graph` inside `run-artifact.v0`

## 4. Reward Server Interface

The reward server should evaluate a trajectory or final answer and emit decomposed scores.

```text
score(trajectory, final_answer, evidence_graph) -> RewardBundle
```

`RewardBundle` should contain:

- `answer_score`
- `citation_score`
- `chain_score`
- `diversity_score`
- `efficiency_score`
- `total_score`
- diagnostic metadata

Current repository status:

- `RewardBundle` is now materialized from `EvalReport`
- the baseline agent attaches a reward bundle automatically after self-evaluation
- the evaluator CLI can also emit a scored copy of any run via `--emit-scored-run`

## 5. Evaluator Interface

The evaluator should be separate from the trainer.

```text
evaluate(run_artifact, task_bundle) -> EvalReport
```

This separation matters because we want to compare:

- online reward signals
- offline evaluation metrics
- human judgment

without collapsing them into one number too early.

## 6. Logging Interface

Every run should produce a compact artifact with:

- task metadata
- action trace
- retrieved evidence
- final answer
- reward bundle
- evaluation report

Current repository status:

- `run-artifact.v0` now supports `evidence_graph` plus `reward_bundle`
- the baseline agent writes both fields

If these artifacts are easy to read, the project will be much easier to debug and much easier to trust.

## 7. Why This v0 Matters

EvidenceWeaver should not start as a giant framework. It should start as a small research loop with clean boundaries:

- the agent acts
- the environment responds
- the evidence graph accumulates structure
- the reward server scores what happened
- the evaluator judges whether it actually helped

That is enough to begin serious experiments.
