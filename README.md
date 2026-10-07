# SD.Folio

**A portfolio built around a globe you can spin — Earth in wireframe, the ISS tracking across it, satellites and a starfield behind, all morphing as you scroll.**

A single page of plain static files. No build step, no package manager, no
bundler. Open it and it runs.

---

## What it is

The personal site of Shubham A. D. — a data engineer and full-stack developer
building ML-driven data products, pipelines, and tools.

The globe is a canvas animation: an Earth wireframe with the International Space
Station on its real orbital path, satellites, and a starfield. It reacts to
scroll, morphing between states as you move through the page rather than sitting
behind the content as decoration.

## Two ideas hold it together

**All content comes from one JSON file.** `portfolio-data.json` holds identity,
nav, hero, stats, projects, blog, contact and footer, plus a `tweaks` block of
globe and UX settings. The HTML is a shell; nothing about *you* is written into
the markup.

**There is a GUI for editing it, in the browser.** The tweaks panel lets you
adjust the globe and the content live and export the JSON back out — so the site
is editable without a text editor, and without a deploy to see the result.

## Running it

There is no build. Serving the folder is preferred so `fetch` of the JSON works
everywhere:

```bash
python3 -m http.server 8000
# http://localhost:8000/index.html
```

Opening `index.html` directly over `file://` mostly works — the code is written
for it — but some browsers block `fetch` on `file://`. In that case the page
falls back to defaults baked into `index.html`, so it still renders rather than
failing blank.

## Editing content

Change `portfolio-data.json` and reload. Nothing needs rebuilding.

For the globe and layout settings, open the tweaks panel in the page, adjust
until it looks right, and export the JSON. React, ReactDOM and Babel standalone
are pulled from unpkg **only** for that panel — the site itself is vanilla JS and
loads none of them.

## Versions

`globe-engine.js`, `globe-enginev02.js`, `globe-enginev03.js` are kept
deliberately. The globe is the whole visual identity of the site and the versions
differ in feel, not just in code — being able to put the previous one back and
compare is the point. **v03 is the live one.**

## Layout

```
index.html             the shell, plus baked-in fallback content
portfolio-data.json    all content and settings — the file to edit
globe-enginev03.js     the live globe: Earth, ISS, satellites, starfield
Editable/              the in-browser JSON editor
brand/  assets/        logos and imagery
Hostinger/             deploy artifacts
```

## Deploying

Copy the folder to any static host. There is nothing to compile and no
server-side anything — which is most of why it still runs unchanged.
