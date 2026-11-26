# nu-portfolio

A quiet, static one-page portfolio. No framework, no build step, no analytics.
Layout and type follow the reference at https://ibiang.xyz/.

## Preview

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## Edit

- `index.html` — name, bio, `Said` entries, `Built` entries, `Find me` links.
  Blocks are marked with `TODO` comments.
- `assets/styles.css` — tokens, type, layout.
- `assets/app.js` — theme toggle and name scramble.

See `.agents/PRDs/PRD.md` for the full product contract.

## Development

Issues are implemented by a dark-factory loop on GitHub. Accepted changes land
on `main` as squash-merges.
