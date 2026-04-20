# EvidenceWeaver: Citation-Grounded Reinforcement Learning for Deep Research Agents

Status: pre-results working draft

## Abstract

Deep research agents increasingly rely on long-horizon tool use, retrieval, and synthesis, yet most current training signals still over-index on final-task success and under-index on evidence quality. This creates a mismatch between what users need from research systems and what many agentic reinforcement learning objectives optimize. We propose EvidenceWeaver, a research program and open-source scaffold for citation-grounded reinforcement learning in deep research agents. The core idea is to move beyond scalar outcome reward and optimize decomposed signals for answer coverage, citation support quality, evidence-chain completeness, source diversity, and budget efficiency. EvidenceWeaver couples those signals with structured evidence memory and evidence-centric evaluation so the resulting agents can be inspected rather than merely admired. The repository already contains a `v0` task and run schema, a deterministic search-read-write baseline agent, a heuristic offline evaluator, and a small snapshot-based benchmark seed set. This draft lays out the motivation, problem setting, method hypothesis, executable artifact, benchmark strategy, and experimental agenda for turning EvidenceWeaver into a serious research artifact.

## 1. Introduction

The strongest agent demos are no longer pure next-token systems. They plan, search, browse, inspect evidence, call tools, and synthesize across many steps. That shift from single-turn response generation to long-horizon interaction has made reinforcement learning newly relevant: the quality of an agent now depends on what actions it chooses, what evidence it collects, and how it spends a limited interaction budget.

At the same time, the standard of usefulness for research agents is different from the standard for chat-only assistants. A research agent should not merely return a plausible conclusion. It should return a conclusion that a human can inspect. That means a user should be able to ask: where did this claim come from, what evidence supports it, what evidence was ignored, and how strong is the support chain from sources to final answer?

This is the motivating gap behind EvidenceWeaver. In many settings, final-task success is necessary but not sufficient. A deep research agent that gives a correct answer for the wrong reasons is still operationally risky. A research agent that cannot show its work is harder to trust, harder to debug, and harder to improve.

Recent agentic RL work has made three things increasingly clear.

First, long-horizon interaction matters. Systems such as [ASearcher](https://arxiv.org/abs/2508.07976) show that search behavior can extend far beyond ten turns. Software and computer-use agents such as [SWE-RL](https://arxiv.org/abs/2502.18449), [SWE-Master](https://github.com/RUCAIBox/SWE-Master), and [ComputerRL](https://arxiv.org/abs/2508.14040) demonstrate that long trajectories and realistic tools reshape the learning problem.

Second, training infrastructure matters. [Agent Lightning](https://arxiv.org/abs/2508.03680), [AgentRL](https://arxiv.org/abs/2510.04206), and [rLLM](https://github.com/rllm-org/rllm) make the space of trainable agent programs much more accessible by decoupling or abstracting parts of the training pipeline.

Third, stability matters. [RAGEN](https://arxiv.org/abs/2504.20073), [RAGEN-2](https://arxiv.org/abs/2604.06268), and [ARLArena](https://arxiv.org/abs/2602.21534) argue that multi-turn agentic RL can fail in subtle ways: repetitive action templates, collapsed exploration, and apparently healthy statistics masking degraded behavior.

EvidenceWeaver is built on the claim that deep research agents are one of the most important places to bring these lessons together. They are practically useful, evaluation-relevant, and still under-served by current reward design.

## 2. Problem Statement

We study bounded research tasks in which an agent receives a question, interacts with a finite snapshot environment, and returns a cited answer. The environment contains a collection of documents, metadata, and evaluation expectations. The agent may search, open documents, write intermediate claims, and finish with a final response.

The project is motivated by three linked failures of current practice.

### 2.1 Outcome-only reward is too coarse

If we reward only final task success, then the agent can learn behaviors that look productive but are weakly grounded. A fluent answer with thin evidence can still score well if the final target is forgiving. In research workflows, that is not good enough.

### 2.2 Flat memory hides evidence structure

Many agent implementations reduce the trajectory to a text blob: searched queries, copied snippets, and partial summaries all collapse into a single context window. This makes it harder to tell which claims are already supported, which are contradictory, and which still need verification.

### 2.3 Long-horizon RL is unstable

Even if the task is well-defined, the learning dynamics can still be fragile. Exploration can collapse. Reward can become dominated by shortcuts. Template-like trajectories can emerge while top-line metrics remain deceptively calm.

EvidenceWeaver treats these as one design surface. The project is not only about training agents. It is about defining what should count as success for research agents and making that success measurable.

## 3. Core Thesis

EvidenceWeaver is built around three research bets.

### 3.1 Bet one: reward decomposition is better than scalar outcome reward

The first bet is that a research agent should be optimized with multiple interpretable reward terms rather than a single final score. A useful starting decomposition is:

- `R_answer`: does the answer cover the task?
- `R_citation`: are key claims properly supported?
- `R_chain`: is there a coherent evidence path from sources to conclusion?
- `R_diversity`: did the agent use varied evidence rather than loop on one source?
- `R_efficiency`: did the agent spend its budget well?

The point is not only better optimization. The point is better diagnosis. If a run improves, we want to know why.

### 3.2 Bet two: evidence should be explicit structure, not implicit residue

The second bet is that a research agent should maintain a lightweight evidence graph. Even a minimal graph with claim nodes, source nodes, and support or contradiction edges can be more useful than an opaque pile of copied text. In the long run, the graph should help the agent identify unsupported claims, explain why a conclusion is justified, and support more targeted reward shaping.

### 3.3 Bet three: stability diagnostics are part of the method

The third bet is methodological. Long-horizon RL is not stable enough to treat diagnostics as optional. The repository should make it easy to inspect action repetition, support redundancy, source diversity collapse, and claim-level failures. A project that only reports top-line task reward is not good enough for this setting.

## 4. Relation to Prior Work

EvidenceWeaver is not trying to replace the recent wave of general agent-training frameworks. It is trying to specialize the objective and evaluation story for research agents.

### 4.1 Stability and training science

The strongest immediate influence comes from work such as [RAGEN](https://arxiv.org/abs/2504.20073), [RAGEN-2](https://arxiv.org/abs/2604.06268), and [ARLArena](https://arxiv.org/abs/2602.21534). These papers reinforce a key lesson: agentic RL instability is not a corner case. It is central.

### 4.2 Training infrastructure

Frameworks such as [Agent Lightning](https://arxiv.org/abs/2508.03680), [AgentRL](https://arxiv.org/abs/2510.04206), and [rLLM](https://github.com/rllm-org/rllm) make it increasingly plausible to train agent programs without rewriting everything from scratch. EvidenceWeaver should use that trend, not compete with it. The novelty target is not "yet another trainer"; it is evidence-sensitive optimization and evaluation.

### 4.3 Deep search and research agents

Systems such as [ASearcher](https://arxiv.org/abs/2508.07976), [DeepDive](https://github.com/THUDM/DeepDive), and [CaRR](https://github.com/THUDM/CaRR) are the closest conceptual neighbors. They suggest that long-horizon search, synthetic data, and citation-aware reward design are converging on a common insight: deep research agents need richer learning signals than outcome-only success.

## 5. Repository Artifact: What Exists Today

EvidenceWeaver is still pre-results, but it is no longer just an idea. The repository already exposes a minimal executable artifact with enough structure to support iterative research.

### 5.1 Schemas

The repository defines:

- `schemas/task-bundle.v0.json`
- `schemas/run-artifact.v0.json`

These schemas formalize the contract between benchmark tasks, agent outputs, and evaluation. That matters because many early research repositories fail by letting interfaces drift before evaluation is stable.

### 5.2 Python package

The `src/evidenceweaver/` package currently includes:

- typed data loaders and validation helpers
- a deterministic search-read-write baseline agent
- an explicit evidence-graph module and builder
- a heuristic offline evaluator that produces evidence-centric metrics

The baseline agent is intentionally modest. It searches a snapshot task, opens top-ranked documents, extracts sentence-level claims, builds an explicit evidence graph, and emits a `run-artifact.v0` JSON structure with citations, graph state, actions, and a decomposed reward bundle.

### 5.3 Example artifacts

The repository includes a fully synthetic task under `examples/` and a more realistic seed benchmark under `benchmarks/snapshot_v0/`.

The synthetic task exists to lock down interfaces and tests. The snapshot benchmark exists to make the first "real-ish" research loop possible without waiting for a large frozen-web benchmark.

### 5.4 Tests

The repository already verifies:

- task and run loading
- CLI output paths
- evaluator behavior on strong versus weak runs
- baseline-agent execution on both synthetic and realistic tasks

That is not glamorous, but it is essential. A research project that wants to study reward design should not have ambiguous artifact contracts.

## 6. Snapshot Benchmark v0

A major step in this round of work is the creation of the first more realistic snapshot benchmark seeds.

### 6.1 Why snapshot-based first

The repository deliberately starts with snapshot tasks instead of live-web tasks because:

- reproducibility is much higher
- debugging is much easier
- evaluation noise is lower
- reward assumptions become visible sooner

This is a strategic decision, not a philosophical one. The goal is eventually to support richer environments, but frozen tasks are a better place to begin reward and benchmark design.

### 6.2 Current tasks

The benchmark currently contains three tasks.

#### Stability task

`agentic_rl_stability_task` asks the agent to explain why recent agentic RL work treats stability as a first-class issue and to cite concrete failure modes or stabilization mechanisms.

#### Training stack task

`agent_training_stack_task` asks the agent to compare the structural emphasis of Agent Lightning, AgentRL, and rLLM.

#### Deep search reward task

`deep_search_reward_task` asks why deep search agents need evidence-sensitive rewards beyond outcome-only success.

These tasks are all domain-relevant to the project itself, which makes them useful as both benchmark seeds and living design probes.

### 6.3 Provenance model

The benchmark documents are paraphrased digests anchored to primary-source URLs. That decision keeps the benchmark lightweight and avoids copying large web pages into the repository. The cost is that the benchmark is not yet a high-fidelity frozen-web benchmark. The benefit is that the project can already reason about realistic task shape, provenance, and evaluation.

## 7. Minimal Baseline Agent

The repository now contains a deterministic baseline agent. This is not the eventual research target. It is the first executable scaffold for the task format.

### 7.1 Agent loop

The current baseline agent does four things:

1. searches over the snapshot documents using prompt-token overlap
2. opens a bounded number of documents under a task budget
3. selects salient sentences as claim candidates
4. records claim-to-source support edges in an evidence graph
5. emits a cited final answer, a structured action trace, and a reward bundle

This creates a very small but concrete "agent loop" that future RL work can refine.

### 7.2 Why a deterministic baseline matters

A deterministic baseline offers several practical benefits:

- regression testing becomes easy
- interface design becomes easier to reason about
- evaluator changes can be tested without stochastic noise
- the repository can begin collecting benchmark artifacts immediately

In other words, a humble baseline is useful precisely because it is boring.

### 7.3 Why explicit graph state matters even in a weak baseline

The current graph implementation is simple, but it still changes the repository in an important way. The project no longer has to infer every structural assumption from free-form text. The artifact now records:

- which sources were opened
- which claims were written
- which support edges were asserted
- which prompt-focus terms remain under-supported

This is exactly the kind of inspectable state that later reward design and graph-aware policies can build on.

## 8. Evaluation Protocol

EvidenceWeaver's evaluator currently reports:

- `answer_coverage`
- `citation_coverage`
- `citation_precision`
- `chain_completeness`
- `source_diversity`
- `budget_efficiency`
- `unsupported_claim_rate`
- `overall_score`

This metric set is intentionally interpretable. It is more important, at this stage, to expose what the evaluator thinks it is measuring than to maximize benchmark sophistication.

The current evaluator is heuristic and should be described honestly as such. It uses keyword and phrase overlap plus citation checks over claim annotations. That means it is good enough to support iteration, but not yet good enough to support strong scientific claims.

## 9. Planned Method Evolution

The current repository suggests a staged path toward a real research contribution.

### 9.1 Stage one: stabilize contracts

This stage is already underway. The main goal is to freeze task and run formats, keep the evaluator inspectable, and widen the benchmark slowly.

### 9.2 Stage two: add evidence graph memory

The next major code change should be a lightweight evidence graph. At minimum, the graph should allow the agent to:

- register claims explicitly
- attach supporting evidence to claims
- surface unsupported claims
- emit compact reasoning traces

### 9.3 Stage three: add reward-side experimentation

Once the benchmark and artifact path are stable enough, the repository should add reward bundles that can be produced offline and then used online. This could begin with heuristic reward decomposition and later move toward verifier- or rubric-backed scoring.

### 9.4 Stage four: train policies, not just evaluate them

Only after the benchmark and reward surfaces are reasonably stable should the project pick a trainer stack and begin systematic RL experiments. Otherwise, the repository risks conflating benchmark instability, evaluator errors, and actual learning signal improvements.

## 10. Experimental Agenda

A credible paper from this project should eventually answer at least five questions.

1. Does decomposed reward improve evidence quality relative to outcome-only reward?
2. Does evidence-graph memory help training, inference, or both?
3. Which diagnostics predict long-horizon collapse earliest?
4. Which benchmark dimensions matter most for research-agent evaluation?
5. How much performance tradeoff exists between answer quality and evidence quality?

The first publishable evidence will likely come from ablations rather than from a huge absolute benchmark win.

## 11. Risks and Failure Modes

There are several obvious ways this project could go wrong.

### 11.1 Reward hacking

A policy could learn to cite frequently without citing meaningfully.

### 11.2 Evaluator overfitting

A simple heuristic evaluator can be gamed, especially if the benchmark remains small.

### 11.3 Benchmark narrowness

A too-small snapshot suite can produce optimistic conclusions that do not generalize.

### 11.4 Infrastructure drift

If the repository expands into a full framework before the benchmark contract is stable, it may become hard to interpret what any improvement actually means.

These risks are not reasons to stop. They are reasons to document failure carefully.

## 12. Limitations of the Current Draft

This repository is still pre-results. It does not claim:

- a state-of-the-art agent
- a validated RL recipe
- a mature evidence graph implementation
- a production-quality research benchmark

The current artifact is a scaffold, not a finished system. That limitation is acceptable because the repository is already useful as a design object: it makes the interfaces, benchmark assumptions, and evaluation philosophy concrete enough to test.

## 13. Conclusion

EvidenceWeaver starts from a simple idea: research agents should be optimized not just to answer, but to justify. If that idea is right, then the future of agentic RL for research systems will require better reward decomposition, better evidence structure, and better stability diagnostics. The current repository is an attempt to make that agenda executable, inspectable, and open to collaboration.

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
