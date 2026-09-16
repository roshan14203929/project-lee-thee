#!/usr/bin/env python3
"""Perform deterministic static checks on generated HTML/CSS output."""

from __future__ import annotations

import html as html_module
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def options(values: list[str]) -> dict[str, str]:
    return {values[index].removeprefix("--"): values[index + 1] for index in range(0, len(values), 2)}


def is_within(root: Path, target: Path) -> bool:
    return target == root or root in target.parents


ROOT = Path(__file__).resolve().parent.parent


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resolve_spec(root: Path, args: dict[str, str]) -> dict[str, object]:
    """Determine flat vs. MediChannel-JCR output shape.

    Auto-detects from the candidate's own candidate.json (written by kit.py's
    `new-candidate`) so the normal orchestrated invocation needs no extra
    flags. A native MediChannel build is flat -- the same contract as
    html5/M3 -- for the whole BUILDING/VERIFYING/REFINING lifecycle; only a
    channel-conversion run's own candidates (run.json's
    `convertedFrom.direction == "m3-to-medichannel"`, produced by
    convert-platform.py's genuine HTML5->XHTML transform) are nested from
    creation, so auto-detect only resolves to "jcr" for those. Legacy
    candidate.json data with no `runId`, or a run.json that can't be read,
    defaults to flat -- native is the norm now, not the exception.

    Falls back to explicit --platform/--content-root/--dam-root/--css-root/
    --article-path for ad hoc invocations with no candidate.json present --
    this is also the documented way to independently validate a
    *materialized* nested tree (releases/v-###/jcr/,
    runs/<run>/materialized/materialized-###/jcr/), which has no
    candidate.json of its own.
    """
    platform = args.get("platform")
    content_root = args.get("content-root")
    dam_root = args.get("dam-root")
    css_root = args.get("css-root")
    article_path = args.get("article-path")
    candidate_meta = read_json(root / "candidate.json")
    project_id = candidate_meta.get("projectId")
    auto_detect = not platform and bool(project_id)
    conversion = False
    if auto_detect:
        project = read_json(ROOT / "projects" / str(project_id) / "project.json")
        platform = project.get("platform")
        delivery = project.get("delivery") or {}
        content_root = content_root or delivery.get("contentRoot")
        dam_root = dam_root or delivery.get("damRoot")
        css_root = css_root or delivery.get("cssRoot")
        page_id = candidate_meta.get("pageId")
        if page_id and not article_path:
            page = read_json(ROOT / "projects" / str(project_id) / "pages" / str(page_id) / "page.json")
            article_path = page.get("articlePath")
        run_id = candidate_meta.get("runId")
        if page_id and run_id:
            run = read_json(ROOT / "projects" / str(project_id) / "pages" / str(page_id) / "runs" / str(run_id) / "run.json")
            conversion = (run.get("convertedFrom") or {}).get("direction") == "m3-to-medichannel"
    if platform != "medichannel" or (auto_detect and not conversion):
        return {"kind": "flat"}
    missing = [
        name for name, value in (
            ("--content-root", content_root), ("--dam-root", dam_root),
            ("--css-root", css_root), ("--article-path", article_path),
        ) if not value
    ]
    if missing:
        raise ValueError(
            f"MediChannel verification requires: {', '.join(missing)} "
            "(read from the candidate's project/page, or pass explicitly)."
        )
    return {"kind": "jcr", "articlePath": article_path, "contentRoot": content_root, "damRoot": dam_root, "cssRoot": css_root}


def jcr_paths(spec: dict[str, object]) -> tuple[Path, Path, Path, Path]:
    article = Path(str(spec["articlePath"]))
    html_rel = Path("content") / str(spec["contentRoot"]) / f"{spec['articlePath']}.html"
    assets_rel = Path("content") / "dam" / str(spec["damRoot"]) / article
    css_dir = Path("etc") / "designs" / "code" / str(spec["cssRoot"]) / article
    return html_rel, assets_rel, css_dir / "base.css", css_dir / "page.css"


def visible_text(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", " ", value, flags=re.I)
    value = re.sub(r"<style\b[^>]*>[\s\S]*?</style>", " ", value, flags=re.I)
    # Accessible text carried in attributes (image alt, aria-label, title) is real
    # page content. Collect it before tags are stripped so an inventory item that
    # is rendered only as image alt text is not falsely reported missing. This is
    # required for XHTML/MediChannel figures whose description lives in alt="".
    attrs = re.findall(r"(?:\balt|\baria-label|\btitle)\s*=\s*\"([^\"]*)\"", value, flags=re.I)
    attrs += re.findall(r"(?:\balt|\baria-label|\btitle)\s*=\s*'([^']*)'", value, flags=re.I)
    # Named inline phrasing elements (span, em, strong, etc.) used for rich-text
    # emphasis do not introduce visual word gaps. When such a tag is surrounded
    # on BOTH sides by visible text (non-whitespace, non-tag-boundary chars),
    # remove it silently so inventory substring checks still pass.
    # Tags at block boundaries (preceded by whitespace/">" or followed by "<"),
    # and void/block elements like <br> and <img>, are left for the next sub
    # which converts them to spaces — correctly handling adjacent-span heading
    # patterns where the tag provides the only word separator.
    _inline_phrasing = (
        r"a|span|em|strong|b|i|u|s|abbr|acronym|cite|code|dfn|kbd|mark|q|samp"
        r"|small|sub|sup|time|var|bdi|bdo|data|ruby|rb|rt|rtc|rp|wbr"
    )
    value = re.sub(
        rf"(?<=[^\s>])</?(?:{_inline_phrasing})\b[^>]*>(?=[^\s<])",
        "", value, flags=re.I,
    )
    value = re.sub(r"<[^>]+>", " ", value)
    value = value + " " + " ".join(attrs)
    return re.sub(r"\s+", " ", html_module.unescape(value).replace("\xa0", " ")).strip()


def main() -> int:
    args = options(sys.argv[1:])
    if not args.get("root"):
        raise ValueError(
            "Usage: verify-output.py --root <generated-dir> [--inventory content-inventory.json] "
            "[--output report.json] [--platform html5|medichannel] [--content-root <path>] "
            "[--dam-root <path>] [--css-root <path>] [--article-path <path>]"
        )
    root = Path(args["root"]).resolve()
    # The default must NOT land inside root: this script enforces an exact-set
    # payload contract on root, so writing the report there makes the next run fail.
    default_output = root.parent / f"{root.name}-technical-report.json"
    output = Path(args.get("output", str(default_output))).resolve()
    if is_within(root, output):
        raise ValueError(f"--output must not be written inside the validated payload: {output}")
    findings: list[dict[str, object]] = []

    def add(identifier: str, severity: str, message: str, evidence: object = None) -> None:
        findings.append({"id": identifier, "severity": severity, "message": message, "section": None, "evidence": evidence, "suggestedFix": None})

    def text_of(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    spec = resolve_spec(root, args)
    if spec["kind"] == "flat":
        index_path, base_css_path, page_css_path, images_dir = root / "index.html", root / "base.css", root / "page.css", root / "images"
    else:
        html_rel, assets_rel, base_rel, page_rel = jcr_paths(spec)
        index_path, base_css_path, page_css_path, images_dir = root / html_rel, root / base_rel, root / page_rel, root / assets_rel

    document = text_of(index_path)
    base_css, page_css = text_of(base_css_path), text_of(page_css_path)
    css = f"{base_css}\n{page_css}"
    if not document:
        add("missing-index", "critical", f"{index_path.relative_to(root).as_posix()} is missing or empty.")
    if not base_css:
        add("missing-base-css", "critical", f"{base_css_path.relative_to(root).as_posix()} is missing or empty.")
    if not page_css:
        add("missing-page-css", "critical", f"{page_css_path.relative_to(root).as_posix()} is missing or empty.")
    if not images_dir.is_dir():
        add("missing-images", "critical", f"{images_dir.relative_to(root).as_posix()}/ is missing or is not a directory.")

    if spec["kind"] == "flat":
        expected = ["base.css", "images", "index.html", "page.css"]
        try:
            # candidate.json is lifecycle metadata, structural-check/ is
            # pre-acceptance diagnostic evidence, and _conversion-input/ is the
            # frozen source payload for a channel-conversion candidate (per the
            # artifact contract, all three live in the candidate dir). None of
            # them are part of the deployable payload.
            found = sorted(entry.name for entry in root.iterdir() if entry.name not in ("candidate.json", "structural-check", "_conversion-input"))
        except Exception:
            found = []
        if found != expected:
            add("invalid-output-structure", "critical", f"Deployable output must contain exactly: {', '.join(expected)}. Found: {', '.join(found)}.")
    else:
        assets_rel = images_dir.relative_to(root)
        allowed_files = {index_path.relative_to(root), base_css_path.relative_to(root), page_css_path.relative_to(root)}
        allowed_dirs = {
            p for rel in (*allowed_files, assets_rel)
            for p in rel.parents if p != Path(".")
        } | {assets_rel}
        stray: list[str] = []
        for entry in sorted(root.rglob("*")):
            rel = entry.relative_to(root)
            if rel.parts[0] in ("candidate.json", "structural-check", "_conversion-input"):
                continue
            if rel == assets_rel or assets_rel in rel.parents:
                continue
            if entry.is_dir():
                if rel not in allowed_dirs:
                    stray.append(rel.as_posix() + "/")
            elif rel not in allowed_files:
                stray.append(rel.as_posix())
        if stray:
            add("invalid-output-structure", "critical", f"Deployable output contains unexpected entries not part of the JCR payload: {', '.join(stray)}.")
    # Accept the HTML5 shorthand (<!doctype html>) and the full XHTML 1.0 Strict
    # DOCTYPE, which may be preceded by an <?xml ...?> declaration. MediChannel
    # deliveries are XHTML 1.0 Strict, not HTML5.
    if document and not re.match(r"^\s*(?:<\?xml\b[^>]*\?>\s*)?<!doctype\s+html\b", document, flags=re.I):
        add("missing-doctype", "high", "Document is missing an HTML doctype.")
    if document and not re.search(r"<html\b[^>]*\blang=[\"'][^\"']+[\"']", document, flags=re.I):
        add("missing-lang", "high", "The html element has no language.")
    if document and not re.search(r"<title>\s*[^<]+\s*</title>", document, flags=re.I):
        add("missing-title", "high", "Document title is missing or empty.")
    if document and not re.search(r"<meta\b[^>]*name=[\"']viewport[\"']", document, flags=re.I):
        add("missing-viewport", "high", "Viewport metadata is missing.")
    # Count main landmarks as either a literal <main> element or an element
    # carrying role="main". XHTML 1.0 Strict has no <main>, so MediChannel uses
    # <div id="main" role="main">. Subtract the overlap so <main role="main">
    # is not double-counted.
    main_elements = len(re.findall(r"<main\b", document, flags=re.I))
    role_main = len(re.findall(r"role\s*=\s*[\"']main[\"']", document, flags=re.I))
    main_overlap = len(re.findall(r"<main\b[^>]*role\s*=\s*[\"']main[\"']", document, flags=re.I))
    if document and (main_elements + role_main - main_overlap) != 1:
        add("main-count", "high", "Document must contain exactly one main landmark (<main> or role=\"main\").")
    if document and len(re.findall(r"<h1\b", document, flags=re.I)) != 1:
        add("h1-count", "high", "Document must contain exactly one h1.")
    if re.search(r"\sstyle\s*=", document, flags=re.I):
        add("inline-style", "medium", "Inline style attributes are not allowed.")
    if re.search(r"!important\b", css, flags=re.I):
        add("important", "medium", "CSS contains !important.")
    # Remote-runtime: flag resource-loading attributes (src on any element; href on
    # non-anchor elements like <link>, <base>). Regular <a href="https://..."> hyperlinks
    # are valid external navigation and must not be flagged as remote resources.
    has_remote_src = bool(re.search(r"\bsrc=[\"']https?://", document, flags=re.I))
    has_remote_link = bool(re.search(r"<link\b[^>]*\bhref=[\"']https?://", document, flags=re.I))
    has_remote_css_url = bool(re.search(r"url\(\s*[\"']?https?://", css, flags=re.I))
    if has_remote_src or has_remote_link or has_remote_css_url:
        add("remote-runtime", "high", "Generated output contains remote runtime resources.")
    if re.search(r"\b(lorem ipsum|todo|placeholder text|replace me)\b", document, flags=re.I):
        add("placeholder-content", "high", "Generated output contains placeholder content.")

    references = set(re.findall(r"(?:src|href)=[\"']([^\"'#?]+)[\"']", document, flags=re.I))
    references.update(re.findall(r"url\(\s*[\"']?([^\"')?#]+)[\"']?\s*\)", css, flags=re.I))
    # MediChannel image/asset references are document-root-absolute AEM DAM paths
    # (/content/dam/<damRoot>/<articlePath>/...), not relative. Resolve those back
    # into the local candidate tree so they get the same broken-reference check as
    # every relative reference, instead of being silently skipped as "absolute".
    dam_prefix = f"/content/dam/{spec['damRoot']}/{spec['articlePath']}/" if spec["kind"] == "jcr" else None
    for reference in references:
        if dam_prefix and reference.startswith(dam_prefix):
            local = (images_dir / reference[len(dam_prefix):]).resolve()
            if not is_within(root, local):
                add("unsafe-reference", "critical", f"Asset reference escapes generated root: {reference}")
            elif not local.exists():
                add("broken-reference", "high", f"Local asset does not exist: {reference}")
            continue
        # Skip non-local schemes (external URLs, data URIs, mailto, tel, etc.)
        if re.match(r"^(?:https?:|data:|mailto:|tel:|javascript:|//)", reference, flags=re.I) or reference.startswith("/"):
            continue
        target = (root / reference).resolve()
        if not is_within(root, target):
            add("unsafe-reference", "critical", f"Asset reference escapes generated root: {reference}")
        elif not target.exists():
            add("broken-reference", "high", f"Local asset does not exist: {reference}")

    if args.get("inventory"):
        inventory = json.loads(Path(args["inventory"]).resolve().read_text(encoding="utf-8"))
        text = visible_text(document)
        for item in inventory.get("items", []):
            required_text = str(item.get("text", ""))
            normalized = re.sub(r"\s+", " ", required_text).strip()
            if item.get("required") and required_text and normalized not in text:
                add(f"missing-content-{item.get('id')}", "critical", f"Required source content is missing: {required_text}", item.get("id"))

    try:
        files = sorted(file.name for file in root.iterdir())
    except Exception:
        files = []
    report = {"kind": "technical", "status": "FAIL" if findings else "PASS", "checkedAt": now(), "summary": f"{len(findings)} technical or content-integrity issue(s) found." if findings else "Static output checks passed.", "findings": findings, "files": files}
    output.parent.mkdir(parents=True, exist_ok=True)
    pretty = json.dumps(report, indent=2) + "\n"
    compact = json.dumps(report, separators=(",", ":")) + "\n"
    output.write_text(pretty, encoding="utf-8")
    sys.stdout.write(compact)
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        raise SystemExit(str(error))
