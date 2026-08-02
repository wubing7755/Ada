"""Regression tests for the Ada distribution validator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
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

    def test_invalid_manifest_yaml_fails(self) -> None:
        root = self.make_distribution()
        manifest = root / "distribution.yaml"
        manifest.write_text(manifest.read_text(encoding="utf-8") + "bad: [\n", encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("invalid YAML" in error for error in result.errors))

    def test_duplicate_manifest_yaml_key_fails(self) -> None:
        root = self.make_distribution()
        manifest = root / "distribution.yaml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8") + "name: duplicate\n",
            encoding="utf-8",
        )

        result = VALIDATOR.validate(root)

        self.assertTrue(any("duplicate YAML key" in error for error in result.errors))

    def test_invalid_frontmatter_yaml_fails(self) -> None:
        root = self.make_distribution()
        skill = root / "skills" / "software-development" / "ada-example" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8").replace("version: 1.0.0", "metadata: ["), encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("invalid YAML frontmatter" in error for error in result.errors))

    def test_duplicate_frontmatter_yaml_key_fails(self) -> None:
        root = self.make_distribution()
        skill = root / "skills" / "software-development" / "ada-example" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        skill.write_text(text.replace("name: ada-example\n", "name: ada-example\nname: duplicate\n"), encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("duplicate YAML key" in error for error in result.errors))

    def test_frontmatter_fence_must_start_at_first_character(self) -> None:
        root = self.make_distribution()
        skill = root / "skills" / "software-development" / "ada-example" / "SKILL.md"
        skill.write_text(" " + skill.read_text(encoding="utf-8"), encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("missing opening frontmatter fence" in error for error in result.errors))

    def test_empty_skill_body_fails(self) -> None:
        root = self.make_distribution()
        skill = root / "skills" / "software-development" / "ada-example" / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        skill.write_text(text[: text.rfind("---") + 3] + "\n", encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("body is empty" in error for error in result.errors))

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

    def test_workspace_runtime_state_fails(self) -> None:
        root = self.make_distribution()
        (root / "workspace").mkdir()
        (root / "workspace" / "private.md").write_text("private", encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("private runtime state" in error for error in result.errors))

    def test_gitignored_runtime_cache_does_not_false_positive(self) -> None:
        root = self.make_distribution()
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        (root / ".gitignore").write_text("cache/\n", encoding="utf-8")
        (root / "cache").mkdir()
        (root / "cache" / "private.bin").write_bytes(b"private")

        result = VALIDATOR.validate(root)

        self.assertEqual([], result.errors)

    def test_duplicate_eval_id_fails(self) -> None:
        root = self.make_distribution()
        evals_dir = root / "skills" / "software-development" / "ada-example" / "evals"
        evals_dir.mkdir()
        case = {
            "id": 1,
            "prompt": "Example",
            "should_trigger": True,
            "expected_output": "Runs the example workflow.",
            "assertions": ["Identifies the example.", "Runs the example workflow."],
        }
        (evals_dir / "evals.json").write_text(
            json.dumps({"skill_name": "ada-example", "evals": [case, case]}),
            encoding="utf-8",
        )

        result = VALIDATOR.validate(root)

        self.assertTrue(any("duplicate eval id" in error for error in result.errors))

    def test_eval_top_level_must_be_object(self) -> None:
        root = self.make_distribution()
        evals_dir = root / "skills" / "software-development" / "ada-example" / "evals"
        evals_dir.mkdir()
        (evals_dir / "evals.json").write_text("[]\n", encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("top level must be an object" in error for error in result.errors))

    def test_eval_id_must_be_hashable_scalar(self) -> None:
        root = self.make_distribution()
        evals_dir = root / "skills" / "software-development" / "ada-example" / "evals"
        evals_dir.mkdir()
        case = {
            "id": ["not", "hashable"],
            "prompt": "Example",
            "should_trigger": True,
            "expected_output": "Runs the example workflow.",
            "assertions": ["Identifies the example.", "Runs the workflow."],
        }
        (evals_dir / "evals.json").write_text(
            json.dumps({"skill_name": "ada-example", "evals": [case]}),
            encoding="utf-8",
        )

        result = VALIDATOR.validate(root)

        self.assertTrue(any("id must be a non-empty string or integer" in error for error in result.errors))

    def test_eval_text_fields_and_assertion_count_are_validated(self) -> None:
        root = self.make_distribution()
        evals_dir = root / "skills" / "software-development" / "ada-example" / "evals"
        evals_dir.mkdir()
        case = {
            "id": 1,
            "prompt": 123,
            "should_trigger": True,
            "expected_output": "Runs the example workflow.",
            "assertions": ["Only one assertion"],
        }
        (evals_dir / "evals.json").write_text(
            json.dumps({"skill_name": "ada-example", "evals": [case]}),
            encoding="utf-8",
        )

        result = VALIDATOR.validate(root)

        self.assertTrue(any("prompt must be a non-empty string" in error for error in result.errors))
        self.assertTrue(any("at least 2 output-quality assertions" in warning for warning in result.warnings))

    def test_missing_skill_owned_script_link_fails(self) -> None:
        root = self.make_distribution()
        skill_dir = root / "skills" / "software-development" / "ada-example"
        (skill_dir / "scripts").mkdir()
        skill = skill_dir / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "Run [checker](scripts/missing.py).\n", encoding="utf-8")

        result = VALIDATOR.validate(root)

        self.assertTrue(any("missing local resource link" in error for error in result.errors))

    def test_missing_markdown_template_link_fails_without_resource_directory(self) -> None:
        root = self.make_distribution()
        skill = root / "skills" / "software-development" / "ada-example" / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8")
            + "The target project uses `templates/missing.md`.\n"
            + "Use [template](templates/missing.md).\n",
            encoding="utf-8",
        )

        result = VALIDATOR.validate(root)

        self.assertTrue(any("missing local resource link" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
