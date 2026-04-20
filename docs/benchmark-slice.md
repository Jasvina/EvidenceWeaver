# Proposed Benchmark Slice

This document sketches the first benchmark slice EvidenceWeaver should target.

The point of the first slice is not to be comprehensive. The point is to be:

- realistic enough to matter
- narrow enough to reproduce
- structured enough to support evidence-centric evaluation

## Principles

The first benchmark slice should:

1. require multi-step information gathering
2. require synthesis rather than single-fact lookup
3. support citation-grounded answers
4. be stable enough to compare runs over time

## Recommended Starting Shape

The most practical starting point is a **snapshot-based deep research benchmark**:

- each task comes with a fixed query
- the environment exposes a bounded collection of pages or documents
- the agent must browse, read, and answer with citations
- evaluation scores both answer quality and citation quality

This is less glamorous than full live-web evaluation, but it is much easier to reproduce and debug.

## Why Snapshot-Based First

Live web evaluation is attractive, but it creates problems early:

- page content changes over time
- site availability adds noise
- retrieval can break for reasons unrelated to policy quality
- reward debugging becomes harder

A fixed-snapshot benchmark gives us a stable target while the training loop is still young.

## Candidate Task Types

The first slice should mix tasks like:

- compare two competing technical approaches
- synthesize a timeline from multiple sources
- answer a multi-hop factual question with explicit support
- identify contradictions across sources
- write a short research note with cited claims

## Minimal Evaluation Bundle

Each task should ideally include:

- prompt or query
- document or page bundle
- reference answer or rubric
- list of key claims expected in a strong answer
- citation expectations for those claims

## Metrics

At minimum, the first benchmark slice should report:

- answer score
- citation precision
- citation coverage
- unsupported-claim rate
- source diversity
- tool budget

## What to Delay Until Later

The first benchmark does not need:

- full live-web browsing
- very large task counts
- multimodal browsing
- multi-agent collaboration
- learned reward models

Those can come later once the basic system is trustworthy.
