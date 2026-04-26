# Security Policy

## Scope

EvidenceWeaver is an early-stage research repository. Security issues are still worth
reporting, especially when they could affect contributors, downstream integrators, or any
future hosted evaluation infrastructure.

Please report issues involving:

- arbitrary code execution through repository-provided scripts or artifacts
- credential leakage or accidental secret exposure
- dependency-chain or packaging risks introduced by the project
- unsafe artifact handling that could mislead users about provenance or verification
- workflow or CI misconfiguration that would expose write access or project secrets

## Supported Versions

The project does not currently maintain multiple supported release branches. Please report
issues against the latest `main` branch state.

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for a suspected vulnerability.

Instead, email `jasvina@outlook.com` with:

- a short summary of the issue
- affected files, commands, or workflows
- reproduction steps or proof-of-concept details
- any suggested mitigation if you have one

We will aim to:

- acknowledge receipt within 72 hours
- confirm whether the issue is in scope
- communicate mitigation or disclosure timing once the issue is validated

## Disclosure Preference

Please prefer responsible disclosure. If the issue affects users of a published artifact,
we may prepare a fix before public discussion.

## Research Integrity Note

For this repository, some issues may be closer to **artifact integrity** than classic
application security. If a bug causes misleading benchmark output, hides provenance, or
creates false confidence in evaluation results, please report it even if it is not a
traditional exploit.
