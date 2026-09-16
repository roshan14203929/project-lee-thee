from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "materialize-medichannel.py"

MARKERS = {
    "headCssStart": "<!-- 個別CSS 設定ここから -->",
    "headCssEnd": "<!-- 個別CSS 設定ここまで -->",
    "bodyStart": "<!-- ボディ部分編集可能エリアここから -->",
    "bodyEnd": "<!-- ボディ部分編集可能エリアここまで -->",
    "jsStart": "<!-- 個別JS 設定ここから -->",
    "jsEnd": "<!-- 個別JS 設定ここまで -->",
}

FIXTURE_SHELL = (
    "<!doctype html><html lang=\"ja\"><head>\n"
    "<title>Placeholder Title</title>\n"
    f"{MARKERS['headCssStart']}\n"
    '<link rel="stylesheet" href="/etc/designs/code/shared/fixed.css" type="text/css" />\n'
    '<link rel="stylesheet" href="/etc/designs/code/old/base.css" type="text/css" />\n'
    '<link rel="stylesheet" href="/etc/designs/code/old/page.css" type="text/css" />\n'
    f"{MARKERS['headCssEnd']}\n"
    "</head>\n<body>\n"
    '<div id="chrome-before">SHARED HEADER</div>\n'
    f"{MARKERS['bodyStart']}\n"
    "PLACEHOLDER BODY\n"
    f"{MARKERS['jsStart']}\n{MARKERS['jsEnd']}\n"
    f"{MARKERS['bodyEnd']}\n"
    '<div id="chrome-after">SHARED FOOTER</div>\n'
    "</body></html>\n"
)


def write_fixture_template(root: Path, broken_sha256: bool = False) -> Path:
    template_dir = root / "delivery-templates" / "medichannel" / "fixture"
    template_dir.mkdir(parents=True)
    shell_path = template_dir / "shell.html"
    shell_path.write_text(FIXTURE_SHELL, encoding="utf-8")
    sha256 = hashlib.sha256(shell_path.read_bytes()).hexdigest()
    manifest = {
        "templateId": "fixture", "capturedFrom": "test fixture", "capturedAt": "2026-01-01T00:00:00Z",
        "sha256": "0" * 64 if broken_sha256 else sha256, "markers": MARKERS,
    }
    (template_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root / "delivery-templates" / "medichannel"


def write_flat_input(root: Path, title: str = "Test Title", body: str = '<div id="main" role="main"><h1>Hello Fixture</h1><img src="images/hero.png" alt="hero"></div>') -> None:
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(
        f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>{title}</title>'
        '<link rel="stylesheet" href="base.css"><link rel="stylesheet" href="page.css"></head>'
        f"<body>{body}</body></html>",
        encoding="utf-8",
    )
    (root / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (root / "page.css").write_text(".hero{background:url(images/hero.png)}", encoding="utf-8")
    (root / "images" / "hero.png").write_bytes(b"fake")


DELIVERY = ["--content-root", "Test/Region", "--dam-root", "tr", "--css-root", "tr/css", "--article-path", "a/b"]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def test_materialize_splices_correctly_and_leaves_chrome_untouched(tmp_path: Path) -> None:
    template_root = write_fixture_template(tmp_path)
    input_dir = tmp_path / "input"
    write_flat_input(input_dir)
    output_dir = tmp_path / "output"
    report_path = tmp_path / "report.json"

    result = run(
        "--input", str(input_dir), "--output", str(output_dir), *DELIVERY,
        "--template", "fixture", "--template-root", str(template_root), "--output-report", str(report_path),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "OK"
    assert report["template"] == "fixture"

    html = (output_dir / "content" / "Test" / "Region" / "a" / "b.html").read_text(encoding="utf-8")
    # Title substituted.
    assert "<title>Test Title</title>" in html
    assert "Placeholder Title" not in html
    # Head CSS marker: only the two per-article links rewritten; the shared one untouched.
    assert 'href="/etc/designs/code/shared/fixed.css"' in html
    assert 'href="/etc/designs/code/old/base.css"' not in html
    assert 'href="/etc/designs/code/old/page.css"' not in html
    assert 'href="/etc/designs/code/tr/css/a/b/base.css"' in html
    assert 'href="/etc/designs/code/tr/css/a/b/page.css"' in html
    # Body marker: flat candidate's own content spliced in, asset path rewritten.
    assert "PLACEHOLDER BODY" not in html
    assert "<h1>Hello Fixture</h1>" in html
    assert 'src="/content/dam/tr/a/b/hero.png"' in html
    # Chrome outside the markers is untouched.
    assert '<div id="chrome-before">SHARED HEADER</div>' in html
    assert '<div id="chrome-after">SHARED FOOTER</div>' in html

    base_css = (output_dir / "etc" / "designs" / "code" / "tr" / "css" / "a" / "b" / "base.css").read_text(encoding="utf-8")
    assert base_css == "body{margin:0}"
    page_css = (output_dir / "etc" / "designs" / "code" / "tr" / "css" / "a" / "b" / "page.css").read_text(encoding="utf-8")
    assert "url(/content/dam/tr/a/b/hero.png)" in page_css
    assert (output_dir / "content" / "dam" / "tr" / "a" / "b" / "hero.png").exists()


def test_rejects_a_non_flat_input(tmp_path: Path) -> None:
    template_root = write_fixture_template(tmp_path)
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    result = run(
        "--input", str(input_dir), "--output", str(tmp_path / "output"), *DELIVERY,
        "--template", "fixture", "--template-root", str(template_root), "--output-report", str(tmp_path / "report.json"),
    )
    assert result.returncode != 0
    assert "base.css" in result.stderr


def test_rejects_a_script_tag_in_the_flat_body(tmp_path: Path) -> None:
    template_root = write_fixture_template(tmp_path)
    input_dir = tmp_path / "input"
    write_flat_input(input_dir, body='<div id="main"><script>alert(1)</script></div>')
    result = run(
        "--input", str(input_dir), "--output", str(tmp_path / "output"), *DELIVERY,
        "--template", "fixture", "--template-root", str(template_root), "--output-report", str(tmp_path / "report.json"),
    )
    assert result.returncode != 0
    assert "<script>" in result.stderr


def test_materializes_a_copy_of_the_real_completed_flat_release(tmp_path: Path) -> None:
    # Regression target: projects/medichannel/pages/fsn-hes-article02's real,
    # already-completed release is flat -- proof that native MediChannel
    # builds have always been flat in practice. Operate on a *copy*, never
    # the live project data.
    real_project = json.loads((ROOT / "projects" / "medichannel" / "project.json").read_text(encoding="utf-8"))
    real_page = json.loads((ROOT / "projects" / "medichannel" / "pages" / "fsn-hes-article02" / "page.json").read_text(encoding="utf-8"))
    real_site = ROOT / "projects" / "medichannel" / "pages" / "fsn-hes-article02" / "releases" / "v-001" / "site"
    delivery = real_project["delivery"]
    article_path = real_page["articlePath"]

    input_dir = tmp_path / "site-copy"
    import shutil

    shutil.copytree(real_site, input_dir)
    output_dir = tmp_path / "jcr"
    result = run(
        "--input", str(input_dir), "--output", str(output_dir),
        "--content-root", delivery["contentRoot"], "--dam-root", delivery["damRoot"], "--css-root", delivery["cssRoot"],
        "--article-path", article_path, "--output-report", str(tmp_path / "report.json"),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "OK"

    html_rel = Path("content") / delivery["contentRoot"] / f"{article_path}.html"
    css_dir = Path("etc") / "designs" / "code" / delivery["cssRoot"] / article_path
    assets_rel = Path("content") / "dam" / delivery["damRoot"] / article_path
    materialized_html = (output_dir / html_rel).read_text(encoding="utf-8")
    real_title = re.search(r"<title>(.*?)</title>", (input_dir / "index.html").read_text(encoding="utf-8"), re.S).group(1).strip()
    assert f"<title>{real_title}</title>" in materialized_html
    assert (output_dir / css_dir / "base.css").is_file()
    assert (output_dir / css_dir / "page.css").is_file()
    assert (output_dir / assets_rel).is_dir()
    for image in (input_dir / "images").iterdir():
        assert (output_dir / assets_rel / image.name).exists()


def test_production_shell_matches_its_recorded_sha256() -> None:
    template_dir = ROOT / "delivery-templates" / "medichannel" / "1column"
    manifest = json.loads((template_dir / "manifest.json").read_text(encoding="utf-8"))
    actual = hashlib.sha256((template_dir / "shell.html").read_bytes()).hexdigest()
    assert actual == manifest["sha256"], (
        "delivery-templates/medichannel/1column/shell.html has drifted from manifest.json's recorded "
        "sha256 -- if this is an intentional recapture, update the manifest; otherwise something hand-edited the shell."
    )
    for key in ("headCssStart", "headCssEnd", "bodyStart", "bodyEnd", "jsStart", "jsEnd"):
        assert manifest["markers"][key] in (template_dir / "shell.html").read_text(encoding="utf-8")
