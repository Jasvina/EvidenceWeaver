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
