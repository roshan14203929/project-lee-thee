"""The QA gate numbers exist in three places on purpose, and must agree.

`visual-diff.py` holds the executable defaults, `references/orchestration.py`-side
prose is what the orchestrator acts on, and `guidelines/global/orchestrator.md`
records them as release evidence (it reaches no role, so it cannot simply cite the
skill). Three copies with three real consumers is not duplication to delete — but
it is drift waiting to happen, so pin it.
"""
from __future__ import annotations

import re

from conftest import ROOT

GUIDE = ROOT / "guidelines" / "global" / "orchestrator.md"
ORCH = ROOT / ".claude" / "skills" / "build-figma-page" / "references" / "orchestration.md"
DIFF = ROOT / "scripts" / "visual-diff.py"
KIT = ROOT / "scripts" / "kit.py"


def _text(p) -> str:
    return p.read_text(encoding="utf-8")


def test_visual_diff_defaults_match_the_recorded_gates() -> None:
    diff = _text(DIFF)
    full = re.search(r'args\.get\("threshold",\s*"(\d+(?:\.\d+)?)"\)', diff)
    peak = re.search(r'args\.get\("peak-threshold",\s*"(\d+(?:\.\d+)?)"\)', diff)
    assert full and peak, "visual-diff.py no longer exposes parseable threshold defaults"

    guide = _text(GUIDE)
    assert f"Full-page maximum pixel difference: {full.group(1)}%." in guide
    assert f"Maximum localized horizontal-band difference: {peak.group(1)}%." in guide


def test_repair_cap_matches_the_run_record() -> None:
    cap = re.search(r"'maxRounds':\s*(\d+)", _text(KIT))
    assert cap, "kit.py no longer sets maxRounds on the run record"
    assert f"Maximum automatic repair rounds: {cap.group(1)}." in _text(GUIDE)


def test_regression_tolerances_agree_between_skill_and_guidelines() -> None:
    # These two have no code authority, so prose is the only guard.
    guide, orch = _text(GUIDE), _text(ORCH)
    assert "Candidate regression tolerance: 0.10 percentage points." in guide
    assert "0.10 percentage points" in orch
    assert "0.20 percentage" in guide and "0.20 points" in orch
