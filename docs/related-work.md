# Related Work for EvidenceWeaver

This note is the working map of prior art most relevant to EvidenceWeaver.

Snapshot date: `2026-04-20`

The aim here is not to be exhaustive. It is to identify the threads that most directly shape the design space for citation-grounded RL in deep research agents.

## 1. Stability and Training Science

| Work | Link | Why it matters |
| --- | --- | --- |
| `RAGEN` | https://arxiv.org/abs/2504.20073 | Early framing of multi-turn RL for reasoning agents in interactive environments. |
| `RAGEN-2` | https://arxiv.org/abs/2604.06268 | Highlights template collapse and proposes diagnostics that treat stability as a core research problem. |
| `ARLArena` | https://arxiv.org/abs/2602.21534 | Organizes agentic RL instability into a more systematic benchmark and stabilization story. |

### Takeaway

The strongest lesson from this line of work is that long-horizon RL fails silently. A policy can look active while becoming behaviorally narrower, more templated, or less grounded. EvidenceWeaver should therefore treat reward diagnostics and rollout health as first-class artifacts.

## 2. General Agentic RL Infrastructure

| Work | Link | Why it matters |
| --- | --- | --- |
| `Agent Lightning` | https://arxiv.org/abs/2508.03680 | Pushes toward decoupling agent execution from RL training and minimizing invasive agent rewrites. |
| `AgentRL` | https://arxiv.org/abs/2510.04206 | Emphasizes fully asynchronous multi-turn and multi-task agent RL pipelines. |
| `rLLM` | https://github.com/rllm-org/rllm | A practical open-source substrate for training or fine-tuning agent programs. |

### Takeaway

The tooling layer is improving rapidly. That suggests EvidenceWeaver should avoid becoming "just another framework." The sharper angle is reward design, evidence structure, and evaluation for research agents.

## 3. Deep Search and Research Agents

| Work | Link | Why it matters |
| --- | --- | --- |
| `ASearcher` / `Beyond Ten Turns` | https://arxiv.org/abs/2508.07976 | Shows that long-horizon search behavior is trainable and important in deep search agents. |
| `ASearcher` repo | https://github.com/inclusionAI/ASearcher | Useful reference for long-horizon search-agent implementation shape. |
| `DeepDive` | https://github.com/THUDM/DeepDive | Points toward synthetic data plus multi-turn training for deep search. |
| `CaRR` | https://github.com/THUDM/CaRR | Strong signal that citation-aware or rubric-aware reward design is becoming central for deep search. |

### Takeaway

This is the closest existing lane to EvidenceWeaver. The opportunity is not to repeat deep search training in general, but to make evidence quality a direct optimization target and a measurable output.

## 4. Domain-Specific Long-Horizon Agents

| Work | Link | Why it matters |
| --- | --- | --- |
| `ComputerRL` | https://arxiv.org/abs/2508.14040 | Shows how RL enters computer-use agents with mixed action spaces and realistic environment constraints. |
| `ComputerRL` repo | https://github.com/THUDM/ComputerRL | A concrete code reference for environment engineering under long-horizon RL. |
| `SWE-RL` | https://arxiv.org/abs/2502.18449 | One of the clearest early signals that software agents can benefit from RL. |
| `SWE-Master` | https://github.com/RUCAIBox/SWE-Master | Strong open-source reference for combining agentic SFT, RL, tools, and test-time scaling. |

### Takeaway

These projects demonstrate the operational difficulty of agentic RL: tools, latency, environment noise, and sparse rewards all matter. EvidenceWeaver should learn from their engineering discipline while staying scoped to research agents.

## 5. Surveys and Landscape Pieces

| Work | Link | Why it matters |
| --- | --- | --- |
| `The Landscape of Agentic Reinforcement Learning for LLMs: A Survey` | https://arxiv.org/abs/2509.02547 | A useful overview of how the field is partitioning itself and where the open gaps are. |

### Takeaway

The survey-level view supports a strategic conclusion: deep research agents are one of the most compelling places to combine real utility with unsolved RL questions.

## What EvidenceWeaver Tries to Add

The project is currently aiming for this gap:

- many systems optimize answer success
- some systems optimize search depth
- a smaller set starts to optimize citation quality
- very few open systems appear centered on **evidence-graph-aware, citation-grounded, stability-aware RL for research agents**

That last line is where EvidenceWeaver wants to live.

## Working Hypothesis

If we optimize for:

- final answer quality
- citation support quality
- evidence-chain completeness
- source diversity and efficient budget use

then we should be able to produce a research agent that is not only stronger, but also easier to audit and more valuable as a practical tool.

## Open Gaps Worth Tracking

- publicly reproducible deep research environments with fixed snapshots
- human-aligned metrics for support quality and evidence completeness
- early-warning diagnostics for long-horizon policy collapse
- reward recipes that improve grounding without making the agent timid
- ablations that isolate the value of structured memory from reward improvements
