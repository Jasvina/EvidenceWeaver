from __future__ import annotations

import argparse
import json
from pathlib import Path

from evidenceweaver.models import RunArtifact, load_run_artifact


def summarize_graph(run: RunArtifact) -> dict[str, object]:
    if run.evidence_graph is None:
        return {
            "run_id": run.run_id,
            "task_id": run.task_id,
            "has_graph": False,
            "notes": ["run artifact does not include evidence_graph"],
        }

    edge_counts: dict[str, int] = {}
    for edge in run.evidence_graph.edges:
        edge_counts[edge.kind] = edge_counts.get(edge.kind, 0) + 1

    return {
        "run_id": run.run_id,
        "task_id": run.task_id,
        "has_graph": True,
        "opened_source_count": run.evidence_graph.opened_source_count,
        "opened_source_ids": list(run.evidence_graph.opened_source_ids),
        "claim_count": len(run.evidence_graph.claim_nodes),
        "supported_claim_ids": list(run.evidence_graph.supported_claim_ids),
        "prompt_focus": list(run.evidence_graph.prompt_focus),
        "covered_focus_tokens": list(run.evidence_graph.covered_focus_tokens),
        "prompt_focus_coverage_ratio": round(run.evidence_graph.prompt_focus_coverage_ratio, 4),
        "open_questions": [question.text for question in run.evidence_graph.open_questions],
        "edge_counts": edge_counts,
        "diagnostics": run.diagnostics.to_dict() if run.diagnostics is not None else None,
        "reward_bundle": run.reward_bundle.to_dict() if run.reward_bundle is not None else None,
    }


def analyze_path(path: str | Path) -> dict[str, object]:
    run = load_run_artifact(path)
    return summarize_graph(run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize the evidence graph contained in a run artifact")
    parser.add_argument("run", help="Path to a run artifact JSON file")
    args = parser.parse_args()
    print(json.dumps(analyze_path(args.run), indent=2))


if __name__ == "__main__":
    main()
