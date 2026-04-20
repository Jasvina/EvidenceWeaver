# EvidenceWeaver Research Agenda

This document turns the repo vision into a sequence of research bets and engineering milestones.

## North Star

Train research agents that are:

- correct enough to be useful
- grounded enough to be trusted
- traceable enough to be audited

## Core Hypotheses

### H1. Decomposed rewards improve evidence quality

A reward with separate terms for answer quality, citation support, and evidence-chain completeness will outperform outcome-only reward on evidence-centric metrics.

### H2. Evidence-graph memory reduces shallow retrieval loops

If the agent explicitly tracks which claims are already supported, contradicted, or unresolved, it should waste less budget on redundant browsing and produce more coherent reports.

### H3. Stability-aware filtering matters in long-horizon search

Long-horizon search behavior can degrade even when top-line task reward looks stable. Diagnostic filtering and rollout quality gates should improve learning stability.

## Initial Experimental Program

### Milestone A - Build the smallest useful system

Goal:

- one query
- one agent
- a small tool set
- a fixed task subset
- an answer with citations

Deliverables:

- minimal search-read-summarize loop
- structured logging of tool calls and retrieved passages
- citation-grounded final answer format
- offline evaluator that scores answer quality and citation support

Success criteria:

- the system produces readable trajectories
- the evaluator catches obvious unsupported claims
- manual inspection is easy

### Milestone B - Add structured evidence

Goal:

- move from flat memory to claim-evidence structure

Deliverables:

- a lightweight evidence graph abstraction
- claim nodes, source nodes, and support edges
- simple contradiction and duplication heuristics

Success criteria:

- the graph is simple enough to inspect
- it reduces repeated retrieval on held-out tasks

### Milestone C - Add decomposed rewards

Goal:

- train the policy against richer signals than final outcome alone

Candidate reward terms:

- `R_answer`
- `R_citation`
- `R_chain`
- `R_diversity`
- `R_efficiency`

Success criteria:

- reward traces are inspectable
- at least one evidence-centric metric improves over outcome-only reward

### Milestone D - Add stability diagnostics

Goal:

- detect and reduce long-horizon collapse

Possible diagnostics:

- repeated action-template rate
- evidence redundancy rate
- reward-term variance drift
- source-diversity collapse
- chain-depth collapse

Success criteria:

- diagnostics predict bad rollouts before top-line results crash
- a filtering or weighting strategy improves training behavior

## Evaluation Plan

We should evaluate at two levels.

### Task-level metrics

- answer accuracy or task success
- answer completeness
- latency
- tool budget consumption

### Evidence-level metrics

- citation precision
- citation coverage for key claims
- evidence-chain completeness
- source diversity
- unsupported-claim rate

## Baselines

EvidenceWeaver should compare against at least:

1. a non-RL search-and-summarize baseline
2. an outcome-only RL baseline
3. an ablated version without evidence graph memory
4. an ablated version without citation-specific reward terms

## Failure Cases We Should Expect

- reward hacking via superficial citation stuffing
- over-conservative policies that stop exploring too early
- noisy support scoring from imperfect retrieval
- long trajectories that look active but carry little new information
- citation correctness without chain completeness

We should actively publish these failure cases instead of hiding them.

## Suggested Milestone Order

1. freeze a task slice
2. build the minimal agent
3. build the offline evaluator
4. add the evidence graph
5. add decomposed rewards
6. run the first RL loop
7. add diagnostics and ablations
8. write the first paper draft

## What Makes This Repo Valuable Even Before Results

Even before a strong experimental result, the repo can be useful if it provides:

- a clean problem framing
- a reproducible benchmark recipe
- transparent reward design
- readable trajectories and evidence traces
- an honest log of what failed and why
