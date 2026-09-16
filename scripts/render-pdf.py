#!/usr/bin/env python3
"""Render an accepted HTML candidate to PDF.

Ground-truthed against a real M3 build and its real PDF export (same
ticket): base.css/page.css/images are byte-identical between the HTML and
PDF deliverable, and the only HTML changes are non-content interactive
elements wrapped in an HTML comment (never deleted, never unwrapped) plus,
separately, targeted U+2060 WORD JOINER fixes a human/agent applies after
visually reviewing a bad line/page break -- this script never inserts word
joiners itself, only re-renders after they are added.
"""

from __future__ import annotations

import asyncio
import json
import mimetypes
import re
import shutil
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.async_api import async_playwright

MIME = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
MM_PER_INCH = 25.4
CSS_PX_PER_INCH = 96


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, str]:
    return {values[index].removeprefix("--"): values[index + 1] for index in range(0, len(values), 2)}


def local_server(root: Path, entry: str) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                pathname = unquote(urlsplit(self.path).path)
                file = (root / ((entry if pathname == "/" else pathname.lstrip("/")))).resolve()
                if file != root and root not in file.parents:
                    raise ValueError("Unsafe path")
                if file.is_dir():
                    file /= entry
                body = file.read_bytes()
                self.send_response(200)
                self.send_header("content-type", MIME.get(file.suffix.lower()) or mimetypes.guess_type(str(file))[0] or "application/octet-stream")
                self.send_header("cache-control", "no-store")
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_response(404)
                self.end_headers()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    return server


# ----------------------------------------------------------------------------
# Comment-wrap pass. Wraps whole <nav>...</nav> blocks (balanced via depth
# counting, since nav can in principle nest) and standalone external CTA
# anchors (target="_blank", which anchors cannot legally nest, so a
# non-greedy match is safe). Everything else that could plausibly be
# interactive-but-content-bearing is only flagged, never touched.
# ----------------------------------------------------------------------------

def wrap_balanced_blocks(html: str, tag: str, wrapped: list[dict[str, object]]) -> str:
    pattern = re.compile(rf"<{tag}\b[^>]*>|</{tag}\s*>", re.I)
    spans: list[tuple[int, int]] = []
    depth = 0
    start = None
    for m in pattern.finditer(html):
        if not m.group(0).startswith("</"):
            if depth == 0:
                start = m.start()
            depth += 1
        else:
            depth = max(0, depth - 1)
            if depth == 0 and start is not None:
                spans.append((start, m.end()))
                start = None
    for s, e in reversed(spans):
        block = html[s:e]
        wrapped.append({"type": tag, "text": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", block)).strip()[:80]})
        html = html[:s] + f"<!-- {block} -->" + html[e:]
    return html


EXTERNAL_BLANK_A_RE = re.compile(r'<a\b[^>]*\btarget\s*=\s*["\']_blank["\'][^>]*>.*?</a>', re.I | re.S)
BUTTON_RE = re.compile(r"<button\b[^>]*>.*?</button>", re.I | re.S)
EXTERNAL_A_RE = re.compile(r'<a\b(?![^>]*target\s*=\s*["\']_blank["\'])[^>]*\bhref\s*=\s*["\']https?://[^"\']*["\'][^>]*>.*?</a>', re.I | re.S)


def strip_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def apply_strip_pass(html: str) -> tuple[str, list[dict[str, object]], list[dict[str, object]]]:
    wrapped: list[dict[str, object]] = []
    flagged: list[dict[str, object]] = []
    html = wrap_balanced_blocks(html, "nav", wrapped)

    def wrap_blank_a(m: re.Match[str]) -> str:
        wrapped.append({"type": "a[target=_blank]", "text": strip_text(m.group(0))[:80]})
        return f"<!-- {m.group(0)} -->"

    html = EXTERNAL_BLANK_A_RE.sub(wrap_blank_a, html)
    for m in BUTTON_RE.finditer(html):
        flagged.append({"type": "button", "text": strip_text(m.group(0))[:80], "message": "No real-world evidence for automatic button stripping; confirm this is a pure action control before comment-wrapping it by hand."})
    for m in EXTERNAL_A_RE.finditer(html):
        flagged.append({"type": "external-link", "text": strip_text(m.group(0))[:80], "message": "External link without target=\"_blank\" is ambiguous (could be a citation, not a pure CTA); confirm before comment-wrapping."})
    return html, wrapped, flagged


async def _render(args: dict[str, str]) -> int:
    if not args.get("root") or not args.get("output"):
        raise ValueError("Usage: render-pdf.py --root <accepted-candidate-or-current> --output <index.pdf> [--entry index.html] [--width 960] [--page-format A4] [--strip-report report.json]")
    root = Path(args["root"]).resolve()
    output = Path(args["output"]).resolve()
    entry = args.get("entry", "index.html")
    width = int(args.get("width", "960"))
    page_format = args.get("page-format", "A4")
    strip_report_path = Path(args["strip-report"]).resolve() if args.get("strip-report") else output.parent / f"{output.stem}-strip-report.json"

    work_dir = output.parent / f"{output.stem}-stripped"
    shutil.rmtree(work_dir, ignore_errors=True)
    shutil.copytree(root, work_dir)
    entry_path = work_dir / entry
    stripped_html, wrapped, flagged = apply_strip_pass(entry_path.read_text(encoding="utf-8"))
    entry_path.write_text(stripped_html, encoding="utf-8")

    server = local_server(work_dir, entry)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={"width": width, "height": 1000})
                response = await page.goto(f"http://127.0.0.1:{server.server_port}/{entry}", wait_until="networkidle")
                if response is None or not response.ok:
                    status = response.status if response is not None else "unknown"
                    raise ValueError(f"Preview returned HTTP {status}.")
                await page.emulate_media(media="print")
                await page.evaluate("() => document.fonts?.ready")
                output.parent.mkdir(parents=True, exist_ok=True)
                await page.pdf(path=str(output), format=page_format, print_background=True)
                page_height_mm = 297.0 if page_format.upper() == "A4" else 279.4
                page_height_px = page_height_mm / MM_PER_INCH * CSS_PX_PER_INCH
                straddling = await page.evaluate(
                    """(pageHeight) => {
                      const results = [];
                      document.querySelectorAll('h1,h2,h3,h4,img,table,figure').forEach((el) => {
                        const r = el.getBoundingClientRect();
                        const top = r.top + window.scrollY;
                        const bottom = r.bottom + window.scrollY;
                        for (let boundary = pageHeight; boundary < bottom; boundary += pageHeight) {
                          if (boundary > top && boundary < bottom) {
                            results.push({tag: el.tagName.toLowerCase(), text: (el.textContent || '').trim().slice(0, 60), topPx: Math.round(top), bottomPx: Math.round(bottom), boundaryPx: Math.round(boundary)});
                            break;
                          }
                        }
                      });
                      return results;
                    }""",
                    page_height_px,
                )
            finally:
                await browser.close()
    finally:
        server.shutdown()
        server.server_close()

    page_count = None
    try:
        pdf_bytes = output.read_bytes()
        page_count = len(re.findall(rb"/Type\s*/Page[^s]", pdf_bytes))
    except Exception:
        pass

    report = {
        "status": "REVIEW_NEEDED" if flagged or straddling else "OK",
        "checkedAt": now(),
        "output": str(output),
        "pageCount": page_count,
        "pageHeightPx": round(page_height_px),
        "straddlingElements": straddling,
        "commentWrapped": wrapped,
        "flaggedInteractive": flagged,
    }
    strip_report_path.parent.mkdir(parents=True, exist_ok=True)
    strip_report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n")
    return 0 if report["status"] == "OK" else 2


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    try:
        raise SystemExit(asyncio.run(_render(options(sys.argv[1:]))))
    except Exception as error:
        raise SystemExit(str(error))
