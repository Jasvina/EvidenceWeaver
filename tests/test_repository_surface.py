import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


REPO_ROOT = Path(__file__).resolve().parents[1]


class RepositorySurfaceTests(unittest.TestCase):
    def test_docs_landing_page_references_present_repo_surface_files(self) -> None:
        required_paths = (
            REPO_ROOT / "CITATION.cff",
            REPO_ROOT / "docs" / "assets" / "og-card.svg",
            REPO_ROOT / "docs" / "assets" / "site.css",
            REPO_ROOT / "docs" / "assets" / "site.js",
        )
        for path in required_paths:
            self.assertTrue(path.exists(), msg=f"missing expected repository-surface file: {path}")

        html = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn("assets/og-card.svg", html)
        self.assertIn("CITATION.cff", html)
        self.assertIn("tests/test_repository_surface.py", html)

        blob_links = re.findall(r"https://github\\.com/Jasvina/EvidenceWeaver/blob/main/([^\"#]+)", html)
        for relative_path in blob_links:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((REPO_ROOT / relative_path).exists(), msg=f"broken docs blob link: {relative_path}")

        workflow_links = re.findall(r"https://github\\.com/Jasvina/EvidenceWeaver/actions/workflows/([^\"#]+)", html)
        for workflow_file in workflow_links:
            with self.subTest(workflow_file=workflow_file):
                self.assertTrue((REPO_ROOT / ".github" / "workflows" / workflow_file).exists(), msg=f"broken workflow link: {workflow_file}")

    def test_public_surface_claims_match_repository_state(self) -> None:
        html = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        real_case_task_count = len(list((REPO_ROOT / "benchmarks" / "real_cases_v1" / "tasks").glob("*.json")))
        snapshot_task_count = len(list((REPO_ROOT / "benchmarks" / "snapshot_v0" / "tasks").glob("*.json")))
        total_task_count = real_case_task_count + snapshot_task_count
        test_count = sum(path.read_text(encoding="utf-8").count("def test_") for path in (REPO_ROOT / "tests").glob("test_*.py"))
        best_score = json.loads((REPO_ROOT / "benchmarks" / "real_cases_v1" / "results" / "baseline_sweep.json").read_text(encoding="utf-8"))[
            "best_config"
        ]["average_overall_score"]

        self.assertIn(f"{real_case_task_count} real-case tasks", html)
        self.assertIn(f"{total_task_count} total tasks", html)
        self.assertIn(f"{test_count} verified tests", html)
        self.assertIn(f"{best_score:.4f} best average score", html)
        self.assertNotIn("eight-task suite", changelog)
        self.assertIn("twelve-task suite", changelog)
