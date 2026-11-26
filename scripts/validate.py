"""Validate HTML tag balance and local href/src references.

Walks every ``*.html`` file at the repo root, checks that tags are
balanced, and checks that every local ``href``/``src`` target exists
on disk. External URLs, fragments, and empty refs are skipped.
Exits non-zero on any failure so CI can fail the build.
"""

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

REPO_ROOT = Path(__file__).resolve().parent.parent


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


def main():
    repo_root = REPO_ROOT
    html_files = sorted(repo_root.glob("*.html"))
    if not html_files:
        print("validate: no *.html files found at repo root")
        return 1
    failures = []
    for html_file in html_files:
        failures.extend(check_file(html_file, repo_root))
    if failures:
        for line in failures:
            print(line)
        print("validate: FAILED (%d problem(s))" % len(failures))
        return 1
    print("validate: OK (%d file(s) checked)" % len(html_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
