from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "scripts" / "kit.py"


def run_kit(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(KIT), *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        # kit.py emits UTF-8; guideline documents contain characters a cp1252
        # locale cannot decode, and the default would silently yield None stdout.
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


def kit(*args: str) -> dict[str, object]:
    return json.loads(run_kit(*args).stdout)


@pytest.fixture
def project_factory():
    project_ids: list[str] = []
    # kit.py records run state outside projects/, so dropping the project tree is
    # not enough: a leftover marker makes the SubagentStop hook attribute the next
    # subagent's token usage to a deleted test project.
    active = ROOT / ".claude" / "state" / "active-run.json"
    saved = active.read_text(encoding="utf-8") if active.exists() else None

    def create(project_id: str) -> Path:
        project_ids.append(project_id)
        return ROOT / "projects" / project_id

    yield create

    for project_id in project_ids:
        shutil.rmtree(ROOT / "projects" / project_id, ignore_errors=True)
    if saved is None:
        active.unlink(missing_ok=True)
    else:
        active.write_text(saved, encoding="utf-8")
