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
        self.assertEqual(len(paths), 12)
        for path in paths:
            task = load_task_bundle(path)
            self.assertIsNotNone(task.provenance)
            self.assertTrue(task.provenance.primary_urls)


    def test_real_case_source_sidecars_cover_every_task(self) -> None:
        sources_root = REPO_ROOT / "benchmarks" / "real_cases_v1" / "sources"
        for path in collect_task_paths(REAL_CASES_DIR):
            task = load_task_bundle(path)
            sidecar_dir = sources_root / task.task_id
            self.assertTrue(sidecar_dir.exists(), msg=f"missing sidecar dir for {task.task_id}")
            manifest_path = sidecar_dir / "source_manifest.json"
            self.assertTrue(manifest_path.exists(), msg=f"missing source manifest for {task.task_id}")
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["task_id"], task.task_id)
            self.assertEqual(manifest["source_count"], len(task.documents))
            manifest_doc_ids = {entry["doc_id"] for entry in manifest["sources"]}
            self.assertEqual(manifest_doc_ids, {document.doc_id for document in task.documents})
            for entry in manifest["sources"]:
                self.assertTrue((sidecar_dir / entry["file"]).exists(), msg=f"missing sidecar file for {task.task_id}:{entry['doc_id']}")

    def test_optimize_suite_returns_ranked_candidates(self) -> None:
        payload = optimize_suite(REAL_CASES_DIR)
        self.assertEqual(payload["task_count"], 12)
        self.assertIn("best_config", payload)
        self.assertIn("candidates", payload)
        self.assertGreaterEqual(len(payload["candidates"]), 3)
        best = payload["best_config"]
        self.assertGreaterEqual(best["average_overall_score"], 0.55)
        self.assertIn("failure_summary", best)
        self.assertIn("weakest_task_id", best["failure_summary"])
        self.assertIn("recommendations", best["failure_summary"])
        self.assertIn("missed_claim_ids", best["failure_summary"])
        self.assertIn("unsupported_claim_ids", best["failure_summary"])
        self.assertIn("missing_source_ids", best["failure_summary"])
        self.assertIn("graph_edge_counts", best["failure_summary"])
        self.assertIn("open_question_count", best["failure_summary"])
        self.assertIn("duplicate_edge_count", best["failure_summary"])
        self.assertIn("contradiction_edge_count", best["failure_summary"])

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
        self.assertEqual(payload["task_count"], 12)
        self.assertIn("best_config", payload)


if __name__ == "__main__":
    unittest.main()
