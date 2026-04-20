# EvidenceWeaver Paper Outline

Working title:

`EvidenceWeaver: Citation-Grounded Reinforcement Learning for Deep Research Agents`

## One-sentence pitch

We present a research-agent training framework that optimizes not only final-task success, but also citation support quality, evidence-chain completeness, and traceable long-horizon reasoning.

## Abstract Draft

Deep research agents increasingly rely on long-horizon tool use, retrieval, and synthesis, yet most training signals still prioritize final-task success over evidence quality. This creates a mismatch between what users need from research systems and what current agentic RL objectives emphasize. We introduce EvidenceWeaver, a citation-grounded reinforcement learning framework for deep research agents that combines structured evidence memory with decomposed rewards for answer quality, citation support, evidence-chain completeness, source diversity, and budget efficiency. EvidenceWeaver is designed to make research-agent behavior more auditable while preserving long-horizon exploration. We outline a reproducible benchmark recipe, a lightweight evidence graph abstraction, and a stability-aware training protocol for evidence-centric agent optimization. We propose evaluations that measure both task success and evidence quality, with special emphasis on unsupported-claim rate and citation coverage. Our goal is to turn research-agent training from outcome optimization into trust-aware optimization.

## Target Venues

Reasonable early targets:

- workshop track on LLM agents, alignment, or tools
- findings-style venue if the evaluation becomes mature
- main conference only if the benchmark and ablations become convincingly strong

## Story Arc

### 1. Problem

Research agents can produce plausible final answers without strong evidence structure.

### 2. Gap

Existing agentic RL often under-optimizes citation support and traceability.

### 3. Method

EvidenceWeaver adds:

- evidence graph memory
- citation-grounded decomposed rewards
- stability-aware diagnostics for long-horizon search

### 4. Evaluation

Measure not just answer quality, but support quality and traceability.

### 5. Result

The hoped-for result is a policy that is not only stronger, but more inspectable.

## Proposed Section Structure

1. Introduction
2. Background and Related Work
3. Problem Setting
4. EvidenceWeaver Method
5. Training and Stability Diagnostics
6. Evaluation Protocol
7. Results
8. Ablations
9. Failure Cases and Limitations
10. Conclusion

## Main Figures

The paper will probably need at least these figures:

1. system overview of the agent, evidence graph, and reward server
2. reward decomposition diagram
3. example trajectory with supported and unsupported claims
4. training stability diagnostics over time

## Ablation Table Ideas

- no evidence graph
- no citation reward
- no chain reward
- no diversity reward
- no stability filter
- outcome-only RL baseline
- strong non-RL baseline

## Evaluation Table Ideas

- task success
- citation precision
- citation coverage
- unsupported-claim rate
- average source diversity
- tool budget

## Risks

- support verification may be noisy
- evidence quality can be hard to judge automatically
- long-horizon RL can still be unstable even with better diagnostics
- benchmark choice may dominate conclusions

## What Would Make the Paper Strong

- a clean and reproducible benchmark slice
- a convincing evidence-centric metric suite
- a sharp ablation on reward decomposition
- honest failure analysis
- a compelling qualitative case study showing why the method matters
