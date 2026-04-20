import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidenceweaver.agent.baseline import BaselineAgent, run_task
from evidenceweaver.eval.offline import evaluate_run
from evidenceweaver.models import load_run_artifact, load_task_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_TASK = REPO_ROOT / "examples" / "tasks" / "synthetic_delay_task.json"
REALISTIC_TASK = REPO_ROOT / "benchmarks" / "snapshot_v0" / "tasks" / "agentic_rl_stability_task.json"


class BaselineAgentTests(unittest.TestCase):
    def test_agent_runs_within_budget_on_synthetic_task(self) -> None:
        task = load_task_bundle(SYNTHETIC_TASK)
        run = BaselineAgent().run(task)
        self.assertEqual(run.task_id, task.task_id)
        self.assertLessEqual(len(run.actions), task.budget.max_steps)
        self.assertTrue(run.final_citations)

    def test_agent_scores_non_trivially_on_realistic_task(self) -> None:
        task = load_task_bundle(REALISTIC_TASK)
        run = BaselineAgent().run(task)
        report = evaluate_run(task, run)
        self.assertGreaterEqual(report.metrics["overall_score"], 0.55)
        self.assertGreaterEqual(report.metrics["citation_coverage"], 0.66)

    def test_cli_emits_run_artifact_json(self) -> None:
        env = dict(os.environ)
        src_path = str(REPO_ROOT / "src")
        env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceweaver.agent.baseline",
                str(SYNTHETIC_TASK),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task_id"], "synthetic-delay-task")
        self.assertTrue(payload["claims"])

    def test_benchmark_directory_loads(self) -> None:
        benchmark_dir = REPO_ROOT / "benchmarks" / "snapshot_v0" / "tasks"
        task_ids = []
        for path in sorted(benchmark_dir.glob("*.json")):
            task = load_task_bundle(path)
            task_ids.append(task.task_id)
        self.assertEqual(len(task_ids), 3)
        self.assertIn("agentic-rl-stability-task", task_ids)

    def test_baseline_agent_scores_reasonably_on_all_snapshot_tasks(self) -> None:
        benchmark_dir = REPO_ROOT / "benchmarks" / "snapshot_v0" / "tasks"
        for path in sorted(benchmark_dir.glob("*.json")):
            task = load_task_bundle(path)
            run = run_task(path)
            report = evaluate_run(task, run)
            self.assertGreaterEqual(report.metrics["overall_score"], 0.55, path.name)

    def test_agent_emits_evidence_graph_and_reward_bundle(self) -> None:
        task = load_task_bundle(REALISTIC_TASK)
        run = BaselineAgent().run(task)
        self.assertIsNotNone(run.evidence_graph)
        self.assertIsNotNone(run.diagnostics)
        self.assertIsNotNone(run.reward_bundle)
        self.assertEqual(len(run.evidence_graph.claim_nodes), len(run.claims))
        self.assertGreaterEqual(len(run.evidence_graph.opened_source_ids), 1)
        self.assertEqual(run.diagnostics.opened_source_count, len(run.evidence_graph.opened_source_ids))
        report = evaluate_run(task, run)
        self.assertEqual(run.reward_bundle.total_score, report.metrics["overall_score"])

    def test_evaluator_cli_can_emit_scored_run(self) -> None:
        env = dict(os.environ)
        src_path = str(REPO_ROOT / "src")
        env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
        with tempfile.TemporaryDirectory() as temp_dir:
            run_path = Path(temp_dir) / "baseline_run.json"
            scored_path = Path(temp_dir) / "scored_run.json"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "evidenceweaver.agent.baseline",
                    str(REALISTIC_TASK),
                    "--output",
                    str(run_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "evidenceweaver.eval.offline",
                    str(REALISTIC_TASK),
                    str(run_path),
                    "--emit-scored-run",
                    str(scored_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            scored_run = load_run_artifact(scored_path)
            self.assertIsNotNone(scored_run.reward_bundle)
            self.assertIsNotNone(scored_run.evidence_graph)
            self.assertIsNotNone(scored_run.diagnostics)

    def test_graph_driven_follow_up_search_occurs_on_snapshot_suite(self) -> None:
        benchmark_dir = REPO_ROOT / "benchmarks" / "snapshot_v0" / "tasks"
        iteration_counts = []
        for path in sorted(benchmark_dir.glob("*.json")):
            run = run_task(path)
            iteration_counts.append(run.diagnostics.iteration_count)
            self.assertGreaterEqual(len(run.diagnostics.search_queries), 1)
        self.assertTrue(any(count > 1 for count in iteration_counts))


if __name__ == "__main__":
    unittest.main()
