import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidenceweaver.agent.baseline import BaselineAgent, run_task
from evidenceweaver.eval.offline import evaluate_run
from evidenceweaver.models import load_task_bundle


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


if __name__ == "__main__":
    unittest.main()
