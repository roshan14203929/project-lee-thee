#!/usr/bin/env python3
"""Materialize a flat, native MediChannel candidate into the nested AEM/JCR tree.

Native MediChannel candidates build/repair/QA in the same flat shape as
HTML5/M3 (index.html, base.css, page.css, images/) and are already required
(by page-builder.md's self-check, backed by guidelines/medichannel/coding/
xhtml-syntax.md) to be valid XHTML 1.0 Strict while still flat. This is
therefore deliberately NOT convert-platform.py's m3-to-medichannel transform
-- that script exists to convert genuine HTML5 semantic markup into XHTML for
a cross-platform-ported page, and re-running its structural/doctype/entity
remap on already-XHTML-compliant flat output would be a no-op at best and
corrupt correct markup at worst. This script only splices and rewrites paths:
it drops the flat candidate's <title> and <body> content into the matching
marker regions of a stored delivery-template shell (see
delivery-templates/medichannel/<template>/), and rewrites relative asset
paths into the document-root-absolute DAM/CSS paths the delivered artifact
requires. Everything else in the shell -- the fixed site chrome outside the
markers -- is never touched.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import ROOT, DEFAULT_TEMPLATE, jcr_paths, dam_prefix, css_prefix, payload  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, object]:
    out: dict[str, object] = {}
    i = 0
    while i < len(values):
        if values[i].startswith("--"):
            key = values[i][2:]
            val = values[i + 1] if i + 1 < len(values) and not values[i + 1].startswith("--") else True
            out[key] = val
            i += 2 if val is not True else 1
        else:
            i += 1
    return out


def extract_title_and_body(html: str) -> tuple[str, str]:
    title_match = re.search(r"<title>(.*?)</title>", html, re.S)
    if not title_match:
        raise ValueError("Flat candidate's index.html has no <title> element.")
    body_open = re.search(r"<body\b[^>]*>", html, re.I)
    body_close = html.rfind("</body>")
    if not body_open or body_close == -1 or body_close < body_open.end():
        raise ValueError("Flat candidate's index.html has no well-formed <body>...</body>.")
    return title_match.group(1).strip(), html[body_open.end():body_close]


def slice_between(text: str, start_marker: str, end_marker: str) -> tuple[int, int, str]:
    if start_marker not in text or end_marker not in text:
        raise ValueError(f"Delivery template shell is missing an expected marker: {start_marker!r} / {end_marker!r}.")
    s = text.index(start_marker) + len(start_marker)
    e = text.index(end_marker, s)
    return s, e, text[s:e]


def replace_between(text: str, start_marker: str, end_marker: str, new_inner: str) -> str:
    s, e, _ = slice_between(text, start_marker, end_marker)
    return text[:s] + new_inner + text[e:]


CSS_URL_RE = re.compile(r"url\((['\"]?)(?:\.\./)?images/")


def rewrite_css_urls(css: str, dam: str) -> str:
    return CSS_URL_RE.sub(rf"url(\1{dam}", css)


def main(argv: list[str]) -> int:
    o = options(argv)
    for flag in ("input", "output", "content-root", "dam-root", "css-root", "article-path"):
        if not o.get(flag) or o.get(flag) is True:
            raise ValueError(
                "Usage: materialize-medichannel.py --input <flat-dir> --output <dir> "
                "--content-root <> --dam-root <> --css-root <> --article-path <> "
                "[--template 1column] [--template-root <dir>] --output-report <report.json>"
            )
    input_dir = Path(str(o["input"])).resolve()
    output_dir = Path(str(o["output"])).resolve()
    template = str(o.get("template") or DEFAULT_TEMPLATE)
    # --template-root exists only so tests can point at a small fixture
    # template instead of the real, 1700+ line shell; production callers
    # never need it.
    template_root = Path(str(o["template-root"])).resolve() if o.get("template-root") else ROOT / "delivery-templates" / "medichannel"
    report_path = Path(str(o["output-report"])).resolve() if o.get("output-report") else output_dir.parent / f"{output_dir.name}-materialization-report.json"

    payload(input_dir, "Materialization input", {"kind": "flat"})

    template_dir = template_root / template
    shell_path = template_dir / "shell.html"
    manifest_path = template_dir / "manifest.json"
    if not shell_path.exists() or not manifest_path.exists():
        raise ValueError(f"Unknown MediChannel delivery template: {template} (expected {shell_path}).")
    shell = shell_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    markers = manifest["markers"]

    html = (input_dir / "index.html").read_text(encoding="utf-8")
    title, body_inner = extract_title_and_body(html)
    if re.search(r"<script\b", body_inner, re.I):
        raise ValueError(
            "Flat candidate's body contains a <script> tag. The delivery template's JS marker "
            "is reserved but not populated automatically -- resolve this by hand before materializing."
        )

    spec = {"kind": "jcr", "articlePath": o["article-path"], "contentRoot": o["content-root"], "damRoot": o["dam-root"], "cssRoot": o["css-root"]}
    dam = dam_prefix(spec)
    css = css_prefix(spec)

    body_inner = body_inner.replace('src="images/', f'src="{dam}')
    base_css = rewrite_css_urls((input_dir / "base.css").read_text(encoding="utf-8"), dam)
    page_css = rewrite_css_urls((input_dir / "page.css").read_text(encoding="utf-8"), dam)

    shell = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", shell, count=1, flags=re.S)
    head_s, head_e, head_slice = slice_between(shell, markers["headCssStart"], markers["headCssEnd"])
    head_slice = re.sub(r'href="[^"]*?base\.css"', f'href="{css}base.css"', head_slice)
    head_slice = re.sub(r'href="[^"]*?page\.css"', f'href="{css}page.css"', head_slice)
    shell = shell[:head_s] + head_slice + shell[head_e:]
    shell = replace_between(shell, markers["bodyStart"], markers["bodyEnd"], f"\n{body_inner.strip()}\n")

    html_rel, assets_rel, base_rel, page_rel, _css_dir = jcr_paths(spec)
    (output_dir / html_rel).parent.mkdir(parents=True, exist_ok=True)
    (output_dir / html_rel).write_text(shell, encoding="utf-8")
    (output_dir / base_rel).parent.mkdir(parents=True, exist_ok=True)
    (output_dir / base_rel).write_text(base_css, encoding="utf-8")
    (output_dir / page_rel).write_text(page_css, encoding="utf-8")
    (output_dir / assets_rel).mkdir(parents=True, exist_ok=True)
    images_dir = input_dir / "images"
    if images_dir.is_dir():
        for f in images_dir.iterdir():
            if f.is_file():
                (output_dir / assets_rel / f.name).write_bytes(f.read_bytes())

    payload(output_dir, "Materialized output", spec)

    report = {
        "status": "OK",
        "template": template,
        "templateSha256": manifest.get("sha256"),
        "checkedAt": now(),
        "filled": {"title": title, "headCss": True, "body": True},
        "findings": [],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        raise SystemExit(str(error))
