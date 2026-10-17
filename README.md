# Davis Landworks website

Source for https://davislandworksva.com, the site for Davis Landworks LLC (Harrison Davis),
stump grinding, grading, light excavation, hauling and cleanup in Hampton Roads.

## How it is built
- Plain static site served by GitHub Pages from `main`. No framework. Four pages: the home page, `/stump-grinding/`,
  `/yard-grading/` and `/service-area/`, plus the branded `404.html` and a generated `sitemap.xml`.
- Never edit `index.html`, `<slug>/index.html`, `404.html` or `sitemap.xml` by hand. They are built from these sources:
  - `_build/index.template.html` is the home page; `_build/<slug>.template.html` becomes `<slug>/index.html`. The
    page list is `PAGES` at the top of `_build/build_index.py`, which also holds the header nav.
  - `_build/partials/*.html`: the shared markup. A page says `%%HEADER%%` and the build drops in
    `_build/partials/header.html`; the same for `icons`, `head_assets`, `proof` (the rating strip), `review_quotes`,
    `area_band` (the gold service-area band), `estimate` (the form), `footer` (footer and the phone action bar) and
    `scripts` (the form, action bar and photo viewer scripts). Edit a partial once and every page gets it.
  - `_build/404.template.html`: the not-found page.
  - `_build/site.json`: the business facts (name, owner, phone, email, rating, review count and its as-of month,
    Maps link). The templates and partials use them as `{{key}}` tokens, and the build refuses to run if one of
    them is typed into a template directly or a stale value is left in the output.
  - `styles.css`: edited directly, but no page loads it. The build inlines it into every page as a `<style>` block,
    so a CSS edit does nothing on the live site until you rebuild.
- Every asset path is root-absolute (`/assets/...`), because the pages live in subfolders. The build fails on a
  relative `assets/` path.
- After any edit to a template, partial, `site.json` or `styles.css`, run `python3 _build/build_index.py`. It
  writes the pages, `404.html` and `sitemap.xml`, inlines the icon sprite (`_build/icons.svg`) and Harrison's
  vector logo (`assets/davis-landworks-logo.svg`) as SVG symbols, and writes the hero `<picture>` from the files
  in `assets/hero/` wherever a page says `%%HERO_PICTURE%%`.
- The build checks each page: one `h1`, a title of 65 characters or fewer and a description of 160 or fewer, both
  unique across the site, canonical and `og:url` matching the page's path, every internal link pointing at a built
  page or an existing file, every in-page anchor having a target, and JSON-LD whose business node, Service node and
  breadcrumbs agree with `site.json` and the page's URL.
- `sitemap.xml` lists every page. Its `lastmod` is the date of the newest commit touching that page's template or
  any shared input (partials, `site.json`, `styles.css`, the build script), or today while any of them has
  uncommitted changes. So it is deterministic once everything is committed.
- Before committing, run `python3 _build/build_index.py --check`. It exits with an error if any built file is out
  of date with its sources. To run it on every commit, install the hook once per clone:
  `cp _build/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`.
- Fonts (Saira and Saira Semi Condensed) are self-hosted in `assets/fonts/`, under the license in
  `_build/LICENSE-saira.txt`.
- The estimate form does not submit anywhere. It opens a prefilled text message to Harrison. If no
  text app opens, as on most computers, it shows his number and a prefilled email link.
- Folders and files starting with an underscore are not published. `_config.yml` also keeps
  this README off the live site.

## Assets
- `assets/davis-landworks-logo.svg` and `-reversed.svg`: vector rebuild of Harrison's logo.
- `assets/hero/`: the Rayco RG45X photo in 4:5 (desktop) and 3:2 (phones), JPEG and WebP.
- `assets/work/`: grading photos at 800, 1200 and 1600 wide, plus `-full` portrait versions for
  the full-screen viewer.
- All photos are tone and crop edits only, with metadata stripped.
- `_build/icons.svg`: four Lucide icons (arrow-right, check, message-square-text, phone), used under
  the licenses in `_build/LICENSE-lucide.txt`.

## Local preview
```
python3 -m http.server 8765
```
Then open http://localhost:8765/, /stump-grinding/, /yard-grading/ and /service-area/.
