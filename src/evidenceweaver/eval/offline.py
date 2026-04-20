from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from evidenceweaver.models import ClaimMatch, EvalReport, GeneratedClaim, RunArtifact, TaskBundle, load_run_artifact, load_task_bundle


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = f" {_normalize(text)} "
    normalized_phrase = _normalize(phrase)
    if not normalized_phrase:
        return False
    return f" {normalized_phrase} " in normalized_text


def _keyword_coverage(text: str, keywords: Iterable[str]) -> float:
    unique_keywords = [keyword for keyword in dict.fromkeys(keywords) if keyword]
    if not unique_keywords:
        return 0.0
    hits = sum(1 for keyword in unique_keywords if _contains_phrase(text, keyword))
    return hits / len(unique_keywords)


def _best_generated_claim(required_claim_text: str, keywords: tuple[str, ...], generated_claims: tuple[GeneratedClaim, ...]) -> tuple[GeneratedClaim | None, float]:
    best_claim: GeneratedClaim | None = None
    best_score = -1.0
    for claim in generated_claims:
        score = max(
            _keyword_coverage(claim.text, keywords),
            1.0 if _contains_phrase(claim.text, required_claim_text) else 0.0,
        )
        if score > best_score:
            best_claim = claim
            best_score = score
    if best_score < 0.0:
        return None, 0.0
    return best_claim, best_score


def _round(value: float) -> float:
    return round(value, 4)


def evaluate_run(task: TaskBundle, run: RunArtifact) -> EvalReport:
    notes: list[str] = []
    if task.task_id != run.task_id:
        notes.append(f"run task_id {run.task_id!r} does not match bundle task_id {task.task_id!r}")

    answer_text = " ".join([run.answer, *[claim.text for claim in run.claims]])
    claim_results: list[ClaimMatch] = []
    covered_by_id: dict[str, bool] = {}

    for required in task.required_claims:
        answer_coverage = max(
            _keyword_coverage(answer_text, required.keywords),
            1.0 if _contains_phrase(answer_text, required.text) else 0.0,
        )
        matched_claim, claim_coverage = _best_generated_claim(required.text, required.keywords, run.claims)
        coverage = max(answer_coverage, claim_coverage)
        covered = coverage >= 0.6
        citations = matched_claim.citations if matched_claim is not None else ()
        if covered and not citations:
            citations = run.final_citations
        supported = covered and bool(set(citations) & set(required.supported_by))
        matched_text = matched_claim.text if matched_claim is not None else ""
        claim_results.append(
            ClaimMatch(
                claim_id=required.claim_id,
                covered=covered,
                coverage=_round(coverage),
                supported=supported,
                matched_text=matched_text,
                citations=tuple(citations),
            )
        )
        covered_by_id[required.claim_id] = covered

    supported_generated_claims = 0
    generated_claims_with_citations = 0
    unsupported_generated_claims = 0
    for claim in run.claims:
        best_required = None
        best_score = -1.0
        for required in task.required_claims:
            score = max(
                _keyword_coverage(claim.text, required.keywords),
                1.0 if _contains_phrase(claim.text, required.text) else 0.0,
            )
            if score > best_score:
                best_required = required
                best_score = score
        has_citations = bool(claim.citations)
        if has_citations:
            generated_claims_with_citations += 1
        is_supported = False
        if best_required is not None and best_score >= 0.6 and has_citations:
            is_supported = bool(set(claim.citations) & set(best_required.supported_by))
        if is_supported:
            supported_generated_claims += 1
        else:
            unsupported_generated_claims += 1

    total_required_claims = max(1, len(task.required_claims))
    covered_count = sum(1 for result in claim_results if result.covered)
    supported_count = sum(1 for result in claim_results if result.supported)

    dependent_claims = [claim for claim in task.required_claims if claim.depends_on]
    if dependent_claims:
        chain_hits = sum(
            1
            for claim in dependent_claims
            if covered_by_id.get(claim.claim_id) and all(covered_by_id.get(parent_id, False) for parent_id in claim.depends_on)
        )
        chain_completeness = chain_hits / len(dependent_claims)
    else:
        chain_completeness = 1.0

    source_pool = task.scorable_document_ids
    cited_docs = set(run.final_citations)
    for claim in run.claims:
        cited_docs.update(claim.citations)
    known_cited_docs = cited_docs & task.document_ids
    source_diversity = min(1.0, len(known_cited_docs & source_pool) / max(1, len(source_pool)))

    if task.budget is None or task.budget.max_steps <= 0:
        budget_efficiency = 1.0
    else:
        overflow = max(0, len(run.actions) - task.budget.max_steps)
        budget_efficiency = max(0.0, 1.0 - (overflow / task.budget.max_steps))

    answer_coverage = covered_count / total_required_claims
    citation_coverage = supported_count / total_required_claims
    citation_precision = supported_generated_claims / max(1, generated_claims_with_citations)
    unsupported_claim_rate = unsupported_generated_claims / max(1, len(run.claims))

    overall_score = (
        (0.35 * answer_coverage)
        + (0.25 * citation_coverage)
        + (0.15 * citation_precision)
        + (0.10 * chain_completeness)
        + (0.10 * source_diversity)
        + (0.05 * budget_efficiency)
    )

    metrics = {
        "answer_coverage": _round(answer_coverage),
        "citation_coverage": _round(citation_coverage),
        "citation_precision": _round(citation_precision),
        "chain_completeness": _round(chain_completeness),
        "source_diversity": _round(source_diversity),
        "budget_efficiency": _round(budget_efficiency),
        "unsupported_claim_rate": _round(unsupported_claim_rate),
        "overall_score": _round(overall_score),
    }
    return EvalReport(task_id=task.task_id, run_id=run.run_id, metrics=metrics, claim_results=tuple(claim_results), notes=tuple(notes))


def evaluate_paths(task_path: str | Path, run_path: str | Path) -> EvalReport:
    task = load_task_bundle(task_path)
    run = load_run_artifact(run_path)
    return evaluate_run(task, run)


def score_paths(task_path: str | Path, run_path: str | Path) -> tuple[EvalReport, RunArtifact]:
    task = load_task_bundle(task_path)
    run = load_run_artifact(run_path)
    report = evaluate_run(task, run)
    return report, run.with_reward_bundle(report.to_reward_bundle())


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a run artifact against an EvidenceWeaver task bundle")
    parser.add_argument("task", help="Path to a task bundle JSON file")
    parser.add_argument("run", help="Path to a run artifact JSON file")
    parser.add_argument(
        "--emit-scored-run",
        help="Optional path to write a copy of the run artifact enriched with reward_bundle",
    )
    args = parser.parse_args()
    report, scored_run = score_paths(args.task, args.run)
    if args.emit_scored_run:
        Path(args.emit_scored_run).write_text(json.dumps(scored_run.to_dict(), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report.to_dict(), indent=2))


if __name__ == "__main__":
    main()
