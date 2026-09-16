#!/usr/bin/env python3
"""Mechanically transform an accepted candidate between M3/HTML5 and MediChannel/XHTML.

Applies only what is mechanically unambiguous (doctype/head swap, the
structural-element table, void-element/boolean-attribute/quoting syntax,
ampersand escaping, the one-directional-safe halves of the character-entity
rules, asset-path rewrite, and the flat<->JCR output-shape move). Everything
else — a plain-ASCII Roman numeral, a parenthesized number that might be a
flattened circled digit, an element with no XHTML alternative, a CSS unit or
specificity choice — is left untouched and reported in `flagged` for a human
or agent to resolve. This script never guesses.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import jcr_paths  # noqa: E402  (reuse the JCR path geometry kit.py already defines)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
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


# ----------------------------------------------------------------------------
# Attribute parsing/rendering — shared by the structural remap and the
# quoting/void/boolean syntax passes.
# ----------------------------------------------------------------------------

ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"|([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*\'([^\']*)\'')


def parse_attrs(s: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in ATTR_RE.finditer(s or ""):
        if m.group(1) is not None:
            out[m.group(1)] = m.group(2)
        else:
            out[m.group(3)] = m.group(4)
    return out


def render_attrs(attrs: dict[str, str]) -> str:
    order = ["id", "class", "role"]
    keys = [k for k in order if k in attrs] + [k for k in attrs if k not in order]
    return "".join(f' {k}="{attrs[k]}"' for k in keys)


VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


# ----------------------------------------------------------------------------
# Structural element table (guidelines/medichannel/coding/xhtml-syntax.md
# "Available Structural Elements"). Each entry: html5 tag -> (xhtml wrapper
# tag, fixed class token or None, fixed role or None, fixed id or None).
# ----------------------------------------------------------------------------

STRUCTURAL = [
    ("main", "div", None, "main", "main"),
    ("section", "div", "section", "region", None),
    ("article", "div", "article", "article", None),
    ("nav", "div", "nav", "navigation", None),
    ("header", "div", "header", "banner", None),
    ("footer", "div", "footer", "contentinfo", None),
    ("aside", "div", "aside", "complementary", None),
    ("figure", "div", "figure", None, None),
    ("figcaption", "p", "figcaption", None, None),
    ("mark", "span", "mark", None, None),
    ("time", "span", "time", None, None),
]
FORWARD = {html5: (wrapper, cls, role, fixed_id) for html5, wrapper, cls, role, fixed_id in STRUCTURAL}
PROHIBITED_NO_ALTERNATIVE = {"picture", "source", "video", "audio", "canvas", "details", "summary", "dialog", "datalist", "output", "progress", "meter", "template"}

TOKEN_RE = re.compile(r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<[^>]+>|[^<]+", re.S)
TAGNAME_RE = re.compile(r"^</?\s*([a-zA-Z][a-zA-Z0-9:_-]*)")
PROTECT_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)


def protect_scripts(html: str) -> tuple[str, list[str]]:
    """Replace <script>/<style> blocks with placeholders so tag content inside
    them (which may contain literal '<'/'>' in JS/CSS) never confuses the
    tag tokenizer used by the structural remap."""
    blocks: list[str] = []

    def stash(m: re.Match[str]) -> str:
        blocks.append(m.group(0))
        return f"\x00PROTECTED-BLOCK-{len(blocks) - 1}\x00"

    return PROTECT_RE.sub(stash, html), blocks


def restore_scripts(html: str, blocks: list[str]) -> str:
    for i, block in enumerate(blocks):
        html = html.replace(f"\x00PROTECTED-BLOCK-{i}\x00", block)
    return html


def backward_match(name: str, attrs: dict[str, str]) -> tuple[str, str, str, str | None] | None:
    """For a generic div/p/span in a MediChannel document, decide whether it
    carries one of our structural sentinel markers and should be rewritten
    back to its HTML5 original. Returns (html5_tag, wrapper, cls, role) or
    None if this is just an ordinary div/p/span."""
    for html5, wrapper, cls, role, fixed_id in STRUCTURAL:
        if wrapper != name:
            continue
        if fixed_id and attrs.get("id") == fixed_id:
            return html5, wrapper, cls, role
        if role and attrs.get("role") == role:
            return html5, wrapper, cls, role
        if not fixed_id and not role and cls:
            classes = (attrs.get("class") or "").split()
            if cls in classes:
                return html5, wrapper, cls, role
    return None


def remap_structural(html: str, direction: str, flagged: list[dict[str, object]]) -> str:
    protected, blocks = protect_scripts(html)
    out: list[str] = []
    stack: list[tuple[str, str | None]] = []  # (original tag name, rewritten tag name or None)
    for tok in TOKEN_RE.findall(protected):
        if not tok.startswith("<") or tok.startswith("<!") or tok.startswith("<?"):
            out.append(tok)
            continue
        m = TAGNAME_RE.match(tok)
        if not m:
            out.append(tok)
            continue
        name = m.group(1).lower()
        closing = tok.startswith("</")
        if closing:
            if stack and stack[-1][0] == name:
                _orig, rewritten = stack.pop()
                out.append(f"</{rewritten or name}>")
            else:
                out.append(tok)
            continue
        self_closing = tok.rstrip().endswith("/>") or name in VOID_ELEMENTS
        body = tok[len(name) + 1:]
        body = body[:-2] if tok.rstrip().endswith("/>") else body[:-1]
        attrs = parse_attrs(body)
        rewritten_name: str | None = None
        if direction == "m3-to-medichannel" and name in FORWARD:
            wrapper, cls, role, fixed_id = FORWARD[name]
            if cls:
                attrs["class"] = f"{cls} {attrs['class']}" if attrs.get("class") else cls
            if role:
                attrs["role"] = role
            if fixed_id:
                attrs["id"] = fixed_id
            rewritten_name = wrapper
        elif direction == "m3-to-medichannel" and name in PROHIBITED_NO_ALTERNATIVE:
            flagged.append({"type": "prohibited-element", "tag": name, "message": f"<{name}> has no XHTML alternative; requires manual rework."})
        elif direction == "medichannel-to-m3" and name in ("div", "p", "span"):
            match = backward_match(name, attrs)
            if match:
                html5, _wrapper, cls, role = match
                if cls and attrs.get("class"):
                    remaining = " ".join(t for t in attrs["class"].split() if t != cls)
                    if remaining:
                        attrs["class"] = remaining
                    else:
                        attrs.pop("class", None)
                if role:
                    attrs.pop("role", None)
                if html5 == "main":
                    attrs.pop("id", None)
                rewritten_name = html5
        final_name = rewritten_name or name
        out.append(f"<{final_name}{render_attrs(attrs)}{' /' if self_closing and name in VOID_ELEMENTS else ''}>")
        if not self_closing:
            stack.append((name, rewritten_name))
    return restore_scripts("".join(out), blocks)


# ----------------------------------------------------------------------------
# Doctype / <html> / charset meta swap.
# ----------------------------------------------------------------------------

DOCTYPE_HTML5_RE = re.compile(r"<!doctype\s+html\s*>\s*<html\b([^>]*)>", re.I)
DOCTYPE_XHTML_RE = re.compile(r"(?:<\?xml\b[^>]*\?>\s*)?<!doctype\s+html\s+public[^>]*>\s*<html\b([^>]*)>", re.I)
CHARSET_HTML5_RE = re.compile(r'<meta\s+charset\s*=\s*["\']utf-8["\']\s*/?>', re.I)
CHARSET_XHTML_RE = re.compile(r'<meta\s+http-equiv\s*=\s*["\']Content-Type["\']\s+content\s*=\s*["\']text/html;\s*charset=UTF-8["\']\s*/?>', re.I)


def doctype_to_xhtml(html: str) -> str:
    m = DOCTYPE_HTML5_RE.search(html)
    if not m:
        return html
    attrs = parse_attrs(m.group(1))
    lang = attrs.get("lang", "ja")
    prologue = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        f'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}" lang="{lang}">'
    )
    html = html[: m.start()] + prologue + html[m.end():]
    return CHARSET_HTML5_RE.sub('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />', html)


def doctype_to_html5(html: str) -> str:
    m = DOCTYPE_XHTML_RE.search(html)
    if not m:
        return html
    attrs = parse_attrs(m.group(1))
    lang = attrs.get("lang") or attrs.get("xml:lang") or "ja"
    html = html[: m.start()] + f'<!doctype html>\n<html lang="{lang}">' + html[m.end():]
    return CHARSET_XHTML_RE.sub('<meta charset="utf-8">', html)


# ----------------------------------------------------------------------------
# Void-element self-close / boolean-attribute / quoting syntax (M3->MediChannel
# only -- HTML5 tolerates either form, XHTML requires the strict form).
# ----------------------------------------------------------------------------

BOOL_ATTRS = ("disabled", "checked", "selected", "readonly", "required", "multiple", "autofocus")
BOOL_RE = re.compile(r"(?<![-\w])(" + "|".join(BOOL_ATTRS) + r")\b(?!\s*=)", re.I)
TAG_RE = re.compile(r"<[a-zA-Z!?][^>]*>")


def _fix_tag(tag: str) -> str:
    tag = re.sub(r"([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*'([^']*)'", r'\1="\2"', tag)
    tag = re.sub(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*([^\s"\'>/][^\s>]*)', r'\1="\2"', tag)
    tag = BOOL_RE.sub(lambda m: f'{m.group(1)}="{m.group(1).lower()}"', tag)
    return tag


def normalize_syntax(html: str) -> str:
    protected, blocks = protect_scripts(html)
    protected = TAG_RE.sub(lambda m: _fix_tag(m.group(0)), protected)

    def close_void(m: re.Match[str]) -> str:
        tag = m.group(0)
        return tag if tag.rstrip().endswith("/>") else tag[:-1].rstrip() + " />"

    protected = re.sub(r"<(?:" + "|".join(VOID_ELEMENTS) + r")\b[^>]*>", close_void, protected, flags=re.I)
    return restore_scripts(protected, blocks)


# ----------------------------------------------------------------------------
# Ampersand escaping (M3->MediChannel only).
# ----------------------------------------------------------------------------

BARE_AMP_RE = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")


def escape_ampersands(html: str) -> str:
    return BARE_AMP_RE.sub("&amp;", html)


# ----------------------------------------------------------------------------
# Character-entity direction. Only the mechanically-safe halves are applied;
# the ambiguous halves are reported in `flagged`, never guessed.
# ----------------------------------------------------------------------------

ROMAN_MAP = {
    0x2160: "I", 0x2161: "II", 0x2162: "III", 0x2163: "IV", 0x2164: "V", 0x2165: "VI",
    0x2166: "VII", 0x2167: "VIII", 0x2168: "IX", 0x2169: "X", 0x216A: "XI", 0x216B: "XII",
    0x2170: "i", 0x2171: "ii", 0x2172: "iii", 0x2173: "iv", 0x2174: "v", 0x2175: "vi",
    0x2176: "vii", 0x2177: "viii", 0x2178: "ix", 0x2179: "x", 0x217A: "xi", 0x217B: "xii",
}
CIRCLED_DIGIT_MAP = {0x2460 + i: f"({i + 1})" for i in range(20)}
CURATED_GLYPHS = {0x3231: "(株)", 0x3232: "(有)", 0x3239: "(代)", **CIRCLED_DIGIT_MAP}
DECODABLE = {**ROMAN_MAP, **CURATED_GLYPHS}
NUMERIC_ENTITY_RE = re.compile(r"&#(x?[0-9a-fA-F]+);")
ROMAN_LITERAL_RE = re.compile("[" + "".join(chr(c) for c in ROMAN_MAP) + "]")
ASCII_ROMAN_RE = re.compile(r"(?<![A-Za-z])(I{1,3}|IV|VI{0,3}|IX|X)(?![A-Za-z])")


def decode_entities_medichannel_to_m3(html: str, flagged: list[dict[str, object]]) -> str:
    def repl(m: re.Match[str]) -> str:
        raw = m.group(1)
        codepoint = int(raw[1:], 16) if raw[:1] in ("x", "X") else int(raw)
        return DECODABLE.get(codepoint, m.group(0))

    html = NUMERIC_ENTITY_RE.sub(repl, html)

    def literal_repl(m: re.Match[str]) -> str:
        return ROMAN_MAP.get(ord(m.group(0)), m.group(0))

    return ROMAN_LITERAL_RE.sub(literal_repl, html)


def flag_ambiguous_migrations(html: str, flagged: list[dict[str, object]]) -> None:
    # Roman numerals as plain ASCII letters are not mechanically re-encodable
    # (III is ambiguous with ordinary text) -- flag only near a real risk
    # context (a Japanese "phase" heading), never a blanket match.
    for m in re.finditer(r"第([IVX]{1,4})相", html):
        flagged.append({"type": "roman-numeral-candidate", "text": m.group(0), "context": html[max(0, m.start() - 20): m.end() + 20], "message": "Plain-ASCII Roman numeral next to 第...相 (\"Phase ...\"); confirm before re-encoding to a Unicode Roman numeral entity."})
    # A parenthesized number may be a circled digit M3 already flattened, or
    # genuine parenthetical text -- always flagged, never auto-converted.
    for m in re.finditer(r"\((\d{1,2})\)", html):
        n = int(m.group(1))
        if 1 <= n <= 20:
            flagged.append({"type": "circled-digit-candidate", "text": m.group(0), "context": html[max(0, m.start() - 20): m.end() + 20], "message": "Cross-reference content-inventory.json's original text before deciding whether this was a flattened circled digit."})


# ----------------------------------------------------------------------------
# Main transform.
# ----------------------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def apply_html(html: str, direction: str, flagged: list[dict[str, object]]) -> str:
    if direction == "m3-to-medichannel":
        html = normalize_syntax(html)
        html = remap_structural(html, direction, flagged)
        html = doctype_to_xhtml(html)
        html = escape_ampersands(html)
        flag_ambiguous_migrations(html, flagged)
    else:
        html = remap_structural(html, direction, flagged)
        html = doctype_to_html5(html)
        html = decode_entities_medichannel_to_m3(html, flagged)
    return html


def rewrite_asset_paths(html: str, css: str, direction: str, delivery: dict[str, str] | None) -> tuple[str, str]:
    if direction == "m3-to-medichannel":
        assert delivery is not None
        dam_prefix = f"/content/dam/{delivery['damRoot']}/{delivery['articlePath']}/"
        css_prefix = f"/etc/designs/code/{delivery['cssRoot']}/{delivery['articlePath']}/"
        html = html.replace('src="images/', f'src="{dam_prefix}')
        html = re.sub(r'href="(?:\./)?base\.css"', f'href="{css_prefix}base.css"', html)
        html = re.sub(r'href="(?:\./)?page\.css"', f'href="{css_prefix}page.css"', html)
        css = re.sub(r"url\((['\"]?)(?:\.\./)?images/", rf"url(\1{dam_prefix}", css)
    else:
        assert delivery is not None
        dam_prefix = f"/content/dam/{delivery['damRoot']}/{delivery['articlePath']}/"
        css_prefix = f"/etc/designs/code/{delivery['cssRoot']}/{delivery['articlePath']}/"
        html = html.replace(f'src="{dam_prefix}', 'src="images/')
        html = html.replace(f'href="{css_prefix}base.css"', 'href="base.css"')
        html = html.replace(f'href="{css_prefix}page.css"', 'href="page.css"')
        css = css.replace(f"url({dam_prefix}", "url(images/").replace(f"url('{dam_prefix}", "url('images/").replace(f'url("{dam_prefix}', 'url("images/')
    return html, css


def main(argv: list[str]) -> int:
    o = options(argv)
    direction = o.get("direction")
    if direction not in ("m3-to-medichannel", "medichannel-to-m3"):
        raise ValueError("Usage: convert-platform.py --direction m3-to-medichannel|medichannel-to-m3 --input <dir> --output <dir> [--content-root --dam-root --css-root --article-path] --output-report <report.json>")
    input_dir = Path(o["input"]).resolve()
    output_dir = Path(o["output"]).resolve()
    report_path = Path(o["output-report"]).resolve() if o.get("output-report") else output_dir.parent / f"{output_dir.name}-conversion-report.json"
    flagged: list[dict[str, object]] = []

    if direction == "m3-to-medichannel":
        for flag in ("content-root", "dam-root", "css-root", "article-path"):
            if not o.get(flag):
                raise ValueError(f"--{flag} is required for --direction m3-to-medichannel.")
        delivery = {"damRoot": o["dam-root"], "cssRoot": o["css-root"], "articlePath": o["article-path"], "contentRoot": o["content-root"]}
        html = apply_html(read_text(input_dir / "index.html"), direction, flagged)
        base_css, page_css = read_text(input_dir / "base.css"), read_text(input_dir / "page.css")
        html, base_css = rewrite_asset_paths(html, base_css, direction, delivery)
        _html2, page_css = rewrite_asset_paths("", page_css, direction, delivery)
        html_rel, assets_rel, base_rel, page_rel, _css_dir = jcr_paths({"articlePath": delivery["articlePath"], "contentRoot": delivery["contentRoot"], "damRoot": delivery["damRoot"], "cssRoot": delivery["cssRoot"]})
        (output_dir / html_rel).parent.mkdir(parents=True, exist_ok=True)
        (output_dir / html_rel).write_text(html, encoding="utf-8")
        (output_dir / base_rel).parent.mkdir(parents=True, exist_ok=True)
        (output_dir / base_rel).write_text(base_css, encoding="utf-8")
        (output_dir / page_rel).write_text(page_css, encoding="utf-8")
        (output_dir / assets_rel).mkdir(parents=True, exist_ok=True)
        images_dir = input_dir / "images"
        if images_dir.is_dir():
            for f in images_dir.iterdir():
                if f.is_file():
                    (output_dir / assets_rel / f.name).write_bytes(f.read_bytes())
    else:
        for flag in ("content-root", "dam-root", "css-root", "article-path"):
            if not o.get(flag):
                raise ValueError(f"--{flag} is required for --direction medichannel-to-m3.")
        delivery = {"damRoot": o["dam-root"], "cssRoot": o["css-root"], "articlePath": o["article-path"], "contentRoot": o["content-root"]}
        html_rel, assets_rel, base_rel, page_rel, _css_dir = jcr_paths({"articlePath": delivery["articlePath"], "contentRoot": delivery["contentRoot"], "damRoot": delivery["damRoot"], "cssRoot": delivery["cssRoot"]})
        html = apply_html(read_text(input_dir / html_rel), direction, flagged)
        base_css, page_css = read_text(input_dir / base_rel), read_text(input_dir / page_rel)
        html, base_css = rewrite_asset_paths(html, base_css, direction, delivery)
        _html2, page_css = rewrite_asset_paths("", page_css, direction, delivery)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text(html, encoding="utf-8")
        (output_dir / "base.css").write_text(base_css, encoding="utf-8")
        (output_dir / "page.css").write_text(page_css, encoding="utf-8")
        (output_dir / "images").mkdir(exist_ok=True)
        assets_dir = input_dir / assets_rel
        if assets_dir.is_dir():
            for f in assets_dir.iterdir():
                if f.is_file():
                    (output_dir / "images" / f.name).write_bytes(f.read_bytes())

    report = {"direction": direction, "checkedAt": now(), "flagged": flagged, "status": "REVIEW_NEEDED" if flagged else "OK"}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sys.stdout.write(json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    # Converted documents are UTF-8 and routinely contain Japanese text; on a
    # cp1252 console, printing the report raises UnicodeEncodeError and the
    # agent gets no report at all.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        raise SystemExit(str(error))
