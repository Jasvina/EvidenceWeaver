# Reward Design Sketch

EvidenceWeaver is built around the idea that deep research agents need richer learning signals than "got the final answer right" or "did not get it right."

This document sketches the first reward decomposition.

## Reward Formula

One simple starting point is:

```text
R_total =
  w_answer     * R_answer     +
  w_citation   * R_citation   +
  w_chain      * R_chain      +
  w_diversity  * R_diversity  +
  w_efficiency * R_efficiency
```

The exact weights should be treated as an experimental surface, not a fixed truth.

## Reward Terms

### `R_answer`

Measures whether the final answer solves the task.

Possible implementations:

- task success from an environment-specific evaluator
- rubric score from a verifier model plus human-checked calibration
- exact-match or fuzzy-match where applicable

Risk:

- outcome-only training can encourage brittle shortcuts and unsupported claims

### `R_citation`

Measures whether key claims are supported by retrieved or quoted evidence.

Possible implementations:

- claim-by-claim support verification
- citation precision over highlighted claims
- penalties for unsupported or weakly supported claims

Risk:

- the agent may learn to cite often without citing well

### `R_chain`

Measures whether the final report reflects a coherent evidence chain rather than isolated facts.

Possible implementations:

- reward multi-hop support paths
- reward linking intermediate facts to final conclusions
- penalize dangling claims without support edges

Risk:

- if over-weighted, the agent may over-construct chains that are verbose but not useful

### `R_diversity`

Measures whether the agent gathers evidence from meaningfully distinct sources and avoids redundancy.

Possible implementations:

- reward source diversity within reason
- penalize repeated retrieval of near-duplicate evidence
- reward contradiction discovery or triangulation

Risk:

- naive diversity rewards can push the agent toward irrelevant source spreading

### `R_efficiency`

Measures whether the agent uses tool budget wisely.

Possible implementations:

- soft penalties on unnecessary browsing or reading loops
- trajectory length normalization
- penalties for repeated low-information actions

Risk:

- too much pressure for efficiency can kill exploration

## Reward Schedule Ideas

The project should explore more than one schedule:

### Option A - Static weighted sum

The simplest baseline. Useful because it is easy to debug.

### Option B - Curriculum weighting

Early training emphasizes `R_answer` and `R_citation`, then gradually increases `R_chain` and `R_diversity`.

### Option C - Constraint-style shaping

Treat support quality as a soft constraint rather than just another bonus term.

## Diagnostics We Should Log

Reward design is only useful if its effects are visible.

Suggested logs:

- per-term reward values
- variance of each reward head over time
- unsupported-claim rate
- duplicate-source rate
- average evidence-chain depth
- repeated-tool-call rate

## Anti-Hacking Checks

Every reward term invites exploitation. The repo should include explicit checks for:

- citation stuffing without real support
- support copied from irrelevant passages
- fake chain structure that does not improve factual grounding
- diversity for its own sake
- extremely short but under-researched trajectories

## What "Good" Looks Like

A strong EvidenceWeaver trajectory should:

- retrieve enough material to answer the question well
- organize findings into a compact support structure
- connect evidence to conclusions clearly
- include citations that survive verification
- stay efficient without becoming timid

That is the behavior the reward system should make easier to learn.
