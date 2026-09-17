from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from conftest import ROOT, kit, run_kit
from test_conversion import write_flat_payload


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
    # Native MediChannel builds are flat (identical contract to html5/M3) all
    # through BUILDING/VERIFYING/REFINING/release -- the nested AEM/JCR tree
    # is a separate, additional artifact produced by release-materialize +
    # materialize-medichannel.py, never the released site/current shape.
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
    assert sorted(x.name for x in candidate_root.iterdir()) == ["candidate.json", "images"]
    write_flat_payload(candidate_root)

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
    assert sorted(x.name for x in site.iterdir()) == ["base.css", "images", "index.html", "page.css"]
    current = Path(str(release["release"])).parents[1] / "current"
    assert sorted(x.name for x in current.iterdir()) == ["base.css", "images", "index.html", "page.css"]

    # release-materialize + materialize-medichannel.py produce the nested
    # AEM/JCR tree as a separate, additional artifact -- site/current stay flat.
    materialized = kit("release-materialize", project_id, page_id, str(run["runId"]))
    materialize_result = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts" / "materialize-medichannel.py"),
            "--input", materialized["input"], "--output", materialized["root"],
            "--content-root", materialized["delivery"]["contentRoot"],
            "--dam-root", materialized["delivery"]["damRoot"],
            "--css-root", materialized["delivery"]["cssRoot"],
            "--article-path", materialized["articlePath"],
            "--output-report", str(Path(materialized["root"]).parent / "jcr-materialization-report.json"),
        ],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert materialize_result.returncode == 0, materialize_result.stderr

    jcr = Path(materialized["root"])
    html_rel = Path("content") / "Test/Region/048-MediChannel/ja/jp" / f"{article_path}.html"
    css_dir = Path("etc") / "designs" / "code" / "test-region/css" / article_path
    assets_rel = Path("content") / "dam" / "test-region" / article_path
    assert (jcr / html_rel).is_file()
    assert (jcr / css_dir / "base.css").is_file()
    assert (jcr / css_dir / "page.css").is_file()
    assert (jcr / assets_rel).is_dir()
    # Nothing outside the three JCR subtrees survives into the materialized output.
    assert sorted(x.relative_to(jcr).as_posix() for x in jcr.rglob("*") if x.is_file()) == sorted(
        p.as_posix() for p in (html_rel, css_dir / "base.css", css_dir / "page.css")
    )


def test_new_materialization_works_on_a_real_in_flight_run_without_touching_generated(project_factory) -> None:
    # Regression target: projects/medichannel/pages/fsn-hes-article03/runs/run-002
    # is a real, currently-VERIFYING (non-terminal) run with real flat content.
    # new-materialization is a side artifact, not a run-state transition, so it
    # must work pre-release and must never touch generated/ or candidates/*.
    real_generated = ROOT / "projects" / "medichannel" / "pages" / "fsn-hes-article03" / "runs" / "run-002" / "generated"
    real_delivery = json.loads((ROOT / "projects" / "medichannel" / "project.json").read_text(encoding="utf-8"))["delivery"]
    real_article_path = json.loads((ROOT / "projects" / "medichannel" / "pages" / "fsn-hes-article03" / "page.json").read_text(encoding="utf-8"))["articlePath"]

    # Kept short: the real contentRoot below is already deep, and Windows'
    # default MAX_PATH (260 chars) has no headroom for a long project id here.
    project_id, page_id = "medi-inflight-test", "home"
    project_factory(project_id)
    kit(
        "init-project", project_id, "In-flight materialization test", "--platform", "medichannel",
        "--content-root", real_delivery["contentRoot"], "--dam-root", real_delivery["damRoot"], "--css-root", real_delivery["cssRoot"],
    )
    kit("init-page", project_id, page_id, "Home", "--article-path", real_article_path)
    source = kit("new-source", project_id, page_id, "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2")
    source_root = Path(str(source["root"]))
    write_json(source_root / "spec" / "spec.json", {
        "version": 1, "page": {}, "variants": [{"id": "desktop", "reference": "desktop.png"}], "sections": [{"id": "main"}],
    })
    write_json(source_root / "spec" / "content-inventory.json", {"version": 1, "items": []})
    write_json(source_root / "asset-manifest.json", {"assets": []})
    (source_root / "reference" / "desktop.png").write_text("test", encoding="utf-8")
    kit("source-ready", project_id, page_id, str(source["sourceId"]))
    run = kit("new-run", project_id, page_id, "--source", str(source["sourceId"]))
    kit("transition", project_id, page_id, str(run["runId"]), "BUILDING")
    candidate = kit("new-candidate", project_id, page_id, str(run["runId"]), "--round", "0")
    candidate_root = Path(str(candidate["root"]))
    for name in ("index.html", "base.css", "page.css"):
        shutil.copyfile(real_generated / name, candidate_root / name)
    shutil.rmtree(candidate_root / "images")
    shutil.copytree(real_generated / "images", candidate_root / "images")

    run_root = Path(str(run["root"]))
    static_report, browser_report, visual_report = (run_root / "static-input.json", run_root / "browser-input.json", run_root / "visual-input.json")
    write_json(static_report, {"status": "PASS"})
    write_json(browser_report, {"status": "PASS"})
    write_json(visual_report, {"status": "PASS", "pixelDifferencePercent": 0, "peakBandDifferencePercent": 0})
    kit("candidate-result", project_id, page_id, str(run["runId"]), str(candidate["candidateId"]), "--status", "accepted", "--static", str(static_report), "--browser", str(browser_report), "--metrics", str(visual_report))
    kit("transition", project_id, page_id, str(run["runId"]), "VERIFYING")

    generated_before = {x.relative_to(run_root / "generated").as_posix(): (run_root / "generated" / x).read_bytes() for x in (run_root / "generated").rglob("*") if x.is_file()}

    materialized = kit("new-materialization", project_id, page_id, str(run["runId"]))
    materialize_result = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts" / "materialize-medichannel.py"),
            "--input", materialized["input"], "--output", materialized["root"],
            "--content-root", materialized["delivery"]["contentRoot"],
            "--dam-root", materialized["delivery"]["damRoot"],
            "--css-root", materialized["delivery"]["cssRoot"],
            "--article-path", materialized["articlePath"],
            "--output-report", str(Path(materialized["root"]).parent / "report.json"),
        ],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert materialize_result.returncode == 0, materialize_result.stderr
    kit("materialization-result", project_id, page_id, str(run["runId"]), str(materialized["materializationId"]), "--status", "ready", "--file", str(Path(materialized["root"]).parent / "report.json"))

    # The run is still VERIFYING (non-terminal), and generated/ is untouched.
    assert json.loads((run_root / "run.json").read_text(encoding="utf-8"))["status"] == "VERIFYING"
    generated_after = {x.relative_to(run_root / "generated").as_posix(): (run_root / "generated" / x).read_bytes() for x in (run_root / "generated").rglob("*") if x.is_file()}
    assert generated_before == generated_after
    assert not (run_root / "candidates" / str(candidate["candidateId"]) / "jcr").exists()

    html_rel = Path("content") / real_delivery["contentRoot"] / f"{real_article_path}.html"
    assert (Path(materialized["root"]) / html_rel).is_file()


def test_medichannel_native_candidate_builds_flat_without_delivery(project_factory) -> None:
    # Native MediChannel builds (not a channel-conversion run) are flat -- the
    # same contract as html5/M3 -- for the whole BUILDING/VERIFYING/REFINING
    # lifecycle, so delivery path fields are not needed until materialization.
    project_id, page_id = "state-controller-medichannel-native-flat-test", "home"
    project_root = project_factory(project_id)
    kit(
        "init-project", project_id, "Native flat build test", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp",
        "--dam-root", "test-region",
        "--css-root", "test-region/css",
    )
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

    candidate = kit("new-candidate", project_id, page_id, str(run["runId"]), "--round", "0")
    candidate_root = Path(str(candidate["root"]))
    assert sorted(x.name for x in candidate_root.iterdir()) == ["candidate.json", "images"]


def test_medichannel_conversion_candidate_still_requires_delivery_and_article_path(project_factory) -> None:
    # A channel-conversion run's candidates ARE nested from creation (they're
    # produced by convert-platform.py's genuine HTML5->XHTML transform), so
    # they still need the target project's delivery fields -- unlike a native
    # MediChannel build (see test above).
    src_project, target_project, page_id = "state-controller-conversion-src-test", "state-controller-conversion-missing-fields-test", "home"
    project_factory(src_project)
    kit("init-project", src_project, "Conversion source", "--platform", "html5")
    kit("init-page", src_project, page_id)
    source = kit("new-source", src_project, page_id, "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2")
    source_root = Path(str(source["root"]))
    write_json(source_root / "spec" / "spec.json", {
        "version": 1, "page": {"name": "Home", "language": "en"},
        "variants": [{"id": "desktop", "label": "desktop", "nodeId": "1:2", "width": 1440, "height": 900, "reference": "desktop.png"}],
        "tokens": {"colors": []},
        "sections": [{"id": "main", "role": "content", "sourceNodeIds": ["1:3"], "textItemIds": ["title"], "assetIds": [], "bounds": {}, "layout": {}, "visual": {}}],
        "assets": [], "openQuestions": [],
    })
    write_json(source_root / "spec" / "content-inventory.json", {
        "version": 1,
        "items": [{"id": "title", "kind": "heading", "text": "Hello", "required": True, "nodeId": "1:3", "sectionId": "main"}],
    })
    write_json(source_root / "asset-manifest.json", {"assets": []})
    (source_root / "reference" / "desktop.png").write_text("test", encoding="utf-8")
    kit("source-ready", src_project, page_id, str(source["sourceId"]))
    run = kit("new-run", src_project, page_id, "--source", str(source["sourceId"]))
    kit("transition", src_project, page_id, str(run["runId"]), "BUILDING")
    candidate = kit("new-candidate", src_project, page_id, str(run["runId"]), "--round", "0")
    candidate_root = Path(str(candidate["root"]))
    (candidate_root / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width">'
        '<title>Home</title><link rel="stylesheet" href="base.css"><link rel="stylesheet" href="page.css">'
        "</head><body><main><h1>Hello</h1></main></body></html>",
        encoding="utf-8",
    )
    (candidate_root / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (candidate_root / "page.css").write_text("main{display:block}", encoding="utf-8")
    run_root = Path(str(run["root"]))
    static_report, browser_report, visual_report = (run_root / "static-input.json", run_root / "browser-input.json", run_root / "visual-input.json")
    write_json(static_report, {"status": "PASS"})
    write_json(browser_report, {"status": "PASS"})
    write_json(visual_report, {"status": "PASS", "pixelDifferencePercent": 0, "peakBandDifferencePercent": 0})
    kit("candidate-result", src_project, page_id, str(run["runId"]), str(candidate["candidateId"]), "--status", "accepted", "--static", str(static_report), "--browser", str(browser_report), "--metrics", str(visual_report))

    target_root = project_factory(target_project)
    kit(
        "init-project", target_project, "Missing delivery fields test", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp",
        "--dam-root", "test-region",
        "--css-root", "test-region/css",
    )
    kit("init-page", target_project, page_id, "Home", "--article-path", "test/product/example_article01")
    # Simulate a pre-migration project.json that predates the delivery field.
    target_project_json = target_root / "project.json"
    target_project_json.write_text(json.dumps({**json.loads(target_project_json.read_text(encoding="utf-8")), "delivery": None}), encoding="utf-8")

    conv_run = kit(
        "new-conversion-run", target_project, page_id,
        "--from-project", src_project, "--from-page", page_id, "--from-run", str(run["runId"]), "--from-candidate", str(candidate["candidateId"]),
        "--direction", "m3-to-medichannel",
    )
    kit("transition", target_project, page_id, str(conv_run["runId"]), "BUILDING")
    ext_ref = f"{src_project}/{page_id}/{run['runId']}/{candidate['candidateId']}"
    result = run_kit("new-candidate", target_project, page_id, str(conv_run["runId"]), "--round", "0", "--from-external", ext_ref, check=False)
    assert result.returncode != 0
    assert "delivery path field" in result.stderr
    assert "contentRoot" in result.stderr and "damRoot" in result.stderr and "cssRoot" in result.stderr


def test_medichannel_project_requires_explicit_delivery_paths(project_factory) -> None:
    # Defaulting these would publish one engagement's build into another's JCR tree.
    project_id = "state-controller-medichannel-no-default-test"
    project_root = project_factory(project_id)
    result = run_kit("init-project", project_id, "No delivery default", "--platform", "medichannel", check=False)
    assert result.returncode != 0
    assert "--content-root" in result.stderr and "--dam-root" in result.stderr and "--css-root" in result.stderr
    assert not project_root.exists()


def test_set_article_path_recovers_a_page_after_a_platform_switch(project_factory) -> None:
    project_id, page_id = "state-controller-set-article-path-test", "home"
    project_root = project_factory(project_id)
    kit("init-project", project_id, "Article path recovery")
    kit("init-page", project_id, page_id, "Home")
    kit(
        "set-platform", project_id, "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp",
        "--dam-root", "test-region",
        "--css-root", "test-region/css",
    )
    page_json = project_root / "pages" / page_id / "page.json"
    assert json.loads(page_json.read_text(encoding="utf-8"))["articlePath"] is None

    article_path = "test/product/example_article01"
    kit("set-article-path", project_id, page_id, "--article-path", article_path)
    assert json.loads(page_json.read_text(encoding="utf-8"))["articlePath"] == article_path
