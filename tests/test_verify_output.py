from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from conftest import ROOT, kit
from test_conversion import build_accepted_m3_run, write_flat_payload

_spec = importlib.util.spec_from_file_location("verify_output_under_test", ROOT / "scripts" / "verify-output.py")
verify_output = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify_output)  # type: ignore[union-attr]


def test_native_medichannel_candidate_auto_resolves_flat(project_factory) -> None:
    project_id, page_id = "verify-output-medichannel-native-test", "home"
    project_factory(project_id)
    kit(
        "init-project", project_id, "Native flat verify test", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp", "--dam-root", "test-region", "--css-root", "test-region/css",
    )
    kit("init-page", project_id, page_id, "Home", "--article-path", "test/product/example01")
    source = kit("new-source", project_id, page_id, "--variant", "desktop=https://www.figma.com/design/example?node-id=1-2")
    source_root = Path(str(source["root"]))
    (source_root / "spec" / "spec.json").write_text(json.dumps({
        "version": 1, "page": {}, "variants": [{"id": "desktop", "reference": "desktop.png"}], "sections": [{"id": "main"}],
    }), encoding="utf-8")
    (source_root / "spec" / "content-inventory.json").write_text(json.dumps({"version": 1, "items": []}), encoding="utf-8")
    (source_root / "asset-manifest.json").write_text(json.dumps({"assets": []}), encoding="utf-8")
    (source_root / "reference" / "desktop.png").write_text("test", encoding="utf-8")
    kit("source-ready", project_id, page_id, str(source["sourceId"]))
    run = kit("new-run", project_id, page_id, "--source", str(source["sourceId"]))
    kit("transition", project_id, page_id, str(run["runId"]), "BUILDING")
    candidate = kit("new-candidate", project_id, page_id, str(run["runId"]), "--round", "0")
    write_flat_payload(Path(str(candidate["root"])))

    spec = verify_output.resolve_spec(Path(str(candidate["root"])), {})
    assert spec == {"kind": "flat"}


def test_conversion_candidate_still_auto_resolves_jcr(project_factory) -> None:
    src_project, target_project, page_id = "verify-output-conv-src-test", "verify-output-conv-target-test", "home"
    run, candidate = build_accepted_m3_run(project_factory, src_project, page_id)
    project_factory(target_project)
    kit(
        "init-project", target_project, "Conversion target", "--platform", "medichannel",
        "--content-root", "Test/Region/048-MediChannel/ja/jp", "--dam-root", "test-region", "--css-root", "test-region/css",
    )
    kit("init-page", target_project, page_id, "Home", "--article-path", "test/product/converted-verify01")
    conv_run = kit(
        "new-conversion-run", target_project, page_id,
        "--from-project", src_project, "--from-page", page_id, "--from-run", str(run["runId"]), "--from-candidate", str(candidate["candidateId"]),
        "--direction", "m3-to-medichannel",
    )
    kit("transition", target_project, page_id, str(conv_run["runId"]), "BUILDING")
    ext_ref = f"{src_project}/{page_id}/{run['runId']}/{candidate['candidateId']}"
    seeded = kit("new-candidate", target_project, page_id, str(conv_run["runId"]), "--round", "0", "--from-external", ext_ref)

    spec = verify_output.resolve_spec(Path(str(seeded["root"])), {})
    assert spec["kind"] == "jcr"
    assert spec["contentRoot"] == "Test/Region/048-MediChannel/ja/jp"
    assert spec["articlePath"] == "test/product/converted-verify01"


def test_explicit_platform_flags_validate_a_materialized_nested_dir(tmp_path: Path) -> None:
    # No candidate.json here at all -- this is the documented ad hoc path for
    # independently validating a materialized nested tree (releases/v-###/jcr/,
    # runs/<run>/materialized/materialized-###/jcr/), which has none of its own.
    spec = verify_output.resolve_spec(tmp_path, {
        "platform": "medichannel", "content-root": "a/b", "dam-root": "c", "css-root": "d/e", "article-path": "f/g",
    })
    assert spec == {"kind": "jcr", "articlePath": "f/g", "contentRoot": "a/b", "damRoot": "c", "cssRoot": "d/e"}
