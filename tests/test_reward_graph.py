import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidenceweaver.agent.baseline import run_task
from evidenceweaver.eval.offline import evaluate_run
from evidenceweaver.graph.analyze import summarize_graph
from evidenceweaver.graph import EvidenceGraphBuilder
from evidenceweaver.models import load_task_bundle
from evidenceweaver.models import Document
from evidenceweaver.reward.compose import compose_reward_bundle, reward_notes


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = REPO_ROOT / "benchmarks" / "snapshot_v0" / "tasks"


class RewardAndGraphTests(unittest.TestCase):
    def test_reward_module_matches_baseline_reward_bundle(self) -> None:
        task_path = BENCHMARK_DIR / "agentic_rl_stability_task.json"
        task = load_task_bundle(task_path)
        run = run_task(task_path)
        report = evaluate_run(task, run)
        composed = compose_reward_bundle(report)
        self.assertEqual(run.reward_bundle, composed)
        self.assertIsInstance(reward_notes(report), tuple)

    def test_graph_contains_non_support_relationship_edge(self) -> None:
        task_path = BENCHMARK_DIR / "agent_training_stack_task.json"
        run = run_task(task_path)
        edge_kinds = {edge.kind for edge in run.evidence_graph.edges}
        self.assertIn("supports", edge_kinds)
        self.assertTrue(edge_kinds & {"derived_from", "duplicates"})

    def test_reward_cli_emits_bundle_and_notes(self) -> None:
        env = dict(os.environ)
        src_path = str(REPO_ROOT / "src")
        env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
        run = run_task(BENCHMARK_DIR / "agent_training_stack_task.json")
        run_path = Path("/tmp/evidenceweaver_reward_test_run.json")
        run_path.write_text(json.dumps(run.to_dict(), indent=2) + "\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceweaver.reward.compose",
                str(BENCHMARK_DIR / "agent_training_stack_task.json"),
                str(run_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)
        self.assertIn("reward_bundle", payload)
        self.assertIn("notes", payload)

    def test_graph_analysis_cli_and_summary(self) -> None:
        env = dict(os.environ)
        src_path = str(REPO_ROOT / "src")
        env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
        run = run_task(BENCHMARK_DIR / "agentic_rl_stability_task.json")
        summary = summarize_graph(run)
        self.assertTrue(summary["has_graph"])
        self.assertIn("edge_counts", summary)
        run_path = Path("/tmp/evidenceweaver_graph_analysis_run.json")
        run_path.write_text(json.dumps(run.to_dict(), indent=2) + "\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceweaver.graph.analyze",
                str(run_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task_id"], "agentic-rl-stability-task")
        self.assertIn("prompt_focus_coverage_ratio", payload)
        self.assertIn("unsupported_claim_ids", payload)
        self.assertIn("contradicted_claim_ids", payload)
        self.assertIn("open_question_count", payload)

    def test_graph_builder_detects_contradiction_edges(self) -> None:
        documents = [
            Document(doc_id="doc-1", title="Support", url="https://example.com/1", content="Tool use improves reliability."),
            Document(doc_id="doc-2", title="Challenge", url="https://example.com/2", content="Tool use does not improve reliability."),
        ]
        graph = EvidenceGraphBuilder(graph_id="graph-contradiction", prompt="Does tool use improve reliability?", documents=documents)
        graph.add_claim("claim-1", "Tool use improves reliability.", ("doc-1",))
        graph.add_claim("claim-2", "Tool use does not improve reliability.", ("doc-2",))
        built = graph.build()
        edge_kinds = {edge.kind for edge in built.edges}
        self.assertIn("contradicts", edge_kinds)
        self.assertEqual(set(built.contradicted_claim_ids), {"claim-1", "claim-2"})


if __name__ == "__main__":
    unittest.main()
