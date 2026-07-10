# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A single-page personal portfolio ("SD.Folio" / Shubham A. D.) built as **plain static files with no build step, no package manager, and no tests**. It renders a canvas-based animated globe (Earth wireframe + ISS + satellites + starfield) that morphs on scroll, with all site content injected at runtime from a JSON file. A separate in-browser GUI edits that JSON.

## Running / developing

- No build, lint, or test tooling exists. "Running" = opening the site in a browser.
- Preferred: serve the folder so `fetch('portfolio-data.json')` works reliably across browsers:
  `python3 -m http.server 8000` then open `http://localhost:8000/index.html`.
- Opening `index.html` directly via `file://` mostly works (the code is written for `file://` compatibility), but some browsers block `fetch` of the JSON on `file://`; in that case the page falls back to hardcoded defaults baked into `index.html`.
- Third-party libraries (React 18, ReactDOM, Babel standalone) are pulled from the unpkg CDN at runtime and are used **only** for the on-screen "tweaks" panel — the rest of the page is vanilla JS.

## Architecture

**Content flow (data-driven UI):**
- `portfolio-data.json` is the single source of content (identity, nav, hero, stats, projects, blog, contact, footer) plus a `tweaks` block of globe/UX settings.
- `index.html` is the live production page. On load, an inline vanilla-JS IIFE `fetch`es `portfolio-data.json?<cachebust>` and imperatively populates the DOM by element id (`setText`/`setHTML`, `populate(d)`), builds the projects bento grid and blog cards, wires cursor/tilt/scroll-reveal effects, and calls into the globe engine. If the JSON is missing it logs and uses hardcoded defaults.

**Globe engine (`globe-engine.js`):**
- Standalone canvas-2D animation. Exposes two globals: `window.initISSIntro()` (fullscreen intro globe + satellites + starfield that morphs with scroll) and `window.initHeroGlobe()` (small hero globe).
- Contains hardcoded continent polygons (`CONTINENTS`, lat/lon) and a `lonLatToXYZ` sphere projection — geometry is generated in code, no external map assets.

**Tweaks panel ↔ engine bridge (important):**
- The live-tweaks React app is inlined as `<script type="text/babel">` inside `index.html` (around the `#tweaks-root` mount). It does not import a separate file.
- It communicates with the globe engine through **`window.__*` global variables**, not props or events: e.g. `window.__globeSpeed`, `window.__satCount`, `window.__starCount`, `window.__nebula`, `window.__frameSkip` (derived from a frame-rate cap), `window.__pixelCap`, `window.__cardTilt`, `window.__particleTrail`. The engine reads these each frame. When editing either side, keep these global names in sync.
- Defaults for these live in both `index.html` (`TWEAK_DEFAULTS`) and the `tweaks` block of `portfolio-data.json`.

**GUI content editor:**
- `portfolio-updater.html` (and the near-duplicate `Editable/portfolio-editor.html`) is a standalone, backend-less editor. It loads current `portfolio-data.json`, lets you edit all sections + tweaks, and exports via `downloadJSON()` / clipboard copy. Workflow: edit in the updater → download `portfolio-data.json` → place it next to `index.html`.

## Live files vs. archives (don't edit the wrong copy)

- **Live:** `index.html`, `globe-engine.js`, `portfolio-data.json`, `portfolio-updater.html`.
- **Archived / experimental (do not edit unless intentionally versioning):** `index03.html`, `indexv02.html`, `indexv04.html`, `globe-enginev02.js`, `globe-enginev03.js`, `Logo Options.html`, `Unused/`, `Editable/`, and the brand snapshots under `brand/brandv01|v02|v03/`. Live brand assets are the top-level `logo-dark.png`, `logo-light.png`, `favicon.png`.

## Git behavior (watch out)

- An external file watcher auto-commits and pushes on save; history is full of `auto-push: <file> [timestamp]` commits and `.gitignore` is marked "Auto-added by watcher." Expect your saved changes to be committed/pushed automatically — do not assume the working tree stays dirty.

## Verification

- After editing content/markup: run `python3 -m http.server 8000` and load `http://localhost:8000/index.html`; confirm the browser console logs `[portfolio] Loaded portfolio-data.json ✓` and the intended section renders.
- After editing globe/tweaks behavior: open the page, use the on-screen tweaks panel, and confirm the globe reacts (speed, satellite/star counts, nebula toggle) — i.e. the `window.__*` bridge still works.
