"""Validate Ada's distributable skill catalog and Profile boundary.

The validator intentionally uses only the Python standard library so it can run
before Profile installation. It checks manifest/catalog consistency, Agent
Skills metadata, local links, local Ada-skill references, eval structure, and
common private-state leaks.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
MANIFEST_PATH = ROOT / "distribution.yaml"
README_PATH = ROOT / "README.md"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_SKILL_REF_RE = re.compile(r"(?<![a-z0-9-])(ada-[a-z0-9]+(?:-[a-z0-9]+)*)(?![a-z0-9-])")
RESOURCE_LINK_RES = (
    re.compile(r"`((?:references|assets|evals)/[^`]+)`"),
    re.compile(r"\]\(((?:references|assets|evals)/[^)]+)\)"),
)
PRIVATE_NAMES = {
    ".env",
    "auth.json",
    "memories",
    "sessions",
    "state.db",
    "logs",
    "cache",
}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, path: Path | str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def warn(self, path: Path | str, message: str) -> None:
        self.warnings.append(f"{path}: {message}")


def relative(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
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
    return fields, []


def parse_manifest_skills(path: Path) -> list[str]:
    skills: list[str] = []
    in_skills = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line == "skills:":
            in_skills = True
            continue
        if in_skills and line and not line[0].isspace():
            break
        if in_skills:
            match = re.match(r"^\s+-\s+([^#\s]+)\s*$", line)
            if match:
                skills.append(match.group(1))
    return skills


def manifest_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*['\"]?([^'\"\n]+)['\"]?\s*$", text)
    return match.group(1).strip() if match else None


def check_resource_links(path: Path, result: ValidationResult, root: Path) -> None:
    text = path.read_text(encoding="utf-8")
    skill_dir = path.parent
    seen: set[str] = set()
    for pattern in RESOURCE_LINK_RES:
        for rel in pattern.findall(text):
            if rel in seen or any(marker in rel for marker in ("*", "<", ">")):
                continue
            seen.add(rel)
            rel_path = rel.split("#", 1)[0]
            target = (skill_dir / rel_path).resolve()
            try:
                target.relative_to(skill_dir.resolve())
            except ValueError:
                result.error(relative(path, root), f"local resource escapes skill directory: {rel}")
                continue
            if not target.exists():
                result.error(relative(path, root), f"missing local resource link: {rel}")


def check_evals(path: Path, result: ValidationResult, root: Path) -> None:
    evals_path = path.parent / "evals" / "evals.json"
    if not evals_path.exists():
        return
    rel = relative(evals_path, root)
    try:
        data = json.loads(evals_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.error(rel, f"invalid JSON: {exc}")
        return
    if data.get("skill_name") != path.parent.name:
        result.error(rel, "skill_name does not match directory")
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        result.error(rel, "must contain a non-empty evals list")
        return

    ids: set[object] = set()
    trigger_count = 0
    reject_count = 0
    for index, item in enumerate(evals):
        if not isinstance(item, dict):
            result.error(rel, f"eval {index} must be an object")
            continue
        for field_name in ("id", "prompt", "expected_output"):
            if not item.get(field_name):
                result.error(rel, f"eval {index} missing {field_name}")
        eval_id = item.get("id")
        if eval_id in ids:
            result.error(rel, f"duplicate eval id: {eval_id!r}")
        ids.add(eval_id)
        should_trigger = item.get("should_trigger")
        if not isinstance(should_trigger, bool):
            result.error(rel, f"eval {index} missing boolean should_trigger")
        elif should_trigger:
            trigger_count += 1
        else:
            reject_count += 1
        assertions = item.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            result.error(rel, f"eval {index} must include assertions")
        elif any(not isinstance(assertion, str) or not assertion.strip() for assertion in assertions):
            result.error(rel, f"eval {index} assertions must be non-empty strings")

    if trigger_count < 4 or reject_count < 4:
        result.warn(
            rel,
            "recommended high-value eval set is at least 4 should-trigger and 4 should-not-trigger cases "
            f"(found {trigger_count}/{reject_count})",
        )


def check_skill(path: Path, all_names: set[str], result: ValidationResult, root: Path) -> None:
    rel = relative(path, root)
    fields, frontmatter_errors = parse_frontmatter(path)
    for error in frontmatter_errors:
        result.error(rel, error)

    name = fields.get("name")
    description = fields.get("description")
    if not name:
        result.error(rel, "missing required field: name")
    elif name != path.parent.name:
        result.error(rel, f"name {name!r} does not match directory {path.parent.name!r}")
    elif not NAME_RE.fullmatch(name):
        result.error(rel, f"name {name!r} is not Agent Skills compatible")
    elif not name.startswith("ada-"):
        result.error(rel, "distributed Ada-owned skill must use the ada- prefix")

    if not description:
        result.error(rel, "missing required field: description")
    elif len(description) > 1024:
        result.error(rel, f"description exceeds 1024 chars ({len(description)})")

    line_count = len(path.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        result.error(rel, f"SKILL.md exceeds 500-line progressive-disclosure limit ({line_count})")

    check_resource_links(path, result, root)
    check_evals(path, result, root)

    references = set(LOCAL_SKILL_REF_RE.findall(path.read_text(encoding="utf-8")))
    for reference in sorted(references - all_names):
        result.error(rel, f"references unknown local Ada skill: {reference}")


def check_private_state(root: Path, result: ValidationResult) -> None:
    for path in root.rglob("*"):
        if ".git" in path.parts or ".hermes" in path.parts:
            continue
        lowered = {part.lower() for part in path.relative_to(root).parts}
        if lowered & PRIVATE_NAMES or any(part.startswith("state.db") for part in lowered):
            result.error(relative(path, root), "private runtime state must not be distributed")


def validate(root: Path = ROOT) -> ValidationResult:
    result = ValidationResult()
    skills_root = root / "skills"
    manifest_path = root / "distribution.yaml"
    readme_path = root / "README.md"
    skill_paths = sorted(skills_root.glob("**/SKILL.md"))
    skill_names = {path.parent.name for path in skill_paths}

    if not manifest_path.exists():
        result.error("distribution.yaml", "missing Profile distribution manifest")
        return result
    if not readme_path.exists():
        result.error("README.md", "missing distribution README")
        return result

    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_skills = parse_manifest_skills(manifest_path)
    if len(manifest_skills) != len(set(manifest_skills)):
        result.error("distribution.yaml", "contains duplicate skill entries")
    declared_paths = {f"skills/{entry}/SKILL.md" for entry in manifest_skills}
    actual_paths = {path.relative_to(root).as_posix() for path in skill_paths}
    for missing in sorted(declared_paths - actual_paths):
        result.error("distribution.yaml", f"declares missing skill: {missing}")
    for undeclared in sorted(actual_paths - declared_paths):
        result.error(undeclared, "skill is not declared in distribution.yaml")

    readme_text = readme_path.read_text(encoding="utf-8")
    readme_names = set(re.findall(r"`(ada-[a-z0-9]+(?:-[a-z0-9]+)*)`", readme_text))
    for missing in sorted(skill_names - readme_names):
        result.error("README.md", f"catalog omits distributed skill: {missing}")
    for unknown in sorted(readme_names - skill_names):
        result.error("README.md", f"catalog references unknown Ada skill: {unknown}")

    readme_count = re.search(r"技能体系\s*\((\d+)\s+skills\)", readme_text)
    if not readme_count or int(readme_count.group(1)) != len(skill_paths):
        result.error("README.md", f"skill count must equal actual catalog size {len(skill_paths)}")
    description_count = re.search(r"Includes\s+(\d+)\s+Agent Skills", manifest_text)
    if not description_count or int(description_count.group(1)) != len(skill_paths):
        result.error("distribution.yaml", f"description skill count must equal {len(skill_paths)}")

    manifest_version = manifest_scalar(manifest_text, "version")
    readme_version = re.search(r"当前版本：`([^`]+)`", readme_text)
    if not readme_version or readme_version.group(1) != manifest_version:
        result.error("README.md", "version does not match distribution.yaml")

    for path in skill_paths:
        check_skill(path, skill_names, result, root)
    check_private_state(root, result)
    return result


def main() -> int:
    result = validate()
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(error)
    if result.errors:
        print(f"Validation failed with {len(result.errors)} error(s).")
        return 1
    print(
        f"Ada distribution validation passed: "
        f"{len(list(SKILLS_ROOT.glob('**/SKILL.md')))} skills, "
        f"{len(result.warnings)} eval recommendation warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())