from __future__ import annotations

import hashlib
import json
from pathlib import Path

from conftest import ROOT, kit, run_kit


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ready_source(project_id: str, page_id: str) -> None:
    source = kit(
        "new-source", project_id, page_id,
        "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2",
    )
    root = Path(str(source["root"]))
    write(root / "spec" / "spec.json", json.dumps({
        "version": 1, "page": {},
        "variants": [{"id": "desktop", "label": "desktop", "reference": "desktop.png"}],
        "sections": [{"id": "hero"}],
    }))
    write(root / "spec" / "content-inventory.json", json.dumps({"version": 1, "items": []}))
    write(root / "asset-manifest.json", json.dumps({"version": 1, "assets": []}))
    (root / "reference").mkdir(parents=True, exist_ok=True)
    (root / "reference" / "desktop.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    kit("source-ready", project_id, page_id, "source-001")


def test_new_run_records_a_real_guideline_snapshot(project_factory) -> None:
    project_id, page_id = "guideline-snapshot-test", "home"
    project_root = project_factory(project_id)
    kit("init-project", project_id, "Guideline snapshot test", "--platform", "html5")
    kit("init-page", project_id, page_id, "Home")
    write(project_root / "guidelines" / "brand.md", "# Brand\n\n- Use the brand teal.\n")
    write(project_root / "pages" / page_id / "guidelines" / "scope.md", "# Scope\n\n- Desktop only.\n")
    ready_source(project_id, page_id)

    run = kit("new-run", project_id, page_id, "--source", "source-001")
    run_root = Path(str(run["root"]))
    snapshot = (run_root / "effective-guidelines.md").read_text(encoding="utf-8")
    recorded = json.loads((run_root / "run.json").read_text(encoding="utf-8"))["guidelineSnapshot"]

    # The snapshot is real content, not the former stub.
    assert len(snapshot) > 1000
    assert recorded["sha256"] == hashlib.sha256(snapshot.encode()).hexdigest()

    paths = [entry["path"] for entry in recorded["sources"]]
    assert paths[0] == "guidelines/global/general-rules.md"
    assert "guidelines/builder.md" in paths
    assert paths[-2:] == [
        f"projects/{project_id}/guidelines/brand.md",
        f"projects/{project_id}/pages/{page_id}/guidelines/scope.md",
    ]
    assert all(entry["sha256"] for entry in recorded["sources"])

    # Precedence order must survive into the rendered document.
    assert snapshot.index("Use the brand teal") < snapshot.index("Desktop only")
    assert snapshot.index("guidelines/global/general-rules.md") < snapshot.index("Use the brand teal")


def test_snapshot_hashes_track_guideline_edits(project_factory) -> None:
    project_id, page_id = "guideline-snapshot-hash-test", "home"
    project_root = project_factory(project_id)
    kit("init-project", project_id, "Guideline hash test", "--platform", "html5")
    kit("init-page", project_id, page_id, "Home")
    write(project_root / "guidelines" / "brand.md", "# Brand\n\n- Original rule.\n")
    ready_source(project_id, page_id)
    first = kit("new-run", project_id, page_id, "--source", "source-001")
    before = json.loads((Path(str(first["root"])) / "run.json").read_text(encoding="utf-8"))

    write(project_root / "guidelines" / "brand.md", "# Brand\n\n- Revised rule.\n")
    second = kit("new-run", project_id, page_id, "--source", "source-001")
    after = json.loads((Path(str(second["root"])) / "run.json").read_text(encoding="utf-8"))

    assert before["guidelineSnapshot"]["sha256"] != after["guidelineSnapshot"]["sha256"]
    changed = next(e for e in after["guidelineSnapshot"]["sources"] if e["path"].endswith("brand.md"))
    original = next(e for e in before["guidelineSnapshot"]["sources"] if e["path"].endswith("brand.md"))
    assert changed["sha256"] != original["sha256"]


def sections(snapshot: str) -> list[str]:
    return [line[3:].strip() for line in snapshot.splitlines() if line.startswith("## guidelines/")]


def test_role_scoped_read_returns_the_role_file_and_the_platform_bundle(project_factory) -> None:
    project_id, page_id = "guideline-role-test", "home"
    project_root = project_factory(project_id)
    kit("init-project", project_id, "Role scope test", "--platform", "html5")
    kit("init-page", project_id, page_id, "Home")
    write(project_root / "guidelines" / "brand.md", "# Brand\n\n- Use the brand teal.\n")

    builder = run_kit("guidelines", project_id, page_id, "--role", "builder").stdout
    technical = run_kit("guidelines", project_id, page_id, "--role", "technical").stdout
    everything = run_kit("guidelines", project_id, page_id).stdout

    # A role gets its own file plus the channel-agnostic baseline and the
    # channel's own delta bundle, never another role's file or another
    # channel's delta. general-rules.md names the channel folders by path, so
    # omitting them would leave the agent unable to reach the delta at all.
    assert sections(builder) == [
        "guidelines/global/general-rules.md",
        "guidelines/builder.md",
        "guidelines/global/coding/assets-media.md",
        "guidelines/global/coding/base-css-template.md",
        "guidelines/global/coding/css.md",
        "guidelines/global/coding/html.md",
        "guidelines/m3/general-rules.md",
        "guidelines/m3/coding/html5-delta.md",
    ]
    assert sections(technical) == [
        "guidelines/global/general-rules.md",
        "guidelines/global/qa/technical-qa.md",
        "guidelines/global/coding/assets-media.md",
        "guidelines/global/coding/base-css-template.md",
        "guidelines/global/coding/css.md",
        "guidelines/global/coding/html.md",
        "guidelines/m3/general-rules.md",
        "guidelines/m3/coding/html5-delta.md",
        "guidelines/m3/qa/qa-findings-reference.md",
    ]
    # Global, project, and page layers are present for every role.
    for scoped in (builder, technical):
        assert "Use the brand teal" in scoped
        assert len(scoped) < len(everything)
    # The unscoped read stays the complete archival record.
    for path in (
        "guidelines/builder.md",
        "guidelines/extractor.md",
        "guidelines/global/qa/ui-qa.md",
        "guidelines/global/qa/content-qa.md",
        "guidelines/global/qa/accessibility-qa.md",
        "guidelines/global/qa/technical-qa.md",
    ):
        assert path in everything


def test_medichannel_delivers_xhtml_rules_and_the_qa_guide_to_qa_roles(project_factory) -> None:
    project_id, page_id = "guideline-platform-test", "home"
    project_factory(project_id)
    kit("init-project", project_id, "Platform test", "--platform", "medichannel")
    kit("init-page", project_id, page_id, "Home", "--article-path", "medical/product/example-contents/example_article01")

    builder = sections(run_kit("guidelines", project_id, page_id, "--role", "builder").stdout)
    ui = sections(run_kit("guidelines", project_id, page_id, "--role", "ui").stdout)

    xhtml = {
        "guidelines/medichannel/general-rules.md",
        "guidelines/medichannel/coding/xhtml-syntax.md",
        "guidelines/medichannel/coding/deviations.md",
        "guidelines/medichannel/coding/design-token-consistency.md",
        "guidelines/medichannel/coding/xhtml-vs-html5-reference.md",
    }
    assert xhtml <= set(builder) and xhtml <= set(ui)
    # The QA workflow file goes to reviewers, not to the builder.
    assert "guidelines/medichannel/qa/coding-qa.md" in ui
    assert "guidelines/medichannel/qa/coding-qa.md" not in builder
    # HTML5's channel-specific delta must never leak into a MediChannel build.
    assert "guidelines/m3/coding/html5-delta.md" not in builder


def test_a_run_cannot_start_without_a_platform(project_factory) -> None:
    project_id, page_id = "guideline-no-platform-test", "home"
    project_factory(project_id)
    kit("init-project", project_id, "No platform test")
    kit("init-page", project_id, page_id, "Home")
    ready_source(project_id, page_id)

    result = run_kit("new-run", project_id, page_id, "--source", "source-001", check=False)

    assert result.returncode != 0
    assert "has no platform" in result.stderr
    # A role-scoped read still works, but says plainly what is missing.
    scoped = run_kit("guidelines", project_id, page_id, "--role", "builder").stdout
    assert "no platform is set" in scoped
    assert sections(scoped) == ["guidelines/global/general-rules.md", "guidelines/builder.md"]


def test_unknown_role_is_rejected(project_factory) -> None:
    project_id, page_id = "guideline-bad-role-test", "home"
    project_factory(project_id)
    kit("init-project", project_id, "Bad role test", "--platform", "html5")
    kit("init-page", project_id, page_id, "Home")

    result = run_kit("guidelines", project_id, page_id, "--role", "nonsense", check=False)

    assert result.returncode != 0
    assert "Unknown role" in result.stderr


def test_run_snapshot_stays_unscoped(project_factory) -> None:
    project_id, page_id = "guideline-archival-test", "home"
    project_factory(project_id)
    kit("init-project", project_id, "Archival test", "--platform", "html5")
    kit("init-page", project_id, page_id, "Home")
    ready_source(project_id, page_id)

    run = kit("new-run", project_id, page_id, "--source", "source-001")
    paths = [e["path"] for e in json.loads(
        (Path(str(run["root"])) / "run.json").read_text(encoding="utf-8")
    )["guidelineSnapshot"]["sources"]]

    # A run records every role's and every channel's guidelines, so release
    # evidence stays complete regardless of which platform the project targets.
    base = [p for p in paths if p.startswith("guidelines/")]
    gr = "guidelines/global/general-rules.md"
    rest = sorted(
        p.relative_to(ROOT).as_posix() for p in (ROOT / "guidelines").rglob("*.md")
        if p.relative_to(ROOT).as_posix() != gr
    )
    assert base == [gr] + rest


def test_global_guidelines_are_always_first(project_factory) -> None:
    project_id, page_id = "guideline-precedence-test", "home"
    project_factory(project_id)
    kit("init-project", project_id, "Precedence test", "--platform", "html5")
    kit("init-page", project_id, page_id, "Home")
    ready_source(project_id, page_id)

    run = kit("new-run", project_id, page_id, "--source", "source-001")
    paths = [e["path"] for e in json.loads(
        (Path(str(run["root"])) / "run.json").read_text(encoding="utf-8")
    )["guidelineSnapshot"]["sources"]]

    assert paths[0] == "guidelines/global/general-rules.md"
    assert paths[1:] == sorted(paths[1:])  # channel files resolve deterministically
    assert (ROOT / paths[0]).exists()
