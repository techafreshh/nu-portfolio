"""Validate HTML tag balance, local refs, and the v2 project contract.

Checks every ``*.html`` file at the repo root plus every
``built/*/index.html`` page: tags must balance, local ``href``/``src``
targets must exist, and absolute local paths are rejected. Per-page
checks derived from ``assets/data/projects.json`` lock the link rules
(public GitHub URL verbatim in the links row, no ``github.com`` for
private repos), the ``Live`` placeholder, About coverage, wrap-around
prev/next order, the per-page byte budget, and local-only scripts.
Exits non-zero on any failure so CI can fail the build.
"""

import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

# Elements that never require a closing tag per the HTML spec.
VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)

# Matches absolute URIs (https:, mailto:, tel:, data:) — anything with
# a scheme — so external/placeholder refs can be skipped.
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")

# Matches CSS url(...) values with optional quotes/whitespace, so local
# @font-face targets can be existence-checked like HTML href/src refs.
CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")\s]+)['\"]?\s*\)")

REPO_ROOT = Path(__file__).resolve().parent.parent

# v1 closing sweep (issue #10): size budget, hygiene, and content bars.
SIZE_BUDGET_BYTES = 30720
BUDGET_FILES = ("index.html", "assets/styles.css", "assets/app.js")
LAYOUT_FILES = (
    "index.html",
    "assets/styles.css",
    "assets/app.js",
    "assets/favicon.svg",
    "404.html",
    "robots.txt",
)
FORBIDDEN_PATTERNS = (
    "googletag",
    "analytics",
    "document.cookie",
    "Project One",
    "Project Two",
    "Project Three",
    "Project Four",
)
REQUIRED_INDEX_STRINGS = ("TODO:", "I'm", "mailto:")
REQUIRED_CSS_STRINGS = (
    "max-width: 40rem",
    "clamp(3rem, 1.8rem + 6vw, 4.6rem)",
    "prefers-color-scheme",
)
FORBIDDEN_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")

# v2 final sweep (issue #32): json-driven per-page contract bars.
EXPECTED_PROJECT_COUNT = 22
LIVE_LINK_HTML = '<a href="#">Live \u2197</a>'
PREV_LABEL = "\u2190 Previous"
NEXT_LABEL = "Next \u2192"
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
PROJECT_LINKS_RE = re.compile(
    r'<nav[^>]*class="[^"]*project-links[^"]*"[^>]*>(.*?)</nav>',
    re.IGNORECASE | re.DOTALL,
)
SCRIPT_SRC_RE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*[\"']([^\"']*)[\"']", re.IGNORECASE
)
BUILT_HREF_RE = re.compile(r'href="built/([^"/]+)/"')


def is_local_ref(value):
    """Return True if an href/src value points at a local file."""
    if not value or not value.strip():
        return False
    value = value.strip()
    if value.startswith("#"):
        return False
    if value.startswith("//"):
        return False
    if SCHEME_RE.match(value):
        return False
    return True


def strip_suffix(value):
    """Strip query string and fragment from a local ref."""
    ref = value.strip().split("#", 1)[0].split("?", 1)[0].strip()
    return ref


def resolve_ref(ref, html_file, repo_root):
    """Resolve a local ref to a filesystem path."""
    if ref.startswith("/"):
        return repo_root / ref.lstrip("/")
    return html_file.parent / ref


class PageChecker(HTMLParser):
    """Collect tag-balance errors and local href/src refs in one pass."""

    def __init__(self, html_file, repo_root):
        super().__init__(convert_charrefs=True)
        self.html_file = html_file
        self.repo_root = repo_root
        self.stack = []
        self.errors = []
        self.refs = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        for name, value in attrs:
            if name.lower() in ("href", "src") and value is not None:
                self.refs.append(value)
        if tag in VOID_ELEMENTS:
            return
        self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        for name, value in attrs:
            if name.lower() in ("href", "src") and value is not None:
                self.refs.append(value)
        # Explicit self-close (e.g. <div/>) needs no stack entry.

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in VOID_ELEMENTS:
            return
        if not self.stack:
            line, _ = self.getpos()
            self.errors.append(
                "%s: unexpected closing tag </%s> on line %d with nothing open"
                % (self.html_file.name, tag, line)
            )
            return
        open_tag, (open_line, _) = self.stack[-1]
        if open_tag == tag:
            self.stack.pop()
        else:
            line, _ = self.getpos()
            self.errors.append(
                "%s: mismatched tag on line %d: expected </%s> for <%s> opened on line %d, got </%s>"
                % (
                    self.html_file.name,
                    line,
                    open_tag,
                    open_tag,
                    open_line,
                    tag,
                )
            )
            # Pop the unclosed tag so one slip does not cascade.
            self.stack.pop()

    def finish(self):
        for open_tag, (open_line, _) in reversed(self.stack):
            self.errors.append(
                "%s: unclosed tag <%s> opened on line %d"
                % (self.html_file.name, open_tag, open_line)
            )
        self.stack.clear()


def check_file(html_file, repo_root):
    """Validate one HTML file; return a list of failure lines."""
    text = html_file.read_text(encoding="utf-8")
    checker = PageChecker(html_file, repo_root)
    try:
        checker.feed(text)
        checker.close()
    except Exception as exc:  # noqa: BLE001 — report parse crashes as failures
        return ["%s: failed to parse: %s" % (html_file.name, exc)]
    checker.finish()
    failures = list(checker.errors)
    for raw in checker.refs:
        if not is_local_ref(raw):
            continue
        ref = strip_suffix(raw)
        if not ref:
            continue
        target = resolve_ref(ref, html_file, repo_root)
        if not target.exists():
            try:
                shown = target.relative_to(repo_root)
            except ValueError:
                shown = target
            failures.append(
                "%s: missing local reference %r -> %s does not exist"
                % (html_file.name, raw, shown)
            )
    return failures


def check_css_file(css_file, repo_root):
    """Validate url(...) targets in one CSS file; return failure lines."""
    text = css_file.read_text(encoding="utf-8")
    failures = []
    for raw in CSS_URL_RE.findall(text):
        if not is_local_ref(raw):
            continue
        ref = strip_suffix(raw)
        if not ref:
            continue
        target = resolve_ref(ref, css_file, repo_root)
        if not target.exists():
            try:
                shown = target.relative_to(repo_root)
            except ValueError:
                shown = target
            failures.append(
                "%s: missing local reference %r -> %s does not exist"
                % (css_file.name, raw, shown)
            )
    return failures


def main():
    repo_root = REPO_ROOT
    failures = []
    for rel in LAYOUT_FILES:
        if not (repo_root / rel).exists():
            failures.append("layout: required file %s is missing" % rel)
    budget_total = 0
    for rel in BUDGET_FILES:
        target = repo_root / rel
        if target.exists():
            budget_total += target.stat().st_size
    if budget_total > SIZE_BUDGET_BYTES:
        failures.append(
            "budget: index.html + assets/styles.css + assets/app.js total %d bytes exceeds %d bytes"
            % (budget_total, SIZE_BUDGET_BYTES)
        )
    projects_file = repo_root / "assets" / "data" / "projects.json"
    projects = []
    try:
        projects_text = projects_file.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append("page: cannot read assets/data/projects.json: %s" % exc)
    else:
        try:
            projects_data = json.loads(projects_text)
        except json.JSONDecodeError as exc:
            failures.append(
                "page: invalid JSON in assets/data/projects.json: %s" % exc
            )
        else:
            listed = (
                projects_data.get("projects")
                if isinstance(projects_data, dict)
                else None
            )
            if not isinstance(listed, list) or len(listed) != EXPECTED_PROJECT_COUNT:
                found = len(listed) if isinstance(listed, list) else 0
                failures.append(
                    "page: assets/data/projects.json must hold %d projects, found %d"
                    % (EXPECTED_PROJECT_COUNT, found)
                )
            else:
                projects = listed
    index_file = repo_root / "index.html"
    index_text = ""
    if index_file.exists():
        index_text = index_file.read_text(encoding="utf-8")
        for required in REQUIRED_INDEX_STRINGS:
            if required not in index_text:
                failures.append(
                    "content: index.html is missing required string %r" % required
                )
    css_file = repo_root / "assets" / "styles.css"
    if css_file.exists():
        css_text = css_file.read_text(encoding="utf-8")
        for required in REQUIRED_CSS_STRINGS:
            if required not in css_text:
                failures.append(
                    "content: assets/styles.css is missing required string %r" % required
                )
    html_files = sorted(repo_root.glob("*.html"))
    built_dir = repo_root / "built"
    if built_dir.is_dir():
        html_files.extend(
            sorted(p for p in built_dir.rglob("*.html") if p.is_file())
        )
    scan_targets = list(html_files)
    assets_dir = repo_root / "assets"
    if assets_dir.is_dir():
        scan_targets.extend(
            sorted(
                p
                for p in assets_dir.rglob("*")
                if p.is_file() and p.suffix in (".html", ".css", ".js", ".svg")
            )
        )
    for target in scan_targets:
        if not target.exists():
            continue
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            shown = target.relative_to(repo_root)
        except ValueError:
            shown = target
        for forbidden in FORBIDDEN_PATTERNS:
            if forbidden in text:
                failures.append(
                    "%s: forbidden pattern %r found (no trackers/cookies)"
                    % (shown, forbidden)
                )
        for host in FORBIDDEN_HOSTS:
            if host in text:
                failures.append(
                    "%s: forbidden third-party host %r found" % (shown, host)
                )
    if not html_files:
        print("validate: no *.html files found at repo root")
        return 1
    for html_file in html_files:
        failures.extend(check_file(html_file, repo_root))
    css_files = sorted(repo_root.rglob("*.css"))
    for css_path in css_files:
        failures.extend(check_css_file(css_path, repo_root))
    raw_ref_re = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)
    for html_file in html_files:
        text = html_file.read_text(encoding="utf-8")
        for raw in raw_ref_re.findall(text):
            if raw.strip().startswith("/"):
                failures.append(
                    "%s: absolute local path %r must be relative for subpath support"
                    % (html_file.name, raw)
                )
    order = [
        project.get("slug", "")
        for project in projects
        if isinstance(project, dict)
    ]
    total = len(projects)
    for i, project in enumerate(projects):
        if not isinstance(project, dict):
            failures.append("page: project at index %d is not an object" % i)
            continue
        slug = project.get("slug", "")
        name = project.get("name", "")
        page = repo_root / "built" / slug / "index.html"
        if not page.exists():
            failures.append("page: built/%s/index.html is missing" % slug)
            continue
        text = page.read_text(encoding="utf-8")
        heading = H1_RE.search(text)
        if heading is None or html.escape(name, quote=False) not in heading.group(1):
            failures.append(
                "page: built/%s/index.html is missing <h1> with the project name"
                % slug
            )
        tagline = project.get("tagline", "")
        if not tagline or html.escape(tagline, quote=False) not in text:
            failures.append(
                "page: built/%s/index.html is missing the project tagline" % slug
            )
        if "<h2>About</h2>" not in text:
            failures.append(
                "page: built/%s/index.html is missing <h2>About</h2>" % slug
            )
        about = project.get("about")
        if isinstance(about, str) and about.strip():
            if html.escape(about.strip(), quote=False) not in text:
                failures.append(
                    "page: built/%s/index.html is missing the About body" % slug
                )
        elif "TODO" not in text:
            failures.append(
                "page: built/%s/index.html is missing the About TODO" % slug
            )
        links = PROJECT_LINKS_RE.search(text)
        if links is None:
            failures.append(
                "page: built/%s/index.html is missing the project-links nav" % slug
            )
        else:
            block = links.group(1)
            if LIVE_LINK_HTML not in block:
                failures.append(
                    "page: built/%s/index.html links row is missing the Live placeholder"
                    % slug
                )
            if "TODO" not in block:
                failures.append(
                    "page: built/%s/index.html links row is missing the Live TODO"
                    % slug
                )
            github = project.get("github")
            if isinstance(github, str) and github:
                if github not in block:
                    failures.append(
                        "page: built/%s/index.html links row is missing %r"
                        % (slug, github)
                    )
            elif "github.com" in block:
                failures.append(
                    "page: built/%s/index.html links row must not link github.com (private repo)"
                    % slug
                )
        prev_project = projects[(i - 1) % total]
        next_project = projects[(i + 1) % total]
        prev_slug = prev_project.get("slug", "") if isinstance(prev_project, dict) else ""
        next_slug = next_project.get("slug", "") if isinstance(next_project, dict) else ""
        prev_name = prev_project.get("name", "") if isinstance(prev_project, dict) else ""
        next_name = next_project.get("name", "") if isinstance(next_project, dict) else ""
        if (
            "../%s/" % prev_slug not in text
            or PREV_LABEL not in text
            or html.escape(prev_name, quote=False) not in text
        ):
            failures.append(
                "page: built/%s/index.html has the wrong previous link (want ../%s/)"
                % (slug, prev_slug)
            )
        if (
            "../%s/" % next_slug not in text
            or NEXT_LABEL not in text
            or html.escape(next_name, quote=False) not in text
        ):
            failures.append(
                "page: built/%s/index.html has the wrong next link (want ../%s/)"
                % (slug, next_slug)
            )
    if index_file.exists() and order:
        built_hrefs = BUILT_HREF_RE.findall(index_text)
        if built_hrefs != order:
            failures.append(
                "content: index.html Built entries are out of order "
                "(want data order from assets/data/projects.json)"
            )
    styles_file = repo_root / "assets" / "styles.css"
    app_file = repo_root / "assets" / "app.js"
    shared_bytes = 0
    for shared in (styles_file, app_file):
        if shared.exists():
            shared_bytes += shared.stat().st_size
    for slug in order:
        if not slug:
            continue
        page = repo_root / "built" / slug / "index.html"
        if page.exists():
            page_total = page.stat().st_size + shared_bytes
            if page_total > SIZE_BUDGET_BYTES:
                failures.append(
                    "budget: built/%s/index.html + shared CSS/JS total %d bytes exceeds %d bytes"
                    % (slug, page_total, SIZE_BUDGET_BYTES)
                )
    # The style.css compat alias was removed on main as an unreferenced
    # duplicate (b3e5ed1); the canonical budget file is styles.css, which
    # every page references relatively. Only lock byte-identity when the
    # alias exists so the check passes with or without it.
    alias_file = repo_root / "assets" / "style.css"
    if (
        alias_file.exists()
        and styles_file.exists()
        and alias_file.read_bytes() != styles_file.read_bytes()
    ):
        failures.append(
            "budget: assets/style.css differs from assets/styles.css "
            "(alias must be byte-identical)"
        )
    for html_file in html_files:
        text = html_file.read_text(encoding="utf-8")
        for raw in SCRIPT_SRC_RE.findall(text):
            value = raw.strip()
            if SCHEME_RE.match(value) or value.startswith("//"):
                try:
                    shown = html_file.relative_to(repo_root)
                except ValueError:
                    shown = html_file
                failures.append(
                    "%s: third-party script src %r (only local scripts allowed)"
                    % (shown, raw)
                )
    if failures:
        for line in failures:
            print(line)
        print("validate: FAILED (%d problem(s))" % len(failures))
        return 1
    print("validate: OK (%d file(s) checked)" % len(html_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
