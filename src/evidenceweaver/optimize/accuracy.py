from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

from evidenceweaver.agent.baseline import BaselineAgentConfig, run_task
from evidenceweaver.eval.offline import evaluate_run
from evidenceweaver.models import load_task_bundle


@dataclass(frozen=True, slots=True)
class SuiteTaskMetric:
    task_id: str
    overall_score: float
    answer_coverage: float
    citation_coverage: float
    citation_precision: float
    unsupported_claim_rate: float
    missed_claim_ids: tuple[str, ...] = ()
    unsupported_claim_ids: tuple[str, ...] = ()
    missing_source_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConfigEvaluation:
    config_name: str
    config: BaselineAgentConfig
    average_overall_score: float
    average_citation_coverage: float
    average_answer_coverage: float
    task_metrics: tuple[SuiteTaskMetric, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "config_name": self.config_name,
            "config": asdict(self.config),
            "average_overall_score": self.average_overall_score,
            "average_citation_coverage": self.average_citation_coverage,
            "average_answer_coverage": self.average_answer_coverage,
            "task_metrics": [asdict(metric) for metric in self.task_metrics],
            "failure_summary": failure_summary(self),
        }


def default_candidate_configs() -> dict[str, BaselineAgentConfig]:
    return {
        "balanced_v1": BaselineAgentConfig(),
        "wider_first_pass": BaselineAgentConfig(initial_doc_cap=3, max_docs=3, max_claims=4),
        "claim_heavy": BaselineAgentConfig(max_claims=5, novelty_weight=1.3),
        "followup_friendly": BaselineAgentConfig(initial_doc_cap=2, followup_doc_limit=1, followup_min_total_budget=8),
        "precision_first": BaselineAgentConfig(max_claims=3, novelty_weight=1.8, signal_bonus_weight=1.2),
        "breadth_first": BaselineAgentConfig(max_docs=3, initial_doc_cap=2, followup_doc_limit=1, max_claims=5, novelty_weight=1.2),
    }


def collect_task_paths(task_dir: str | Path) -> list[Path]:
    return sorted(Path(task_dir).glob("*.json"))


def build_suite_task_metric(task, run, report) -> SuiteTaskMetric:
    claim_by_id = {claim.claim_id: claim for claim in task.required_claims}
    missed_claim_ids = tuple(result.claim_id for result in report.claim_results if not result.covered)
    unsupported_claim_ids = tuple(result.claim_id for result in report.claim_results if result.covered and not result.supported)
    cited_doc_ids = set(run.final_citations)
    for claim in run.claims:
        cited_doc_ids.update(claim.citations)
    missing_source_ids = tuple(
        doc_id
        for claim_id in unsupported_claim_ids
        for doc_id in claim_by_id[claim_id].supported_by
        if doc_id not in cited_doc_ids
    )
    return SuiteTaskMetric(
        task_id=task.task_id,
        overall_score=float(report.metrics["overall_score"]),
        answer_coverage=float(report.metrics["answer_coverage"]),
        citation_coverage=float(report.metrics["citation_coverage"]),
        citation_precision=float(report.metrics["citation_precision"]),
        unsupported_claim_rate=float(report.metrics["unsupported_claim_rate"]),
        missed_claim_ids=missed_claim_ids,
        unsupported_claim_ids=unsupported_claim_ids,
        missing_source_ids=missing_source_ids,
    )


def evaluate_config_on_suite(task_paths: list[Path], config_name: str, config: BaselineAgentConfig) -> ConfigEvaluation:
    task_metrics: list[SuiteTaskMetric] = []
    for task_path in task_paths:
        task = load_task_bundle(task_path)
        run = run_task(task_path, config=config)
        report = evaluate_run(task, run)
        task_metrics.append(build_suite_task_metric(task, run, report))
    return ConfigEvaluation(
        config_name=config_name,
        config=config,
        average_overall_score=round(mean(metric.overall_score for metric in task_metrics), 4),
        average_citation_coverage=round(mean(metric.citation_coverage for metric in task_metrics), 4),
        average_answer_coverage=round(mean(metric.answer_coverage for metric in task_metrics), 4),
        task_metrics=tuple(task_metrics),
    )


def optimize_suite(task_dir: str | Path) -> dict[str, object]:
    task_paths = collect_task_paths(task_dir)
    results = [
        evaluate_config_on_suite(task_paths, config_name=name, config=config)
        for name, config in default_candidate_configs().items()
    ]
    ranked = sorted(
        results,
        key=lambda item: (
            -item.average_overall_score,
            -item.average_citation_coverage,
            -item.average_answer_coverage,
        ),
    )
    best = ranked[0]
    return {
        "task_dir": str(task_dir),
        "task_count": len(task_paths),
        "best_config": best.to_dict(),
        "candidates": [result.to_dict() for result in ranked],
    }


def failure_summary(result: ConfigEvaluation) -> dict[str, object]:
    weakest = min(result.task_metrics, key=lambda metric: metric.overall_score)
    recommendations: list[str] = []
    if weakest.unsupported_claim_rate > 0.25:
        recommendations.append("reduce unsupported claims via stricter duplicate suppression or tighter claim selection")
    if weakest.citation_precision < 0.75:
        recommendations.append("improve citation precision by preferring richer multi-sentence evidence snippets")
    if weakest.answer_coverage < 1.0:
        recommendations.append("increase answer coverage with task-family-aware follow-up search or broader first-pass retrieval")
    if weakest.citation_coverage < 1.0:
        recommendations.append("improve citation coverage by ensuring each major claim is grounded in at least one selected document")
    return {
        "weakest_task_id": weakest.task_id,
        "weakest_task_score": weakest.overall_score,
        "missed_claim_ids": list(weakest.missed_claim_ids),
        "unsupported_claim_ids": list(weakest.unsupported_claim_ids),
        "missing_source_ids": list(weakest.missing_source_ids),
        "recommendations": recommendations,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple accuracy-optimization sweep over a benchmark task directory")
    parser.add_argument("task_dir", help="Directory containing task-bundle.v0 JSON files")
    args = parser.parse_args()
    print(json.dumps(optimize_suite(args.task_dir), indent=2))


if __name__ == "__main__":
    main()
