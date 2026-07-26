"""Validate Ada skill metadata and local references.

This is intentionally lightweight: it checks the Agent Skills constraints that
matter most before deeper qualitative review.
"""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills" / "software-development"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESOURCE_LINK_RE = re.compile(r"`((?:references|assets|evals)/[^`]+)`")


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    if not lines or lines[0].strip() != "---":
        return {}, ["missing opening frontmatter fence"]
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        return {}, ["missing closing frontmatter fence"]

    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip().strip("'\"")
    return fields, errors


def check_skill(path: Path) -> list[str]:
    errors: list[str] = []
    skill_dir = path.parent
    fields, fm_errors = parse_frontmatter(path)
    errors.extend(fm_errors)

    name = fields.get("name")
    desc = fields.get("description")

    if not name:
        errors.append("missing required field: name")
    elif name != skill_dir.name:
        errors.append(f"name {name!r} does not match directory {skill_dir.name!r}")
    elif not NAME_RE.match(name):
        errors.append(f"name {name!r} is not Agent Skills compatible")

    if not desc:
        errors.append("missing required field: description")
    elif len(desc) > 1024:
        errors.append(f"description exceeds 1024 chars ({len(desc)})")

    text = path.read_text(encoding="utf-8")
    for rel in RESOURCE_LINK_RE.findall(text):
        if any(marker in rel for marker in ("*", "<", ">")):
            continue
        rel_path = rel.split("#", 1)[0]
        target = skill_dir / rel_path
        if not target.exists():
            errors.append(f"missing local resource link: {rel}")

    evals_path = skill_dir / "evals" / "evals.json"
    if evals_path.exists():
        try:
            data = json.loads(evals_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid evals/evals.json: {exc}")
        else:
            if data.get("skill_name") != skill_dir.name:
                errors.append("evals/evals.json skill_name does not match directory")
            evals = data.get("evals")
            if not isinstance(evals, list) or not evals:
                errors.append("evals/evals.json must contain a non-empty evals list")
            elif evals:
                for index, item in enumerate(evals):
                    if not isinstance(item, dict):
                        errors.append(f"evals/evals.json eval {index} must be an object")
                        continue
                    for field in ("id", "prompt", "expected_output"):
                        if not item.get(field):
                            errors.append(f"evals/evals.json eval {index} missing {field}")
                    if not isinstance(item.get("should_trigger"), bool):
                        errors.append(
                            f"evals/evals.json eval {index} missing boolean should_trigger"
                        )
                    assertions = item.get("assertions")
                    if not isinstance(assertions, list) or not assertions:
                        errors.append(
                            f"evals/evals.json eval {index} must include assertions"
                        )

    return errors


def main() -> int:
    failures: list[tuple[Path, list[str]]] = []
    for path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        errors = check_skill(path)
        if errors:
            failures.append((path, errors))

    if failures:
        for path, errors in failures:
            rel = path.relative_to(ROOT)
            for error in errors:
                print(f"{rel}: {error}")
        return 1

    print("All Ada skills pass lightweight metadata and local-link validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
