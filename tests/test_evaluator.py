import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidenceweaver.eval.offline import evaluate_paths
from evidenceweaver.models import load_run_artifact, load_task_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]
TASK_PATH = REPO_ROOT / "examples" / "tasks" / "synthetic_delay_task.json"
GOOD_RUN_PATH = REPO_ROOT / "examples" / "runs" / "synthetic_delay_good_run.json"
WEAK_RUN_PATH = REPO_ROOT / "examples" / "runs" / "synthetic_delay_weak_run.json"


class EvaluatorTests(unittest.TestCase):
    def test_examples_load(self) -> None:
        task = load_task_bundle(TASK_PATH)
        good_run = load_run_artifact(GOOD_RUN_PATH)
        weak_run = load_run_artifact(WEAK_RUN_PATH)
        self.assertEqual(task.task_id, good_run.task_id)
        self.assertEqual(task.task_id, weak_run.task_id)
        self.assertEqual(len(task.required_claims), 3)

    def test_good_run_scores_higher_than_weak_run(self) -> None:
        good_report = evaluate_paths(TASK_PATH, GOOD_RUN_PATH)
        weak_report = evaluate_paths(TASK_PATH, WEAK_RUN_PATH)
        self.assertGreater(good_report.metrics["overall_score"], weak_report.metrics["overall_score"])
        self.assertEqual(good_report.metrics["citation_coverage"], 1.0)
        self.assertGreater(weak_report.metrics["unsupported_claim_rate"], good_report.metrics["unsupported_claim_rate"])

    def test_cli_outputs_json_report(self) -> None:
        env = dict(os.environ)
        src_path = str(REPO_ROOT / "src")
        env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceweaver.eval.offline",
                str(TASK_PATH),
                str(GOOD_RUN_PATH),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task_id"], "synthetic-delay-task")
        self.assertIn("overall_score", payload["metrics"])


if __name__ == "__main__":
    unittest.main()
