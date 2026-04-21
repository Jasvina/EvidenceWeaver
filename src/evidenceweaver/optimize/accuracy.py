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


def evaluate_config_on_suite(task_paths: list[Path], config_name: str, config: BaselineAgentConfig) -> ConfigEvaluation:
    task_metrics: list[SuiteTaskMetric] = []
    for task_path in task_paths:
        task = load_task_bundle(task_path)
        run = run_task(task_path, config=config)
        report = evaluate_run(task, run)
        task_metrics.append(
            SuiteTaskMetric(
                task_id=task.task_id,
                overall_score=float(report.metrics["overall_score"]),
                answer_coverage=float(report.metrics["answer_coverage"]),
                citation_coverage=float(report.metrics["citation_coverage"]),
                citation_precision=float(report.metrics["citation_precision"]),
                unsupported_claim_rate=float(report.metrics["unsupported_claim_rate"]),
            )
        )
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple accuracy-optimization sweep over a benchmark task directory")
    parser.add_argument("task_dir", help="Directory containing task-bundle.v0 JSON files")
    args = parser.parse_args()
    print(json.dumps(optimize_suite(args.task_dir), indent=2))


if __name__ == "__main__":
    main()
