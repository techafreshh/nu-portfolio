# PRD — nu-portfolio

**Status:** ready for factory slicing
**Owner:** techafreshh
**Visual reference:** https://ibiang.xyz/ (layout, type, restraint — not its content)

## 1. What this is

A one-page personal portfolio: a short introduction, a list of writing, a list of
selected work, and a row of contact links. It is a static site — no framework, no
build step, no backend, no analytics. It should feel quiet, fast, and deliberate:
large name, generous whitespace, one narrow column, almost no chrome.

## 2. Goals

- **G1** A stranger landing on the page understands in ~10 seconds who the person
  is, what they have written, and what they have built.
- **G2** Every piece of content is editable in one obvious place, with no tooling.
- **G3** The page loads instantly on a phone and degrades gracefully without
  JavaScript.
- **G4** The look stays faithful to the reference: white/ink, Inter, a narrow
  measured column, one circular theme toggle.

## 3. Non-goals

- No CMS, database, API, auth, comments, contact form, or analytics.
- No framework and no build step. Files in the repo are the deployed files.
- No per-essay pages in v1: writing entries link out to wherever the essay lives.
- No blog engine, generated feeds, pagination, or search.
- No dark/light images, hero photos, or illustration systems.

## 4. Audience and voice

Recruiters, collaborators, and peers scanning quickly. First person, plain and
short. The reference's voice is the model: "I build software, and I read a lot."
No buzzwords, no third-person résumé prose.

## 5. Page structure

One page, one centered column, in this order:

1. **Hero** — faint `I'm`, the name at display size, three short bio paragraphs.
2. **Said** — writing entries: title left, year right, newest first.
3. **Built** — selected work: title plus a one-line description, year right.
4. **Find me** — a wrapping row of contact links (Email, GitHub, Substack, X,
   LinkedIn; drop any the owner does not use).

The one-word section labels are intentional and should stay short.

## 6. Visual contract

These values are not suggestions; the page must render with them.

### Color tokens

| token | light | dark |
|---|---|---|
| `--bg` | `#ffffff` | `#0d0d0d` |
| `--ink` | `#111111` | `#ededed` |
| `--ink-soft` | `#555555` | `#b5b5b5` |
| `--ink-faint` | `#767676` | `#8f8f8f` |
| `--rule` | `#eeeeee` | `#2a2a2a` |
| `--rule-strong` | `#d4d4d4` | `#3d3d3d` |
| `--accent` | `#2456d6` | `#7aa2ff` |

`--ink-faint` is deliberately darker than the reference's `#9a9a9a`: at 1.05rem
the reference value is ~2.8:1 on white and fails WCAG AA. `#767676` reads the
same and passes at 4.5:1.

### Type

- Sans: **Inter** (400/500/700); mono: **JetBrains Mono** (400) for years only.
- Body `1.05rem`, line-height `1.65`.
- Name: `clamp(3rem, 1.8rem + 6vw, 4.6rem)`, weight 700,
  letter-spacing `-0.03em`, line-height `1.05`.
- Section label: `1.5rem`, weight 700, letter-spacing `-0.01em`.
- Entry title `1.02rem`; entry year `0.82rem` mono, color `--ink-soft`.
- `font-variant-ligatures: none` on the name.

### Spacing and layout

- Column: `max-width: 40rem`, centered.
- Page padding: `clamp(4rem, 10vw, 7rem) clamp(1.25rem, 5vw, 2rem) 6rem`.
- Gap between sections: `clamp(3rem, 8vw, 4.5rem)`.
- Entries: flex, `align-items: baseline`, `justify-content: space-between`,
  `gap: 1rem`, vertical padding `0.35rem`.
- Below `34rem`: entries stack (title above year, `gap: 0.1rem`).
- Theme toggle: fixed top-right at `clamp(1.25rem, 4vw, 2rem)`, 2.3rem circle,
  1px `--rule-strong` border, transparent background, moon/sun icon at 1rem.

### Interaction

- Links: inherit color, underline in `--rule`, `text-underline-offset: 3px`;
  on hover color and underline become `--accent`.
- `::selection`: `--accent` background, `--bg` text.
- Theme change transitions background and color over `0.35s`.
- Toggle hover: accent color and border; active: `scale(0.94)`.

## 7. Functional requirements

**FR-1 — Semantic document.** One `<h1>`, `<h2>` per section, `<main>`,
`<footer>`, `<nav aria-label="Elsewhere">`, `lang="en"`, viewport meta.

**FR-2 — Hero content.** Faint `I'm` line, name heading, three bio paragraphs.
The content block is clearly marked so the owner can edit it without reading
markup.

**FR-3 — Said list.** Each entry: linked title, mono year on the right, newest
first. External links open in a new tab with `rel="noopener noreferrer"`. An
empty list renders a muted "Nothing published yet." line instead of a blank gap.

**FR-4 — Built list.** Same mechanics, plus a one-line description under each
title in `--ink-soft`. Empty state as in FR-3.

**FR-5 — Find me.** Email as `mailto:`, the rest external with
`rel="noopener noreferrer"`. The row wraps on narrow screens.

**FR-6 — Theme.** Follow the OS by default via `prefers-color-scheme`. A manual
toggle overrides it, persists in `localStorage` under `theme`, and the choice
wins on the next visit. No flash of the wrong theme: the saved value is applied
by an inline pre-paint script in `<head>`. The toggle icon reflects the active
theme and has an accessible label.

**FR-7 — Name scramble (progressive enhancement).** On first paint the name
resolves from random characters to the exact final text within ~650ms. It must
end on the exact text (no truncation), cause no layout shift, and be skipped
entirely under `prefers-reduced-motion: reduce`. With JavaScript off the name is
plain text.

**FR-8 — No-JS parity.** With JavaScript disabled, all content is visible, all
links work, and the theme follows the OS. Only the toggle and the scramble may
be inert.

**FR-9 — Responsive.** Correct from 320px up. No horizontal scrolling at any
width. Entries stack below 34rem. The toggle keeps a ≥24px hit area.

**FR-10 — Structure.** `index.html`, `assets/styles.css`, `assets/app.js`,
`assets/favicon.svg`, `404.html`, `robots.txt`. The only inline script allowed
is the pre-paint theme bootstrap; the only inline style allowed is none.

**FR-11 — Self-hosted fonts.** Inter and JetBrains Mono are served from
`assets/fonts/` with `@font-face` and `font-display: swap`. No request goes to
`fonts.googleapis.com` or `fonts.gstatic.com`. Include the OFL license text.

**FR-12 — Metadata.** Title, description, `og:title`, `og:description`,
`og:type`, `twitter:card`, `theme-color` for both color schemes, and an SVG
favicon referenced from `<head>`. Do not ship a placeholder canonical URL; add
it when the domain is chosen.

**FR-13 — 404 page.** `404.html` reuses the same shell and tokens, says the page
does not exist, and links home. No JavaScript required.

**FR-14 — robots.txt.** Allow all crawlers; no sitemap until there is more than
one indexable page.

**FR-15 — Accessibility.** Visible `:focus-visible` outline (2px `--accent`,
2px offset). Text contrast meets WCAG AA in both themes. The toggle has
`aria-label`. Nothing relies on color alone.

**FR-16 (stretch) — Print stylesheet.** A readable black-on-white print view
with links printed as text and the toggle hidden.

**FR-17 (stretch) — CI.** One GitHub Actions workflow that validates the HTML
and checks that referenced local assets exist.

## 8. Content model and placeholders

Content lives in `index.html` inside clearly marked blocks (`TODO: ...`
comments). No content is generated by JavaScript; the rendered HTML is the
source of truth.

Placeholder policy: the name, bio, entry titles, project names, and contact
links are placeholders in this first pass. They must be obviously editable and
marked with `TODO`. The owner replaces them; the factory must not invent real
links or identities. Placeholder external links must not point to unrelated live
sites.

## 9. Quality bars

- HTML + CSS + JS ≤ 30 KB uncompressed, excluding fonts.
- No third-party JavaScript, no trackers, no cookies.
- Font files ≤ 200 KB total.
- LCP < 2.5s on Slow 4G, CLS < 0.1.
- Works in current Chrome, Firefox, and Safari, and with JS disabled.

## 10. Technical constraints

- Static files only. `python3 -m http.server` must serve the site from the repo
  root for verification; nothing may require a build, install, or bundler.
- Relative asset paths so the site works from a subpath as well as a domain
  root (e.g. `/nu-portfolio/` on GitHub Pages).
- No dependency on client-side routing or history APIs.

## 11. Acceptance criteria

The site is acceptable when, served from the repo root:

1. `GET /` returns 200 and contains the hero, `Said`, `Built`, and `Find me`.
2. `GET /assets/styles.css` and `GET /assets/app.js` return 200.
3. The stylesheet contains both theme token blocks and the accent value.
4. The HTML references a local favicon and local fonts; no Google Fonts host.
5. `GET /404.html` returns 200 and contains a link to `/`.
6. `GET /robots.txt` returns 200.
7. An unknown path returns 404.
8. With JS disabled, content is complete and readable.
9. At 360px wide there is no horizontal overflow.
10. Both themes meet AA contrast for body text.

## 12. Current state (already in `main`)

The initial commit already contains: hero, Said, Built, Find me, both theme
token sets, OS-default theme, toggle with `localStorage` persistence, the inline
pre-paint bootstrap, the name scramble with reduced-motion handling, responsive
entry stacking, accent hover/selection, and title/description metadata.

**Do not re-slice these as new work.** The backlog is the delta described below.

## 13. Slicing guidance

- **Foundation first:** extract the inline CSS and JS into `assets/styles.css`
  and `assets/app.js` with zero visual or behavioral change. The pre-paint theme
  bootstrap stays inline. This issue unblocks the rest.
- Then independent leaves, each one file or one concern:
  favicon + metadata + theme-color; `404.html`; `robots.txt`; empty states;
  focus-visible + contrast pass; self-hosted fonts; print stylesheet (stretch);
  CI validation (stretch).
- Everything touches `index.html` or `assets/styles.css`, so issues are
  sequential — no parallel lanes.
- Keep each issue small enough to review as a diff in under a minute.

## 14. Operator checklist (not factory issues)

- Replace the placeholder name, bio, entry titles, project names, and contact
  links with real content.
- Choose a domain and a static host (GitHub Pages, Cloudflare Pages, Netlify).
  Add the canonical URL once the domain is fixed.
- Decide later whether writing gets its own pages; that is a separate PRD.
