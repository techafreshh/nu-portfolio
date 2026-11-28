# PRD v2 — nu-portfolio: Built → project pages

**Status:** ready for factory slicing
**Owner:** techafreshh
**Supersedes:** PRD v1 (`.agents/PRDs/PRD.md`, kept for history) for the Built
section and the content model. Everything else in v1 — the visual contract,
quality bars, accessibility, and technical constraints — carries forward
unchanged and binds the work below.

## 1. Shipped so far (context)

The initial page plus eleven factory laps delivered: the static shell with
extracted assets, favicon + head metadata + theme-color, a standalone 404 page,
robots.txt, empty states, the focus/contrast pass, self-hosted Inter and
JetBrains Mono, a print stylesheet, CI that validates HTML and local assets,
the final acceptance sweep, and CSS `url()` target validation.

## 2. What v2 adds

Clicking a project in **Built** plays a full-screen ink curtain carrying the
project's name, then lands on a per-project page. The Built list holds the
owner's 22 real projects, revealed five at a time behind a "Show more" control.
A single data file plus a generator script replaces hand-edited project
markup. Runtime stays static, zero-build, and complete without JavaScript.

## 3. Content model (amends v1 §8)

- `assets/data/projects.json` is the single source of truth for Built entries
  and project pages: an ordered list of
  `{slug, name, tagline, about, github, live, year}`. The `about` field is the
  owner's detailed description; `null` falls back to two TODO placeholder
  paragraphs.
- `scripts/generate.py` (Python 3 stdlib only, run from the repo root)
  renders:
  - the Built `<ul>` between `<!-- BUILT:START -->` and `<!-- BUILT:END -->`
    markers in `index.html`, leaving every other byte of the file untouched,
    and
  - `built/<slug>/index.html` for every entry.
- Generated output is committed. Serving requires no build, install, or
  bundler, and no JavaScript renders content at runtime. The generator is a
  content tool the owner runs, never something the server needs.
- `null` fields: `github` → no GitHub link rendered at all;
  `live` → placeholder `href="#"` marked `TODO`; `year` → no year shown,
  `TODO` comment in its place.
- The four placeholder entries ("Project One" … "Project Four") are deleted.

## 4. Home: Built section

- 22 entries in the order of `projects.json` (§7).
- Entry: the title links to `built/<slug>/`; the verbatim tagline sits beneath
  in `--ink-soft`; no year column.
- Progressive reveal: with JavaScript, exactly the first 5 entries are visible
  on load; a "Show more" control beneath the list reveals 5 more per click and
  disappears once everything is visible. The collapsed state is applied by the
  pre-paint bootstrap (it may set `html[data-js]` in addition to the theme) so
  there is no flash of the full list. Without JavaScript, all 22 entries are
  visible and linked and the control is hidden. All content is in the served
  HTML either way — the control only toggles visibility.
- The Said section is untouched.

## 5. Ink curtain transition

- **Trigger:** a Built entry link, activated by a plain left click or keyboard
  Enter, when JavaScript is on and `prefers-reduced-motion: reduce` is not set.
  Modified clicks (middle, ctrl/cmd/shift) and no-JS follow the plain link.
- **Sequence:** the default action is prevented; a fixed full-screen panel
  colored `var(--ink)` slides up from the bottom edge (`translateY(100%)` →
  `0`) over ~450ms with an eased curve; the project's display name sits
  centered in `var(--bg)` at the same type scale as the home name; navigation
  then proceeds to `built/<slug>/`.
- The panel is decorative: `aria-hidden`, no focus is trapped, and focus stays
  on the activated link until navigation.
- The project page plays **no** entrance animation — the name is already the
  hero — so the handoff reads as one continuous move.
- `prefers-reduced-motion`: skip the overlay entirely; navigate immediately.

## 6. Project pages

- **Path:** `built/<slug>/index.html`, with relative asset paths
  (`../../assets/...`) so subpath hosting works.
- Same shell as home: tokens, Inter / JetBrains Mono, theme bootstrap + toggle
  for both themes, 40rem column. No name scramble.
- **Split hero** on desktop: a two-column grid spanning the hero area — the
  project name (`h1`) sits vertically centered in the left half, and the
  details stack on the right half: the verbatim tagline (kicker), the meta
  row (mono, year when present, omitted otherwise), and the links row (styled
  like Find me: "Live ↗" for every project with a placeholder `href="#"` +
  `TODO`; "GitHub ↗" only when `github` is set). The `h1` uses its own smaller
  display clamp
  (roughly `clamp(2.4rem, 1.6rem + 4vw, 3.6rem)`) so long names like
  `digital-products-factory` wrap and fit; the column never scrolls
  horizontally. Below the existing 34rem breakpoint the hero stacks: name
  first, details beneath.
- Layout, top to bottom:
  1. back link "← Built" → `../../`
  2. split hero (name left / details right, per above)
  3. "About" (`h2`) — the `about` field rendered as body text; when `about`
     is `null`, two short `TODO` placeholder paragraphs instead
  4. picture band: two images using the shared `assets/img/placeholder.svg`,
     each with `alt="<Name> screenshot — replace with a real screenshot"`, and
     `TODO` comments marking where real screenshots go
  5. prev/next navigation in `projects.json` order with wrap-around, labeled
     "← Previous" / "Next →" with the neighbor's name
- `<head>`: title `<Name> — Your Name`, description = tagline; no canonical
  until the domain exists. `robots.txt` and `404.html` are unchanged.

## 7. Data (committed with this PRD)

`assets/data/projects.json` — 22 projects in reveal order:

aura\*, pi-dark-factory, redline, digital-products-factory\*, argus,
decision-cortex, engram, website-factory\*, bi-ai-ui, scribe\*, room-brain,
longform\*, gatekeep, reins, kintsugi, magpie, financial-assistant\*,
yt-clipping, arc-rag, repo-reader, scrapline, techa-dl-bot

(\* = private repo; its GitHub link is omitted. Taglines are the owner's
verbatim text.)

## 8. Acceptance criteria

Served from the repo root:

1. `GET /` contains 22 Built links to `built/<slug>/` in the §7 order, a
   "Show more" control, and the `html[data-js]` pre-paint bootstrap.
2. With JavaScript off, all 22 entries are visible and linked; the control is
   hidden.
3. `GET /built/<slug>/` returns 200 for all 22 slugs; each page contains its
   `h1` name, the verbatim tagline, the About body text where `about` is set,
   a Live placeholder link, and prev/next neighbors that match the §7 order
   with wrap-around. The hero renders as a two-column split on desktop and
   stacks below 34rem.
4. Public repos link to `https://github.com/techafreshh/<repo>`. Private repos
   contain no `github.com` link in their links row.
5. `assets/app.js` implements the curtain; reduced-motion and no-JS paths
   navigate directly.
6. The placeholder entries no longer appear anywhere.
7. The existing runtime and holdout scenarios stay green, and CI validation
   passes on all new pages.

## 9. Quality bars (carried from v1)

AA contrast in both themes; HTML+CSS+JS ≤ 30 KB per page excluding fonts and
images; no third-party JavaScript; correct from 320px up with no horizontal
scroll; everything works with JavaScript disabled.

## 10. Technical constraints (carried from v1)

Static files only. `python3 -m http.server` serves the site from the repo root
for verification; nothing may require a runtime build, install, or bundler.
Relative asset paths everywhere. No client-side routing.

## 11. Slicing guidance

This amendment ships as **one issue**: the split hero + About section on all
22 pages (generator template + CSS) with the `about` fields already committed
in `projects.json`. The "The build" section is replaced by About. The
existing runtime scenario must stay green; new probes are added by the
operator after merge.

## 12. Operator checklist (not factory issues)

- Provide real live URLs; replace the placeholder screenshots; add years if
  wanted; prettify display names in `projects.json` if desired.
- Choose a domain and a static host; add the canonical URL once fixed.
- Replace the Said placeholders with real essays.
