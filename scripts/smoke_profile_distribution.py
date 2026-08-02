"""Run an isolated Hermes Profile install/update smoke test for Ada.

The script points HERMES_HOME at a temporary directory, installs a temporary
copy of this repository, mutates only that copy, updates it, and verifies that
user-owned state survives while distribution-owned content changes.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SMOKE_PROFILE = "ada-distribution-smoke"


def run_hermes(args: list[str], env: dict[str, str]) -> None:
    process = subprocess.run(
        ["hermes", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode:
        raise RuntimeError(
            f"hermes {' '.join(args)} failed ({process.returncode})\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )


def next_patch(version: str) -> str:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"smoke test requires a numeric semver, got {version!r}")
    major, minor, patch = (int(value) for value in match.groups())
    return f"{major}.{minor}.{patch + 1}"


def main() -> int:
    if shutil.which("hermes") is None:
        raise RuntimeError("hermes CLI is required for the distribution smoke test")

    with tempfile.TemporaryDirectory(prefix="ada-profile-smoke-") as temp_name:
        temp = Path(temp_name)
        source = temp / "source"
        hermes_home = temp / "hermes"
        shutil.copytree(
            ROOT,
            source,
            ignore=shutil.ignore_patterns(".git", ".hermes", "__pycache__", "*.pyc"),
        )
        hermes_home.mkdir()
        env = os.environ.copy()
        env["HERMES_HOME"] = str(hermes_home)

        source_manifest_path = source / "distribution.yaml"
        source_manifest = yaml.safe_load(source_manifest_path.read_text(encoding="utf-8"))
        expected_skill_count = len(source_manifest["skills"])
        initial_version = str(source_manifest["version"])
        updated_version = next_patch(initial_version)

        run_hermes(
            ["profile", "install", str(source), "--name", SMOKE_PROFILE, "--yes"],
            env,
        )
        profile = hermes_home / "profiles" / SMOKE_PROFILE
        installed_skills = list(profile.glob("skills/**/SKILL.md"))
        if len(installed_skills) != expected_skill_count:
            raise AssertionError(
                f"installed {len(installed_skills)} Skills; expected {expected_skill_count}"
            )
        for forbidden in ("auth.json", ".env", "state.db", "state.db-wal", "state.db-shm"):
            if (profile / forbidden).exists():
                raise AssertionError(f"private file unexpectedly installed: {forbidden}")

        user_markers = {
            "memories/SMOKE.md": "keep-memory",
            "sessions/SMOKE.txt": "keep-session",
            "local/SMOKE.txt": "keep-local",
        }
        for relative, content in user_markers.items():
            marker = profile / relative
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(content, encoding="utf-8")

        manifest_text = source_manifest_path.read_text(encoding="utf-8")
        source_manifest_path.write_text(
            manifest_text.replace(
                f"version: {initial_version}",
                f"version: {updated_version}",
                1,
            ),
            encoding="utf-8",
        )
        owned_marker = (
            source
            / "skills"
            / "software-development"
            / "ada-business-document-authoring"
            / "SMOKE_UPDATE.txt"
        )
        owned_marker.write_text("updated", encoding="utf-8")

        run_hermes(["profile", "update", SMOKE_PROFILE, "--yes"], env)

        installed_manifest = yaml.safe_load(
            (profile / "distribution.yaml").read_text(encoding="utf-8")
        )
        if str(installed_manifest["version"]) != updated_version:
            raise AssertionError("distribution manifest was not updated")
        if (profile / owned_marker.relative_to(source)).read_text(encoding="utf-8") != "updated":
            raise AssertionError("distribution-owned Skill content was not updated")
        for relative, content in user_markers.items():
            if (profile / relative).read_text(encoding="utf-8") != content:
                raise AssertionError(f"user-owned state was not preserved: {relative}")

        print(
            "Ada Profile distribution smoke test passed: "
            f"install/update, {expected_skill_count} Skills, user state preserved."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
