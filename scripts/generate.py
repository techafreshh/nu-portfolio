"""Regenerate the Built list and per-project pages from the data file.

Reads ``assets/data/projects.json`` (the single source of truth) and:

1. rewrites only the markup between ``<!-- BUILT:START -->`` and
   ``<!-- BUILT:END -->`` inside the Built ``<ul class="entries">`` in
   ``index.html``, leaving every other byte untouched, and
2. writes ``built/<slug>/index.html`` for every project in file order.

Run from the repo root::

    python3 scripts/generate.py

Stdlib only (``json``, ``html``, ``re``, ``sys``, ``pathlib``).
Exits non-zero with a message on bad input. Re-running without data
changes writes zero new bytes (idempotent).
"""

import html
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "assets" / "data" / "projects.json"
INDEX_FILE = REPO_ROOT / "index.html"
BUILT_DIR = REPO_ROOT / "built"

BUILT_RE = re.compile(r"(<!-- BUILT:START -->).*?(<!-- BUILT:END -->)", re.DOTALL)

EXPECTED_COUNT = 22

# Verbatim copy of the pre-paint theme bootstrap in index.html <head>.
BOOTSTRAP_JS = (
    "<script>\n"
    '  // Saved localStorage "theme" wins; otherwise the CSS prefers-color-scheme'
    " media query (tokens --bg/--accent in assets/styles.css) applies the OS"
    " theme \u2014 hence no flash.\n"
    "  try {\n"
    '    var saved = localStorage.getItem("theme");\n'
    '    if (saved === "light" || saved === "dark") {\n'
    '      document.documentElement.setAttribute("data-theme", saved);\n'
    "    }\n"
    "  } catch (e) {}\n"
    "</script>"
)

# Verbatim copy of the toggle markup in index.html body.
TOGGLE_HTML = (
    '  <div class="toggle-wrap">\n'
    '    <button class="toggle" id="theme-toggle" aria-label="Toggle light/dark theme" title="Toggle theme">\n'
    '      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>\n'
    "    </button>\n"
    "  </div>"
)

# Project-only rules; the shared stylesheet stays untouched.
PAGE_CSS = (
    "<style>\n"
    "  .back { margin-bottom: 1.6rem; }\n"
    "  .tagline { color: var(--ink-soft); margin-bottom: 1rem; }\n"
    "  .meta { font-family: var(--font-mono); font-size: 0.82rem; color: var(--ink-soft); margin-bottom: 1.4rem; }\n"
    "  .project-links { margin-bottom: 0.5rem; }\n"
    "  .shots { display: grid; gap: 1rem; margin: 2rem 0; }\n"
    "  .shots img { width: 100%; height: auto; display: block; border: 1px solid var(--rule); border-radius: 6px; }\n"
    "  .pager { display: flex; justify-content: space-between; gap: 1rem; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--rule); }\n"
    "</style>"
)


def fail(message):
    """Print an error to stderr and exit non-zero."""
    print("generate: error: %s" % message, file=sys.stderr)
    return 1


def load_projects():
    """Load and validate the ordered project list from the data file."""
    try:
        raw = DATA_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        return None, "cannot read %s: %s" % (DATA_FILE.name, exc)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, "invalid JSON in assets/data/projects.json: %s" % exc
    if not isinstance(data, dict) or not isinstance(data.get("projects"), list):
        return None, 'assets/data/projects.json must hold an object with a "projects" list'
    projects = data["projects"]
    if len(projects) != EXPECTED_COUNT:
        return None, "expected %d projects, found %d" % (EXPECTED_COUNT, len(projects))
    seen = set()
    for i, project in enumerate(projects):
        if not isinstance(project, dict):
            return None, "project at index %d is not an object" % i
        for key in ("slug", "name", "tagline"):
            value = project.get(key)
            if not isinstance(value, str) or not value.strip():
                return None, "project at index %d has a bad %r" % (i, key)
        for key in ("github", "live", "year"):
            value = project.get(key)
            if value is not None and not isinstance(value, str):
                return None, "project %r has a bad %r (want string or null)" % (
                    project.get("slug"),
                    key,
                )
        if project["slug"] in seen:
            return None, "duplicate slug %r" % project["slug"]
        seen.add(project["slug"])
    return projects, None


def render_built_block(projects):
    """Render the Built <li> entries in data order (no year column)."""
    lines = []
    for project in projects:
        lines.append(
            '      <li class="entry"><a class="entry-title link" href="built/'
            + html.escape(project["slug"], quote=True)
            + '/">'
            + html.escape(project["name"], quote=False)
            + '<span class="entry-sub">'
            + html.escape(project["tagline"], quote=False)
            + "</span></a></li>"
        )
    return "".join(line + "\n" for line in lines)


def render_page(project, prev_project, next_project):
    """Render one self-contained project page."""
    name = project["name"]
    tagline = project["tagline"]
    name_text = html.escape(name, quote=False)
    name_attr = html.escape(name, quote=True)
    tag_text = html.escape(tagline, quote=False)
    tag_attr = html.escape(tagline, quote=True)

    if project.get("year"):
        meta_inner = html.escape(str(project["year"]), quote=False)
    else:
        meta_inner = "<!-- TODO: add the year for " + name_attr + " when known. -->"

    links = []
    links.append('    <a href="#">Live \u2197</a>')
    links.append("    <!-- TODO: replace the Live placeholder for " + name_attr + " with the real URL. -->")
    if project.get("github"):
        links.append(
            '    <a href="'
            + html.escape(project["github"], quote=True)
            + '" target="_blank" rel="noopener noreferrer">GitHub \u2197</a>'
        )
    links_html = "\n".join(links)

    img_alt = name_attr + " screenshot \u2014 replace with a real screenshot"
    shots = []
    shots.append("    <!-- TODO: replace with a real screenshot of " + name_attr + ". -->")
    shots.append('    <img src="../../assets/img/placeholder.svg" alt="' + img_alt + '">')
    shots.append("    <!-- TODO: replace with a real screenshot of " + name_attr + ". -->")
    shots.append('    <img src="../../assets/img/placeholder.svg" alt="' + img_alt + '">')
    shots_html = "\n".join(shots)

    parts = []
    parts.append("<!DOCTYPE html>")
    parts.append('<html lang="en">')
    parts.append("<head>")
    parts.append('<meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    parts.append("<title>" + name_text + " \u2014 Your Name</title>")
    parts.append('<meta name="description" content="' + tag_attr + '">')
    parts.append('<meta property="og:title" content="' + name_attr + " \u2014 Your Name" + '">')
    parts.append('<meta property="og:description" content="' + tag_attr + '">')
    parts.append('<meta property="og:type" content="website">')
    parts.append('<meta name="twitter:card" content="summary">')
    parts.append('<meta name="theme-color" media="(prefers-color-scheme: light)" content="#ffffff">')
    parts.append('<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0d0d0d">')
    parts.append('<link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml">')
    parts.append('<link rel="stylesheet" href="../../assets/styles.css">')
    parts.append(PAGE_CSS)
    parts.append(BOOTSTRAP_JS)
    parts.append("</head>")
    parts.append("<body>")
    parts.append('<main class="shell">')
    parts.append(TOGGLE_HTML)
    parts.append("")
    parts.append('  <p class="back"><a class="link" href="../../">\u2190 Built</a></p>')
    parts.append('  <h1 class="name">' + name_text + "</h1>")
    parts.append('  <p class="tagline">' + tag_text + "</p>")
    parts.append('  <p class="meta">' + meta_inner + "</p>")
    parts.append('  <nav class="footer-links project-links" aria-label="Project links">')
    parts.append(links_html)
    parts.append("  </nav>")
    parts.append('  <div class="shots">')
    parts.append(shots_html)
    parts.append("  </div>")
    parts.append("  <h2>The build</h2>")
    parts.append("  <!-- TODO: describe how " + name_attr + " was built. -->")
    parts.append("  <p>Build notes coming soon.</p>")
    parts.append("  <!-- TODO: describe what " + name_attr + " does differently and what is next. -->")
    parts.append("  <p>More detail coming soon.</p>")
    parts.append('  <nav class="pager" aria-label="More projects">')
    parts.append(
        '    <a class="link" href="../'
        + html.escape(prev_project["slug"], quote=True)
        + '/">\u2190 Previous \u00b7 '
        + html.escape(prev_project["name"], quote=False)
        + "</a>"
    )
    parts.append(
        '    <a class="link" href="../'
        + html.escape(next_project["slug"], quote=True)
        + '/">Next \u2192 \u00b7 '
        + html.escape(next_project["name"], quote=False)
        + "</a>"
    )
    parts.append("  </nav>")
    parts.append("</main>")
    parts.append("")
    parts.append('<script src="../../assets/app.js" defer></script>')
    parts.append("</body>")
    parts.append("</html>")
    return "\n".join(parts) + "\n"


def rewrite_index(projects):
    """Replace only the marker block in index.html; return True if changed."""
    text = INDEX_FILE.read_text(encoding="utf-8")
    match = BUILT_RE.search(text)
    if match is None:
        return None, "index.html has no <!-- BUILT:START --> / <!-- BUILT:END --> block"
    # Rebuild from match spans so everything outside the markers is untouched.
    replacement = "<!-- BUILT:START -->\n" + render_built_block(projects) + "      <!-- BUILT:END -->"
    updated = text[: match.start()] + replacement + text[match.end() :]
    if updated == text:
        return False, None
    INDEX_FILE.write_text(updated, encoding="utf-8")
    return True, None


def write_pages(projects):
    """Write built/<slug>/index.html for every project; return count."""
    total = len(projects)
    for i, project in enumerate(projects):
        prev_project = projects[(i - 1) % total]
        next_project = projects[(i + 1) % total]
        page = render_page(project, prev_project, next_project)
        target = BUILT_DIR / project["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
    return total


def print_usage():
    print("usage: python3 scripts/generate.py [--help]")
    print("Rewrites the Built list in index.html and all built/<slug>/ pages")
    print("from assets/data/projects.json. Run from the repo root.")


def main(argv):
    if len(argv) > 1:
        if argv[1] in ("-h", "--help"):
            print_usage()
            return 0
        print_usage()
        return 2
    projects, error = load_projects()
    if error is not None:
        print("generate: error: %s" % error, file=sys.stderr)
        return 1
    changed, error = rewrite_index(projects)
    if error is not None:
        print("generate: error: %s" % error, file=sys.stderr)
        return 1
    count = write_pages(projects)
    print("generate: OK (%d project page(s) written%s)" % (count, "" if changed else "; index.html unchanged"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
