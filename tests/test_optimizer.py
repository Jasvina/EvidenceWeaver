import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evidenceweaver.models import load_task_bundle
from evidenceweaver.optimize.accuracy import collect_task_paths, optimize_suite


REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_CASES_DIR = REPO_ROOT / "benchmarks" / "real_cases_v1" / "tasks"


class OptimizerTests(unittest.TestCase):
    def test_real_cases_suite_has_expected_task_count(self) -> None:
        paths = collect_task_paths(REAL_CASES_DIR)
        self.assertEqual(len(paths), 5)
        for path in paths:
            task = load_task_bundle(path)
            self.assertIsNotNone(task.provenance)
            self.assertTrue(task.provenance.primary_urls)

    def test_optimize_suite_returns_ranked_candidates(self) -> None:
        payload = optimize_suite(REAL_CASES_DIR)
        self.assertEqual(payload["task_count"], 5)
        self.assertIn("best_config", payload)
        self.assertIn("candidates", payload)
        self.assertGreaterEqual(len(payload["candidates"]), 3)
        best = payload["best_config"]
        self.assertGreaterEqual(best["average_overall_score"], 0.55)

    def test_optimizer_cli_emits_json(self) -> None:
        env = dict(os.environ)
        src_path = str(REPO_ROOT / "src")
        env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}:{env['PYTHONPATH']}"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "evidenceweaver.optimize.accuracy",
                str(REAL_CASES_DIR),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["task_count"], 5)
        self.assertIn("best_config", payload)


if __name__ == "__main__":
    unittest.main()
