from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render-pdf.py"

_spec = importlib.util.spec_from_file_location("render_pdf_under_test", SCRIPT)
render_pdf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(render_pdf)  # type: ignore[union-attr]


def test_strip_pass_wraps_nav_and_blank_target_links_without_deleting_them() -> None:
    html = (
        '<body><nav class="toc"><a href="#s1">Section 1</a></nav>'
        "<h1>Title</h1><p>Keep this visible.</p>"
        '<a target="_blank" rel="noopener noreferrer" href="https://example.com/pi">View PI</a>'
        "</body>"
    )
    out, wrapped, flagged = render_pdf.apply_strip_pass(html)
    assert flagged == []
    assert {w["type"] for w in wrapped} == {"nav", "a[target=_blank]"}
    # Comment-wrapped, not deleted: the original markup is still present, just inert.
    assert '<!-- <nav class="toc"><a href="#s1">Section 1</a></nav> -->' in out
    assert '<!-- <a target="_blank" rel="noopener noreferrer" href="https://example.com/pi">View PI</a> -->' in out
    assert "<h1>Title</h1>" in out
    assert "Keep this visible." in out


def test_strip_pass_flags_buttons_and_ambiguous_external_links_without_touching_them() -> None:
    html = '<body><button>Submit</button><a href="https://cite.example/paper">Citation</a></body>'
    out, wrapped, flagged = render_pdf.apply_strip_pass(html)
    assert wrapped == []
    assert out == html  # nothing auto-wrapped; both are ambiguous, so left untouched
    types = {f["type"] for f in flagged}
    assert types == {"button", "external-link"}


def test_strip_pass_handles_nested_nav_blocks_via_depth_counting() -> None:
    html = '<nav id="outer">outer text<nav id="inner">inner text</nav>after</nav><p>tail</p>'
    out, wrapped, flagged = render_pdf.apply_strip_pass(html)
    assert len(wrapped) == 1
    assert wrapped[0]["type"] == "nav"
    assert out.count("<!--") == 1
    assert "<p>tail</p>" in out


def test_render_pdf_end_to_end_produces_pdf_and_report(tmp_path: Path) -> None:
    site = tmp_path / "site"
    (site / "images").mkdir(parents=True)
    (site / "index.html").write_text(
        '<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>T</title>'
        '<link rel="stylesheet" href="base.css"><link rel="stylesheet" href="page.css"></head>'
        '<body><div class="cst-page"><nav class="toc"><a href="#s1">S1</a></nav>'
        "<h1>Title</h1><p>Hello world.</p>"
        '<a target="_blank" rel="noopener noreferrer" href="https://example.com/pi">View PI</a>'
        "</div></body></html>",
        encoding="utf-8",
    )
    (site / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (site / "page.css").write_text(".cst-page{max-width:960px}", encoding="utf-8")

    output = tmp_path / "out" / "index.pdf"
    report_path = tmp_path / "out" / "report.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(site), "--output", str(output), "--strip-report", str(report_path)],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert output.exists() and output.stat().st_size > 0
    assert report["status"] == "OK"
    assert {w["type"] for w in report["commentWrapped"]} == {"nav", "a[target=_blank]"}
    assert report["flaggedInteractive"] == []

    # base.css/page.css/images must stay byte-identical to the source, never touched.
    stripped_root = output.parent / f"{output.stem}-stripped"
    assert (stripped_root / "base.css").read_text(encoding="utf-8") == "body{margin:0}"
    assert (stripped_root / "page.css").read_text(encoding="utf-8") == ".cst-page{max-width:960px}"
    stripped_html = (stripped_root / "index.html").read_text(encoding="utf-8")
    assert "<!-- <nav" in stripped_html
    assert "View PI" in stripped_html  # preserved inside the comment, not deleted
    assert "<h1>Title</h1>" in stripped_html
