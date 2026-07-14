#!/usr/bin/env python3
import os
import sys
import unittest

# Add parent directory to sys.path so automation package can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automation.update_readme import format_repos_markdown


class TestGPSValidation(unittest.TestCase):
    def setUp(self):
        self.workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_repo_structure_exists(self):
        """Verify that all core folders exist in the workspace."""
        core_dirs = [
            ".github",
            ".github/workflows",
            ".github/ISSUE_TEMPLATE",
            "docs",
            "profile",
            "branding",
            "templates",
            "automation",
            "assets",
            "prompts",
            "tests",
        ]
        for d in core_dirs:
            full_path = os.path.join(self.workspace_dir, d)
            self.assertTrue(os.path.isdir(full_path), f"Required directory {d} is missing.")

    def test_yaml_syntax_basic(self):
        """Verify that workflow YAML configs have basic structural keywords."""
        workflow_dir = os.path.join(self.workspace_dir, ".github", "workflows")
        for fn in os.listdir(workflow_dir):
            if fn.endswith(".yml") or fn.endswith(".yaml"):
                path = os.path.join(workflow_dir, fn)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    self.assertTrue(
                        "name:" in content or "on:" in content,
                        f"Workflow {fn} appears invalid or missing trigger sections.",
                    )

    def test_update_readme_dry_run(self):
        """Test the data formatting block of the automation updater."""
        sample_repos = [
            {
                "name": "test-repo",
                "html_url": "https://github.com/Adithshajee/test-repo",
                "description": "A sample description.",
                "stargazers_count": 5,
                "forks_count": 2,
                "updated_at": "2026-07-11T12:00:00Z",
                "fork": False,
            }
        ]
        formatted = format_repos_markdown(sample_repos)
        self.assertIn("test-repo", formatted)
        self.assertIn("🌟 `5`", formatted)
        self.assertIn("A sample description.", formatted)


if __name__ == "__main__":
    unittest.main()
