# Contributing to EvidenceWeaver

Thanks for considering a contribution.

EvidenceWeaver is still a research bootstrapping project, so the best contributions are the ones that reduce ambiguity, improve reproducibility, or sharpen the evaluation story.

## Good First Contribution Shapes

- clarify a benchmark proposal
- propose a reward term or anti-hacking check
- add a reproducible environment wrapper
- contribute a baseline or ablation
- improve the docs with stronger evidence or clearer framing
- add a failure case that the project should explicitly track

## What to Include in an Issue

Please open issues with a clear shape. Good titles usually start with:

- `benchmark:`
- `reward:`
- `eval:`
- `infra:`
- `docs:`
- `failure-case:`

Each issue should try to answer:

1. What problem are you addressing?
2. Why does it matter for research agents?
3. What concrete change do you propose?
4. How would we know it helped?

## Pull Request Expectations

For documentation PRs:

- keep claims precise
- link primary sources when possible
- avoid vague "state of the art" language unless it is supported

For code PRs:

- keep interfaces small and explicit
- prefer reversible changes
- document evaluation assumptions
- include the smallest useful verification step

## Philosophy

EvidenceWeaver should be a project that earns trust slowly.

That means:

- no inflated claims
- no benchmark cherry-picking
- no hidden reward shaping tricks
- no pretending a messy result is clean

If a contribution makes the project more inspectable, more reproducible, or more honest, it is likely directionally correct.
