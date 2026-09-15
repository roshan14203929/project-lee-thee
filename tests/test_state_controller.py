from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from conftest import kit, run_kit


def write_json(path: Path, value: object) -> None:
    path.write_text(f"{json.dumps(value, indent=2)}\n", encoding="utf-8")


def test_state_controller_creates_an_immutable_released_run(project_factory) -> None:
    project_id, page_id = "state-controller-test", "home"
    project_factory(project_id)
    kit("init-project", project_id, "State controller test", "--platform", "html5")
    kit("init-page", project_id, page_id, "Home")
    source = kit(
        "new-source", project_id, page_id,
        "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2",
        "--variant", "mobile=https://www.figma.com/design/example?node-id=2-3",
    )
    source_root = Path(str(source["root"]))
    write_json(source_root / "spec" / "spec.json", {
        "version": 1,
        "page": {"name": "Home", "language": "en"},
        "variants": [
            {"id": "desktop", "width": 1440, "height": 900, "reference": "desktop.png"},
            {"id": "mobile", "width": 375, "height": 812, "reference": "mobile.png"},
        ],
        "tokens": {}, "sections": [{"id": "main"}], "assets": [], "openQuestions": [],
    })
    write_json(source_root / "spec" / "content-inventory.json", {
        "version": 1,
        "items": [{"id": "title", "kind": "heading", "text": "Hello", "required": True, "nodeId": "1:3", "sectionId": "main"}],
    })
    write_json(source_root / "asset-manifest.json", {"assets": []})
    (source_root / "reference" / "desktop.png").write_text("test", encoding="utf-8")
    (source_root / "reference" / "mobile.png").write_text("test", encoding="utf-8")
    kit("source-ready", project_id, page_id, str(source["sourceId"]))

    run = kit("new-run", project_id, page_id, "--source", str(source["sourceId"]))
    kit("transition", project_id, page_id, str(run["runId"]), "BUILDING")
    candidate = kit("new-candidate", project_id, page_id, str(run["runId"]), "--round", "0")
    candidate_root = Path(str(candidate["root"]))
    (candidate_root / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width"><title>Home</title><link rel="stylesheet" href="base.css"><link rel="stylesheet" href="page.css"></head><body><main><h1>Hello</h1></main></body></html>',
        encoding="utf-8",
    )
    (candidate_root / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (candidate_root / "page.css").write_text("main{display:block}", encoding="utf-8")
    (candidate_root / "images").mkdir(exist_ok=True)

    run_root = Path(str(run["root"]))
    static_report, browser_report, visual_report = (run_root / "static-input.json", run_root / "browser-input.json", run_root / "visual-input.json")
    write_json(static_report, {"status": "PASS"})
    write_json(browser_report, {"status": "PASS"})
    write_json(visual_report, {"status": "PASS", "pixelDifferencePercent": 0, "peakBandDifferencePercent": 0})
    kit("candidate-result", project_id, page_id, str(run["runId"]), str(candidate["candidateId"]), "--status", "accepted", "--static", str(static_report), "--browser", str(browser_report), "--metrics", str(visual_report))
    kit("transition", project_id, page_id, str(run["runId"]), "VERIFYING")

    checked_at = datetime.now(timezone.utc).isoformat()
    invalid_ui = run_root / "ui-missing-provenance.json"
    write_json(invalid_ui, {"kind": "ui", "status": "PASS", "checkedAt": checked_at, "summary": "Passed", "findings": []})
    invalid_result = run_kit("qa-record", project_id, page_id, str(run["runId"]), "ui", "--file", str(invalid_ui), check=False)
    assert invalid_result.returncode != 0
    assert "provenance" in invalid_result.stderr.lower()

    for kind in ("content", "ui", "accessibility", "technical"):
        report = run_root / f"{kind}-input.json"
        qa: dict[str, object] = {"kind": kind, "status": "PASS", "checkedAt": checked_at, "summary": "Passed", "findings": []}
        if kind == "ui":
            qa["webInterfaceGuidelines"] = {"sourceUrl": "https://example.com/guidelines.md", "fetchStatus": "FETCHED", "revision": "abc123", "sha256": "a" * 64}
        if kind == "accessibility":
            qa["webInterfaceGuidelines"] = {"sourceUrl": "https://example.com/guidelines.md", "fetchStatus": "FAILED", "revision": None, "sha256": None}
        write_json(report, qa)
        kit("qa-record", project_id, page_id, str(run["runId"]), kind, "--file", str(report))

    assert kit("qa-summary", project_id, page_id, str(run["runId"]))["status"] == "PASS"
    verdict = run_root / "release-verdict-input.json"
    write_json(verdict, {"status": "READY", "runId": run["runId"], "candidateId": candidate["candidateId"], "summary": "All invariants pass."})
    kit("release-check", project_id, page_id, str(run["runId"]), "--file", str(verdict))
    release = kit("release", project_id, page_id, str(run["runId"]))
    assert str(release["releaseId"]).startswith("v-")
    released_ui = json.loads((Path(str(release["release"])) / "qa" / "ui.json").read_text(encoding="utf-8"))
    assert released_ui["webInterfaceGuidelines"]["sha256"] == "a" * 64
    site = Path(str(release["release"])) / "site"
    assert (site / "images").is_dir()
    assert sorted(entry.name for entry in site.iterdir()) == ["base.css", "images", "index.html", "page.css"]
    terminal = json.loads((run_root / "run.json").read_text(encoding="utf-8"))
    assert terminal["status"] == "COMPLETED"
    mutation = run_kit("transition", project_id, page_id, str(run["runId"]), "BUILDING", check=False)
    assert mutation.returncode != 0
    assert "immutable" in mutation.stderr.lower()


def test_state_controller_creates_an_immutable_released_run_medichannel(project_factory) -> None:
    project_id, page_id = "state-controller-medichannel-test", "home"
    project_factory(project_id)
    kit(
        "init-project", project_id, "State controller MediChannel test", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp",
        "--dam-root", "test-region",
        "--css-root", "test-region/css",
    )
    article_path = "test/product/example_article01"
    kit("init-page", project_id, page_id, "Home", "--article-path", article_path)
    source = kit(
        "new-source", project_id, page_id,
        "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2",
    )
    source_root = Path(str(source["root"]))
    write_json(source_root / "spec" / "spec.json", {
        "version": 1, "page": {"name": "Home", "language": "ja"},
        "variants": [{"id": "desktop", "width": 960, "height": 900, "reference": "desktop.png"}],
        "tokens": {}, "sections": [{"id": "main"}], "assets": [], "openQuestions": [],
    })
    write_json(source_root / "spec" / "content-inventory.json", {
        "version": 1,
        "items": [{"id": "title", "kind": "heading", "text": "Hello", "required": True, "nodeId": "1:3", "sectionId": "main"}],
    })
    write_json(source_root / "asset-manifest.json", {"assets": []})
    (source_root / "reference" / "desktop.png").write_text("test", encoding="utf-8")
    kit("source-ready", project_id, page_id, str(source["sourceId"]))

    run = kit("new-run", project_id, page_id, "--source", str(source["sourceId"]))
    kit("transition", project_id, page_id, str(run["runId"]), "BUILDING")
    candidate = kit("new-candidate", project_id, page_id, str(run["runId"]), "--round", "0")
    candidate_root = Path(str(candidate["root"]))

    html_rel = Path("content") / "Test/Region/048-MediChannel/ja/jp" / f"{article_path}.html"
    css_dir = Path("etc") / "designs" / "code" / "test-region/css" / article_path
    assets_rel = Path("content") / "dam" / "test-region" / article_path

    assert (candidate_root / assets_rel).is_dir()
    (candidate_root / html_rel).parent.mkdir(parents=True, exist_ok=True)
    (candidate_root / html_rel).write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja"><head>'
        '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /><title>Home</title></head>'
        '<body><div id="main" role="main"><h1>Hello</h1></div></body></html>',
        encoding="utf-8",
    )
    (css_dir_abs := candidate_root / css_dir).mkdir(parents=True, exist_ok=True)
    (css_dir_abs / "base.css").write_text(".cst-page{margin:0}", encoding="utf-8")
    (css_dir_abs / "page.css").write_text(".cst-page h1{display:block}", encoding="utf-8")

    run_root = Path(str(run["root"]))
    static_report, browser_report, visual_report = (run_root / "static-input.json", run_root / "browser-input.json", run_root / "visual-input.json")
    write_json(static_report, {"status": "PASS"})
    write_json(browser_report, {"status": "PASS"})
    write_json(visual_report, {"status": "PASS", "pixelDifferencePercent": 0, "peakBandDifferencePercent": 0})
    kit("candidate-result", project_id, page_id, str(run["runId"]), str(candidate["candidateId"]), "--status", "accepted", "--static", str(static_report), "--browser", str(browser_report), "--metrics", str(visual_report))
    kit("transition", project_id, page_id, str(run["runId"]), "VERIFYING")

    checked_at = datetime.now(timezone.utc).isoformat()
    for kind in ("content", "ui", "accessibility", "technical"):
        report = run_root / f"{kind}-input.json"
        qa: dict[str, object] = {"kind": kind, "status": "PASS", "checkedAt": checked_at, "summary": "Passed", "findings": []}
        if kind == "ui":
            qa["webInterfaceGuidelines"] = {"sourceUrl": "https://example.com/guidelines.md", "fetchStatus": "FETCHED", "revision": "abc123", "sha256": "a" * 64}
        if kind == "accessibility":
            qa["webInterfaceGuidelines"] = {"sourceUrl": "https://example.com/guidelines.md", "fetchStatus": "FAILED", "revision": None, "sha256": None}
        write_json(report, qa)
        kit("qa-record", project_id, page_id, str(run["runId"]), kind, "--file", str(report))

    assert kit("qa-summary", project_id, page_id, str(run["runId"]))["status"] == "PASS"
    verdict = run_root / "release-verdict-input.json"
    write_json(verdict, {"status": "READY", "runId": run["runId"], "candidateId": candidate["candidateId"], "summary": "All invariants pass."})
    kit("release-check", project_id, page_id, str(run["runId"]), "--file", str(verdict))
    release = kit("release", project_id, page_id, str(run["runId"]))

    site = Path(str(release["release"])) / "site"
    assert (site / html_rel).is_file()
    assert (site / css_dir / "base.css").is_file()
    assert (site / css_dir / "page.css").is_file()
    assert (site / assets_rel).is_dir()
    # Nothing outside the three JCR subtrees survives into the released site.
    assert sorted(x.relative_to(site).as_posix() for x in site.rglob("*") if x.is_file()) == sorted(
        p.as_posix() for p in (html_rel, css_dir / "base.css", css_dir / "page.css")
    )


def test_medichannel_candidate_requires_delivery_and_article_path(project_factory) -> None:
    project_id, page_id = "state-controller-medichannel-missing-fields-test", "home"
    project_root = project_factory(project_id)
    kit("init-project", project_id, "Missing delivery fields test", "--platform", "medichannel")
    kit("init-page", project_id, page_id, "Home", "--article-path", "test/product/example_article01")
    # Simulate a pre-migration project.json that predates the delivery field.
    project_json = project_root / "project.json"
    project_json.write_text(json.dumps({**json.loads(project_json.read_text(encoding="utf-8")), "delivery": None}), encoding="utf-8")
    source = kit(
        "new-source", project_id, page_id,
        "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2",
    )
    source_root = Path(str(source["root"]))
    write_json(source_root / "spec" / "spec.json", {
        "version": 1, "page": {}, "variants": [{"id": "desktop", "reference": "desktop.png"}],
        "sections": [{"id": "main"}],
    })
    write_json(source_root / "spec" / "content-inventory.json", {"version": 1, "items": []})
    write_json(source_root / "asset-manifest.json", {"assets": []})
    (source_root / "reference" / "desktop.png").write_text("test", encoding="utf-8")
    kit("source-ready", project_id, page_id, str(source["sourceId"]))
    run = kit("new-run", project_id, page_id, "--source", str(source["sourceId"]))
    kit("transition", project_id, page_id, str(run["runId"]), "BUILDING")

    result = run_kit("new-candidate", project_id, page_id, str(run["runId"]), "--round", "0", check=False)
    assert result.returncode != 0
    assert "delivery path field" in result.stderr
    assert "contentRoot" in result.stderr and "damRoot" in result.stderr and "cssRoot" in result.stderr
