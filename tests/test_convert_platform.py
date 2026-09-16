from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "convert-platform.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )


def write_m3_input(root: Path, body: str) -> None:
    (root / "images").mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(
        "<!doctype html>\n<html lang=\"ja\">\n<head><meta charset=\"utf-8\">"
        f"<title>T</title><link rel=\"stylesheet\" href=\"base.css\">"
        f"<link rel=\"stylesheet\" href=\"page.css\"></head>\n<body>\n{body}\n</body>\n</html>\n",
        encoding="utf-8",
    )
    (root / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (root / "page.css").write_text(".hero{background:url(images/hero.png)}", encoding="utf-8")
    (root / "images" / "hero.png").write_bytes(b"fake")


DELIVERY = ["--content-root", "Test/Region", "--dam-root", "tr", "--css-root", "tr/css", "--article-path", "a/b"]


def test_m3_to_medichannel_remaps_structure_doctype_and_paths(tmp_path: Path) -> None:
    m3_input = tmp_path / "m3-input"
    write_m3_input(m3_input, (
        '<main><header class="site-header"><h1>T</h1></header>'
        '<section id="sec-01" class="hero"><figure><img src="images/hero.png" alt="hero">'
        "<figcaption>caption</figcaption></figure>"
        "<p>Tom & Jerry's data <input disabled> <br></p></section>"
        "<nav><a href=\"#sec-01\">Link</a></nav></main><footer>F</footer>"
    ))
    output = tmp_path / "medi-output"
    report_path = tmp_path / "report.json"
    result = run("--direction", "m3-to-medichannel", "--input", str(m3_input), "--output", str(output), *DELIVERY, "--output-report", str(report_path))
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "OK"
    assert report["flagged"] == []

    html = (output / "content" / "Test" / "Region" / "a" / "b.html").read_text(encoding="utf-8")
    assert html.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert 'DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"' in html
    assert '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">' in html
    assert '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />' in html
    assert '<div id="main" role="main">' in html
    assert 'class="header site-header" role="banner"' in html
    assert 'id="sec-01" class="section hero" role="region"' in html
    assert '<div class="figure">' in html
    assert '<p class="figcaption">caption</p>' in html
    assert '<div class="nav" role="navigation">' in html
    assert '<div class="footer" role="contentinfo">' in html
    assert "Tom &amp; Jerry's" in html
    assert '<input disabled="disabled" />' in html
    assert "<br />" in html
    assert 'src="/content/dam/tr/a/b/hero.png"' in html
    assert 'href="/etc/designs/code/tr/css/a/b/base.css"' in html
    assert 'href="/etc/designs/code/tr/css/a/b/page.css"' in html
    assert "</main>" not in html and "</section>" not in html and "</header>" not in html

    base_css = (output / "etc" / "designs" / "code" / "tr" / "css" / "a" / "b" / "base.css").read_text(encoding="utf-8")
    assert base_css == "body{margin:0}"
    page_css = (output / "etc" / "designs" / "code" / "tr" / "css" / "a" / "b" / "page.css").read_text(encoding="utf-8")
    assert "url(/content/dam/tr/a/b/hero.png)" in page_css
    assert (output / "content" / "dam" / "tr" / "a" / "b" / "hero.png").exists()


def test_medichannel_to_m3_reverses_structure_and_decodes_safe_entities(tmp_path: Path) -> None:
    medi_input = tmp_path / "medi-input"
    html_dir = medi_input / "content" / "Test" / "Region" / "a"
    css_dir = medi_input / "etc" / "designs" / "code" / "tr" / "css" / "a" / "b"
    dam_dir = medi_input / "content" / "dam" / "tr" / "a" / "b"
    html_dir.mkdir(parents=True)
    css_dir.mkdir(parents=True)
    dam_dir.mkdir(parents=True)
    (html_dir / "b.html").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja"><head>'
        '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /><title>T</title></head>'
        "<body><div id=\"main\" role=\"main\"><div class=\"section\" role=\"region\">"
        "<h2>第&#8546;相試験</h2>"
        "<p>&#9312;主要評価項目&#9313;副次的評価項目</p>"
        '<img src="/content/dam/tr/a/b/hero.png" alt="hero" />'
        "</div></div></body></html>",
        encoding="utf-8",
    )
    (css_dir / "base.css").write_text("body{margin:0}", encoding="utf-8")
    (css_dir / "page.css").write_text(".hero{background:url(/content/dam/tr/a/b/hero.png)}", encoding="utf-8")
    (dam_dir / "hero.png").write_bytes(b"fake")

    output = tmp_path / "m3-output"
    report_path = tmp_path / "report.json"
    result = run("--direction", "medichannel-to-m3", "--input", str(medi_input), "--output", str(output), *DELIVERY, "--output-report", str(report_path))
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["flagged"] == []

    html = (output / "index.html").read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert '<html lang="ja">' in html
    assert '<meta charset="utf-8">' in html
    assert "<main>" in html and "<section>" in html
    assert "第III相試験" in html  # 第III相: decoded Roman numeral
    assert "(1)主要評価項目(2)" in html  # decoded circled digits
    assert 'src="images/hero.png"' in html
    page_css = (output / "page.css").read_text(encoding="utf-8")
    assert "url(images/hero.png)" in page_css
    assert (output / "images" / "hero.png").exists()


def test_flags_prohibited_elements_and_ambiguous_characters_without_mutating(tmp_path: Path) -> None:
    m3_input = tmp_path / "m3-input"
    write_m3_input(m3_input, (
        "<section><h2>第III相試験</h2>"
        "<p>検定手順は(1)主要評価項目(2)副次的評価項目</p>"
        '<picture><source src="a.webp"><img src="a.png" alt="x"></picture></section>'
    ))
    output = tmp_path / "medi-output"
    report_path = tmp_path / "report.json"
    result = run("--direction", "m3-to-medichannel", "--input", str(m3_input), "--output", str(output), *DELIVERY, "--output-report", str(report_path))
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "REVIEW_NEEDED"
    types = {f["type"] for f in report["flagged"]}
    assert types == {"prohibited-element", "roman-numeral-candidate", "circled-digit-candidate"}

    html = (output / "content" / "Test" / "Region" / "a" / "b.html").read_text(encoding="utf-8")
    # Ambiguous cases must be left untouched, not silently re-encoded.
    assert "第III相試験" in html
    assert "(1)主要評価項目(2)" in html
    assert "<picture>" in html and "<source" in html


def test_requires_delivery_flags(tmp_path: Path) -> None:
    m3_input = tmp_path / "m3-input"
    write_m3_input(m3_input, "<main><p>Hi</p></main>")
    result = run("--direction", "m3-to-medichannel", "--input", str(m3_input), "--output", str(tmp_path / "out"))
    assert result.returncode != 0
    assert "--content-root" in result.stderr
