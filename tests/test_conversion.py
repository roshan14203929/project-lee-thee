from __future__ import annotations

import json
from pathlib import Path

from conftest import kit, run_kit


def write_json(path: Path, value: object) -> None:
    path.write_text(f"{json.dumps(value, indent=2)}\n", encoding="utf-8")


def prepare_ready_source(source: dict[str, object], heading: str = "Hello") -> None:
    root = Path(str(source["root"]))
    write_json(root / "spec" / "spec.json", {
        "version": 1,
        "page": {"name": "Home", "language": "en"},
        "variants": [{"id": "desktop", "label": "desktop", "nodeId": "1:2", "width": 1440, "height": 900, "reference": "desktop.png"}],
        "tokens": {"colors": []},
        "sections": [{"id": "main", "role": "content", "sourceNodeIds": ["1:3"], "textItemIds": ["title"], "assetIds": [], "bounds": {}, "layout": {}, "visual": {}}],
        "assets": [], "openQuestions": [],
    })
    write_json(root / "spec" / "content-inventory.json", {
        "version": 1,
        "items": [{"id": "title", "kind": "heading", "text": heading, "required": True, "nodeId": "1:3", "sectionId": "main"}],
    })
    write_json(root / "asset-manifest.json", {"assets": []})
    (root / "reference" / "desktop.png").write_text("reference", encoding="utf-8")


def write_flat_payload(candidate_root: Path) -> None:
    candidate_root.mkdir(parents=True, exist_ok=True)
    (candidate_root / "index.html").write_text(
        '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width">'
        '<title>Home</title><link rel="stylesheet" href="base.css"><link rel="stylesheet" href="page.css">'
        "</head><body><main><h1>Hello</h1></main></body></html>",
        encoding="utf-8",
    )
    (candidate_root / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (candidate_root / "page.css").write_text("main{display:block}", encoding="utf-8")
    (candidate_root / "images").mkdir(exist_ok=True)


def accept_candidate(project_id: str, page_id: str, run: dict[str, object], candidate: dict[str, object]) -> None:
    run_root = Path(str(run["root"]))
    static_report, browser_report, visual_report = (
        run_root / "static-input.json", run_root / "browser-input.json", run_root / "visual-input.json",
    )
    write_json(static_report, {"status": "PASS"})
    write_json(browser_report, {"status": "PASS"})
    write_json(visual_report, {"status": "PASS", "pixelDifferencePercent": 0, "peakBandDifferencePercent": 0})
    kit(
        "candidate-result", project_id, page_id, str(run["runId"]), str(candidate["candidateId"]),
        "--status", "accepted", "--static", str(static_report), "--browser", str(browser_report), "--metrics", str(visual_report),
    )


def build_accepted_m3_run(project_factory, project_id: str, page_id: str = "home") -> tuple[dict[str, object], dict[str, object]]:
    project_factory(project_id)
    kit("init-project", project_id, "Conversion source", "--platform", "html5")
    kit("init-page", project_id, page_id)
    source = kit("new-source", project_id, page_id, "--variant", "desktop=https://www.figma.com/design/example/Home?node-id=1-2")
    prepare_ready_source(source)
    kit("source-ready", project_id, page_id, str(source["sourceId"]))
    run = kit("new-run", project_id, page_id, "--source", str(source["sourceId"]))
    kit("transition", project_id, page_id, str(run["runId"]), "BUILDING")
    candidate = kit("new-candidate", project_id, page_id, str(run["runId"]), "--round", "0")
    write_flat_payload(Path(str(candidate["root"])))
    accept_candidate(project_id, page_id, run, candidate)
    return run, candidate


def test_convert_source_copies_and_dedupes(project_factory) -> None:
    src_project, target_project, page_id = "conv-src-a", "conv-target-a", "home"
    run, _candidate = build_accepted_m3_run(project_factory, src_project, page_id)
    project_factory(target_project)
    kit(
        "init-project", target_project, "Conversion target", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp", "--dam-root", "test-region", "--css-root", "test-region/css",
    )
    kit("init-page", target_project, page_id, "Home", "--article-path", "test/product/converted01")

    source_id = json.loads((Path(str(run["root"])) / "run.json").read_text(encoding="utf-8"))["sourceId"]
    converted = kit("convert-source", target_project, page_id, "--from-project", src_project, "--from-page", page_id, "--from-source", source_id)
    assert converted["reused"] is False
    assert converted["convertedFrom"] == {"project": src_project, "page": page_id, "sourceId": source_id}
    copied = json.loads((Path(str(converted["root"])) / "source.json").read_text(encoding="utf-8"))
    assert copied["status"] == "READY"
    assert (Path(str(converted["root"])) / "spec" / "spec.json").exists()

    reused = kit("convert-source", target_project, page_id, "--from-project", src_project, "--from-page", page_id, "--from-source", source_id)
    assert reused["reused"] is True
    assert reused["sourceId"] == converted["sourceId"]

    forced = kit("convert-source", target_project, page_id, "--from-project", src_project, "--from-page", page_id, "--from-source", source_id, "--force-new")
    assert forced["sourceId"] != converted["sourceId"]


def test_new_conversion_run_rejects_direction_platform_mismatch(project_factory) -> None:
    src_project, target_project, page_id = "conv-src-b", "conv-target-b", "home"
    run, candidate = build_accepted_m3_run(project_factory, src_project, page_id)
    project_factory(target_project)
    # Target is html5, but the direction targets medichannel -> must be rejected.
    kit("init-project", target_project, "Wrong platform target", "--platform", "html5")
    kit("init-page", target_project, page_id)
    mismatch = run_kit(
        "new-conversion-run", target_project, page_id,
        "--from-project", src_project, "--from-page", page_id, "--from-run", str(run["runId"]), "--from-candidate", str(candidate["candidateId"]),
        "--direction", "m3-to-medichannel", check=False,
    )
    assert mismatch.returncode != 0
    assert "platform" in mismatch.stderr.lower()


def test_new_conversion_run_rejects_non_accepted_candidate(project_factory) -> None:
    src_project, target_project, page_id = "conv-src-c", "conv-target-c", "home"
    run, _candidate = build_accepted_m3_run(project_factory, src_project, page_id)
    project_factory(target_project)
    kit(
        "init-project", target_project, "Conversion target", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp", "--dam-root", "test-region", "--css-root", "test-region/css",
    )
    kit("init-page", target_project, page_id, "Home", "--article-path", "test/product/converted03")
    wrong_candidate = run_kit(
        "new-conversion-run", target_project, page_id,
        "--from-project", src_project, "--from-page", page_id, "--from-run", str(run["runId"]), "--from-candidate", "candidate-999",
        "--direction", "m3-to-medichannel", check=False,
    )
    assert wrong_candidate.returncode != 0
    assert "not the accepted candidate" in wrong_candidate.stderr.lower()


def test_m3_to_medichannel_conversion_seeds_candidate_and_records_provenance(project_factory) -> None:
    src_project, target_project, page_id = "conv-src-d", "conv-target-d", "home"
    run, candidate = build_accepted_m3_run(project_factory, src_project, page_id)
    project_factory(target_project)
    article_path = "test/product/converted04"
    kit(
        "init-project", target_project, "Conversion target", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp", "--dam-root", "test-region", "--css-root", "test-region/css",
    )
    kit("init-page", target_project, page_id, "Home", "--article-path", article_path)

    conv_run = kit(
        "new-conversion-run", target_project, page_id,
        "--from-project", src_project, "--from-page", page_id, "--from-run", str(run["runId"]), "--from-candidate", str(candidate["candidateId"]),
        "--direction", "m3-to-medichannel",
    )
    assert conv_run["convertedFrom"]["project"] == src_project
    run_record = json.loads((Path(str(conv_run["root"])) / "run.json").read_text(encoding="utf-8"))
    assert run_record["convertedFrom"]["candidate"] == candidate["candidateId"]

    kit("transition", target_project, page_id, str(conv_run["runId"]), "BUILDING")
    ext_ref = f"{src_project}/{page_id}/{run['runId']}/{candidate['candidateId']}"
    seeded = kit("new-candidate", target_project, page_id, str(conv_run["runId"]), "--round", "0", "--from-external", ext_ref)
    seeded_root = Path(str(seeded["root"]))
    assert (seeded_root / "_conversion-input" / "index.html").exists()
    seeded_record = json.loads((seeded_root / "candidate.json").read_text(encoding="utf-8"))
    assert seeded_record["convertedFrom"] == {"project": src_project, "page": page_id, "run": run["runId"], "candidate": candidate["candidateId"]}

    # from-accepted and from-external must not be combinable.
    conflict = run_kit(
        "new-candidate", target_project, page_id, str(conv_run["runId"]), "--round", "0",
        "--from-accepted", "--from-external", ext_ref, check=False,
    )
    assert conflict.returncode != 0

    # The agent writes the target-shaped MediChannel payload alongside the frozen input.
    html_rel = Path("content") / "Test/Region/048-MediChannel/ja/jp" / f"{article_path}.html"
    css_dir = Path("etc") / "designs" / "code" / "test-region/css" / article_path
    assets_rel = Path("content") / "dam" / "test-region" / article_path
    (seeded_root / html_rel).parent.mkdir(parents=True, exist_ok=True)
    (seeded_root / html_rel).write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja"><head>'
        '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />'
        '<meta name="viewport" content="width=960" /><title>Home</title></head>'
        '<body><div id="main" role="main"><h1>Hello</h1></div></body></html>', encoding="utf-8",
    )
    (seeded_root / css_dir).mkdir(parents=True, exist_ok=True)
    (seeded_root / css_dir / "base.css").write_text(".cst-page{margin:0}", encoding="utf-8")
    (seeded_root / css_dir / "page.css").write_text(".cst-page h1{display:block}", encoding="utf-8")
    (seeded_root / assets_rel).mkdir(parents=True, exist_ok=True)

    accept_candidate(target_project, page_id, conv_run, seeded)
    generated = Path(str(conv_run["root"])) / "generated"
    assert not (generated / "_conversion-input").exists()
    assert (generated / html_rel).exists()


def test_pdf_export_requires_matching_accepted_candidate_and_full_lifecycle(project_factory) -> None:
    project_id, page_id = "conv-pdf-a", "home"
    run, candidate = build_accepted_m3_run(project_factory, project_id, page_id)

    mismatch = run_kit("new-pdf-export", project_id, page_id, str(run["runId"]), "--from-candidate", "candidate-999", check=False)
    assert mismatch.returncode != 0
    assert "not the accepted candidate" in mismatch.stderr.lower()

    export = kit("new-pdf-export", project_id, page_id, str(run["runId"]), "--from-candidate", str(candidate["candidateId"]))
    export_root = Path(str(export["root"]))
    (export_root / "index.pdf").write_text("fake-pdf-bytes", encoding="utf-8")

    run_root = Path(str(run["root"]))
    result_meta = run_root / "pdf-result-input.json"
    write_json(result_meta, {"pageCount": 1, "straddlingElements": []})
    kit("pdf-result", project_id, page_id, str(run["runId"]), str(export["pdfId"]), "--status", "ready", "--file", str(result_meta))

    incomplete = kit("pdf-qa-summary", project_id, page_id, str(run["runId"]), str(export["pdfId"]))
    assert incomplete["status"] == "FAIL"
    assert incomplete["missing"] == ["content", "visual-cutoff"]

    for kind in ("content", "visual-cutoff"):
        qa_file = run_root / f"pdf-{kind}-input.json"
        write_json(qa_file, {"kind": kind, "status": "PASS", "summary": "ok", "findings": []})
        kit("pdf-qa-record", project_id, page_id, str(run["runId"]), str(export["pdfId"]), kind, "--file", str(qa_file))

    assert kit("pdf-qa-summary", project_id, page_id, str(run["runId"]), str(export["pdfId"]))["status"] == "PASS"
    released = kit("pdf-release", project_id, page_id, str(run["runId"]), str(export["pdfId"]))
    assert released["released"] is True
    assert (Path(str(run["root"])).parents[1] / "current" / "index.pdf").read_text(encoding="utf-8") == "fake-pdf-bytes"
