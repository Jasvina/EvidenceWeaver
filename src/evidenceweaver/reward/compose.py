from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from evidenceweaver.models import EvalReport, RewardBundle


@dataclass(frozen=True, slots=True)
class RewardWeights:
    answer: float = 0.35
    citation: float = 0.25
    precision: float = 0.15
    chain: float = 0.10
    diversity: float = 0.10
    efficiency: float = 0.05


def compose_reward_bundle(report: EvalReport, weights: RewardWeights | None = None) -> RewardBundle:
    active = weights or RewardWeights()
    answer_score = float(report.metrics.get("answer_coverage", 0.0))
    citation_score = float(report.metrics.get("citation_coverage", 0.0))
    citation_precision = float(report.metrics.get("citation_precision", 0.0))
    chain_score = float(report.metrics.get("chain_completeness", 0.0))
    diversity_score = float(report.metrics.get("source_diversity", 0.0))
    efficiency_score = float(report.metrics.get("budget_efficiency", 0.0))
    total_score = (
        (active.answer * answer_score)
        + (active.citation * citation_score)
        + (active.precision * citation_precision)
        + (active.chain * chain_score)
        + (active.diversity * diversity_score)
        + (active.efficiency * efficiency_score)
    )
    return RewardBundle(
        answer_score=round(answer_score, 4),
        citation_score=round(citation_score, 4),
        chain_score=round(chain_score, 4),
        diversity_score=round(diversity_score, 4),
        efficiency_score=round(efficiency_score, 4),
        total_score=round(total_score, 4),
    )


def reward_notes(report: EvalReport) -> tuple[str, ...]:
    notes: list[str] = []
    if report.metrics.get("citation_coverage", 0.0) < 0.75:
        notes.append("citation coverage is still weak")
    if report.metrics.get("chain_completeness", 0.0) < 0.5:
        notes.append("claim chain coverage is incomplete")
    if report.metrics.get("unsupported_claim_rate", 0.0) > 0.25:
        notes.append("unsupported claim rate is elevated")
    if report.metrics.get("source_diversity", 0.0) < 0.5:
        notes.append("source diversity is narrow")
    return tuple(notes)


def main() -> None:
    from evidenceweaver.eval.offline import evaluate_paths

    parser = argparse.ArgumentParser(description="Compose an EvidenceWeaver reward bundle from a task and run artifact")
    parser.add_argument("task", help="Path to a task bundle JSON file")
    parser.add_argument("run", help="Path to a run artifact JSON file")
    args = parser.parse_args()
    report = evaluate_paths(args.task, args.run)
    payload = {
        "reward_bundle": asdict(compose_reward_bundle(report)),
        "notes": list(reward_notes(report)),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
