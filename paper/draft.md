# EvidenceWeaver: Citation-Grounded Reinforcement Learning for Deep Research Agents

Status: pre-results working draft

## Abstract

Deep research agents increasingly rely on long-horizon tool use, retrieval, and synthesis, yet most training signals still prioritize final-task success over evidence quality. This creates a mismatch between what users need from research systems and what current agentic reinforcement learning objectives optimize. We propose EvidenceWeaver, a research-agent training framework centered on citation-grounded reinforcement learning, structured evidence memory, and evidence-centric evaluation. The core idea is to move from scalar outcome reward toward decomposed signals for answer coverage, citation support quality, evidence-chain completeness, source diversity, and budget efficiency. EvidenceWeaver pairs those signals with a lightweight evidence graph so the agent can track which claims are already supported, contradicted, or unresolved. Because long-horizon reinforcement learning is known to fail in subtle ways, the project also treats stability diagnostics as a first-class component rather than an afterthought. This draft describes the problem setting, method, benchmark recipe, and experimental agenda for a reproducible open-source research program.

## 1. Introduction

The most compelling research-agent demos today can search, browse, read, and synthesize across many steps. But practical usefulness depends on more than final answer quality. In real research workflows, a strong answer needs to be inspectable: a reviewer should be able to trace a claim back to its sources, understand what evidence was used, and notice where the support chain is weak.

Current agentic RL work has pushed the field forward on long-horizon interaction, training infrastructure, and task-specific environments. Recent work such as [RAGEN](https://arxiv.org/abs/2504.20073), [RAGEN-2](https://arxiv.org/abs/2604.06268), and [ARLArena](https://arxiv.org/abs/2602.21534) has made it increasingly clear that long-horizon RL stability is its own problem, not just a scaling detail. In parallel, systems such as [Agent Lightning](https://arxiv.org/abs/2508.03680), [AgentRL](https://arxiv.org/abs/2510.04206), and [rLLM](https://github.com/rllm-org/rllm) have made it easier to train or fine-tune agent programs. Deep search agents such as [ASearcher](https://arxiv.org/abs/2508.07976), [DeepDive](https://github.com/THUDM/DeepDive), and [CaRR](https://github.com/THUDM/CaRR) suggest that evidence-sensitive optimization is both possible and valuable.

This draft argues that deep research agents are a particularly important setting for the next phase of agentic RL. They are useful enough to matter, open-ended enough to expose long-horizon failure modes, and structured enough to support evidence-centric evaluation. EvidenceWeaver is our attempt to turn that opportunity into a practical research program.

## 2. Problem Setting

We consider tasks where an agent receives a research question and interacts with a bounded environment of searchable or browsable sources. The agent may issue tool calls, inspect documents, record intermediate claims, and produce a final cited answer. Unlike pure question answering, the system is not judged solely by whether it reaches a plausible final statement. It is also judged by whether its claims are actually supported.

This setting creates three linked challenges.

First, reward design is hard. If we only reward final answers, the agent may learn to produce fluent but weakly supported conclusions. If we only reward local evidence matching, the agent may become conservative and stop exploring. Second, memory is hard. Flat context accumulation encourages repeated retrieval, weak source tracking, and fragile synthesis. Third, stability is hard. Long-horizon RL can look healthy in top-line reward while the policy quietly collapses into repetitive or shallow patterns.

EvidenceWeaver treats these three problems as one design surface rather than as isolated modules.

## 3. Method Overview

EvidenceWeaver has three primary ingredients.

### 3.1 Decomposed evidence-centric rewards

Instead of a single scalar task reward, EvidenceWeaver proposes separate terms for:

- answer coverage or task success
- citation support quality
- evidence-chain completeness
- source diversity
- budget efficiency

The immediate reason for decomposing reward is interpretability. If a training run improves, we should know whether it improved because the agent became more correct, because it started citing better evidence, or because it simply learned to exploit a narrower part of the environment.

### 3.2 Evidence graph memory

The agent maintains a lightweight evidence graph with claim nodes, source nodes, and support or contradiction edges. This graph is intentionally small in the first version. Its purpose is not to implement sophisticated symbolic reasoning; its purpose is to avoid treating the agent's working memory as an unstructured text dump.

A graph-based memory can support several useful operations early:

- listing unsupported claims
- tracing a conclusion back to its sources
- detecting duplicate or contradictory evidence
- exposing what the agent still needs to verify

### 3.3 Stability-aware training diagnostics

EvidenceWeaver borrows its caution from recent long-horizon RL work. We expect collapse modes such as repeated action templates, citation stuffing, shallow source loops, and answers that look grounded but depend on redundant evidence. The project therefore treats diagnostics as first-class artifacts. A good run should ship not only trajectories and scores, but also the traces that explain why those scores moved.

## 4. Evaluation Philosophy

A central claim of this project is that research-agent evaluation should separate answer quality from evidence quality.

We therefore propose two metric families.

### 4.1 Task-level metrics

These metrics capture whether the answer is useful at all:

- answer accuracy or coverage
- answer completeness
- latency
- tool budget consumption

### 4.2 Evidence-level metrics

These metrics capture whether the answer deserves trust:

- citation precision
- citation coverage for key claims
- evidence-chain completeness
- unsupported-claim rate
- source diversity

The current repository already contains a minimal offline evaluator implementing a first-pass version of this idea on a synthetic benchmark task. The evaluator is intentionally simple, but it forces the project to make its scoring assumptions explicit rather than vague.

## 5. Benchmark Strategy

The first benchmark should not aim for maximum realism. It should aim for reproducibility.

That implies starting with a bounded, snapshot-based deep research setting in which:

- each task has a fixed prompt
- the environment exposes a stable set of documents
- the agent must answer with citations
- evaluation is deterministic enough to compare runs over time

This does not replace live-web evaluation. It creates a controllable substrate that makes debugging reward and training behavior possible.

## 6. Repository Agenda

The open-source repository is designed to grow in three layers.

### 6.1 Layer one: research contract

The docs define the problem, the benchmark slice, the interface boundaries, and the reward design surface.

### 6.2 Layer two: executable baseline

The codebase starts with a small Python package containing:

- task and run schemas
- a minimal offline evaluator
- example task bundles and trajectories
- tests that keep the scoring logic honest

### 6.3 Layer three: training system

Once the benchmark slice is stable, the project can add:

- a small search-read-write agent loop
- evidence graph state updates
- reward-server integration
- trainer adapters for a chosen RL stack

This staged approach is deliberate. Many open-source research repositories become hard to reason about because they rush into infrastructure before they have agreed on what the system is supposed to prove.

## 7. Expected Failure Modes

We do not expect the first training recipe to work cleanly. The most likely failure modes include:

- citation stuffing without genuine support
- over-conservative policies that stop exploring too early
- duplicate evidence that creates the illusion of confidence
- policies that optimize local support but lose global synthesis quality
- reward instability that encourages templated trajectories

Publishing these failures is part of the project, not a sign that the project failed.

## 8. Limitations

EvidenceWeaver is currently a pre-results program. The present repository does not claim a state-of-the-art agent, a validated benchmark, or a stable RL recipe. The evaluator is heuristic, the benchmark slice is intentionally small, and the evidence graph design is still under active refinement. These limitations are acceptable at this stage because the current goal is to establish a crisp, reproducible research direction.

## 9. Conclusion

Agentic RL is moving from single-turn reasoning toward long-horizon interaction, but research agents still need better objectives. EvidenceWeaver proposes that correctness is only one part of the target: grounding, traceability, and evidence quality should also be optimized directly. If this thesis is right, then research-agent training should become easier to audit, easier to debug, and more aligned with how people actually decide whether an answer is trustworthy.

## References

- [RAGEN](https://arxiv.org/abs/2504.20073)
- [RAGEN-2](https://arxiv.org/abs/2604.06268)
- [ARLArena](https://arxiv.org/abs/2602.21534)
- [Agent Lightning](https://arxiv.org/abs/2508.03680)
- [AgentRL](https://arxiv.org/abs/2510.04206)
- [ASearcher / Beyond Ten Turns](https://arxiv.org/abs/2508.07976)
- [The Landscape of Agentic Reinforcement Learning for LLMs: A Survey](https://arxiv.org/abs/2509.02547)
- [rLLM repository](https://github.com/rllm-org/rllm)
- [DeepDive repository](https://github.com/THUDM/DeepDive)
- [CaRR repository](https://github.com/THUDM/CaRR)
