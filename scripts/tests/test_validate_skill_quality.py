"""Regression tests for the Ada distribution validator."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validate_skill_quality.py"
SPEC = importlib.util.spec_from_file_location("ada_validator", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


class DistributionValidatorTests(unittest.TestCase):
    def make_distribution(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        skill = root / "skills" / "software-development" / "ada-example"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: ada-example\n"
            'description: "Use when validating an example distribution."\n'
            "version: 1.0.0\n"
            "---\n\n"
            "# Example\n",
            encoding="utf-8",
        )
        (root / "distribution.yaml").write_text(
            "name: ada\n"
            "version: 1.0.0\n"
            "description: Includes 1 Agent Skills capability.\n"
            "skills:\n"
            "  - software-development/ada-example\n",
            encoding="utf-8",
        )
        (root / "README.md").write_text(
            "当前版本：`1.0.0`\n\n"
            "## 技能体系 (1 skills)\n\n"
            "- `ada-example`\n",
            encoding="utf-8",
        )
        return root

    def test_valid_distribution_passes(self) -> None:
        result = VALIDATOR.validate(self.make_distribution())
        self.assertEqual([], result.errors)

    def test_unknown_local_skill_reference_fails(self) -> None:
        root = self.make_distribution()
        skill = root / "skills" / "software-development" / "ada-example" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "Use ada-does-not-exist.\n", encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("references unknown local Ada skill" in error for error in result.errors))

    def test_manifest_and_readme_catalog_mismatch_fails(self) -> None:
        root = self.make_distribution()
        (root / "distribution.yaml").write_text(
            "name: ada\n"
            "version: 1.0.0\n"
            "description: Includes 1 Agent Skills capability.\n"
            "skills:\n"
            "  - software-development/ada-missing\n",
            encoding="utf-8",
        )

        result = VALIDATOR.validate(root)

        self.assertTrue(any("declares missing skill" in error for error in result.errors))
        self.assertTrue(any("not declared" in error for error in result.errors))

    def test_private_runtime_state_fails(self) -> None:
        root = self.make_distribution()
        (root / "memories").mkdir()
        (root / "memories" / "MEMORY.md").write_text("private", encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("private runtime state" in error for error in result.errors))

    def test_duplicate_eval_id_fails(self) -> None:
        root = self.make_distribution()
        evals_dir = root / "skills" / "software-development" / "ada-example" / "evals"
        evals_dir.mkdir()
        case = {
            "id": 1,
            "prompt": "Example",
            "should_trigger": True,
            "expected_output": "Runs the example workflow.",
            "assertions": ["Identifies the example."],
        }
        (evals_dir / "evals.json").write_text(
            json.dumps({"skill_name": "ada-example", "evals": [case, case]}),
            encoding="utf-8",
        )

        result = VALIDATOR.validate(root)

        self.assertTrue(any("duplicate eval id" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
