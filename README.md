# Davis Landworks website

Source for https://davislandworksva.com, the site for Davis Landworks LLC (Harrison Davis),
stump grinding, grading, light excavation, hauling and cleanup in Hampton Roads.

## How it is built
- Plain static site served by GitHub Pages from `main`. No framework. Five pages: the home page, `/stump-grinding/`,
  `/yard-grading/`, `/service-area/` and `/privacy/` (noindex, out of the sitemap), plus the branded `404.html` and a
  generated `sitemap.xml`.
- Never edit `index.html`, `<slug>/index.html`, `404.html` or `sitemap.xml` by hand. They are built from these sources:
  - `_build/index.template.html` is the home page; `_build/<slug>.template.html` becomes `<slug>/index.html`. The
    page list is `PAGES` at the top of `_build/build_index.py`, which also holds the header nav. A page entry says
    whether the page is indexed and carries its slot values (see below).
  - `_build/partials/*.html`: the shared markup. A page says `%%HEADER%%` and the build drops in
    `_build/partials/header.html`; the same for `icons`, `head_assets`, `proof` (the rating strip), `review_quotes`,
    `area_band` (the gold service-area band), `estimate` (the form), `stump_guide` (the how-to-measure figure and
    text), `stump_aside` (the guide wrapped for the form's intro column), `footer` (footer and the phone action bar)
    and `scripts` (the one script tag). A partial may hold another partial. Edit a partial once and every page gets it.
  - Slots: a partial may say `%%NAME%%` for something that differs per page, and each page's `PAGES` entry supplies
    the value. Today: `ESTIMATE_ASIDE` (the home page puts the stump guide under the form's intro; the others leave
    it empty) and `SIZE_HELP` (where the form's "How to measure" link points).
  - `_build/404.template.html`: the not-found page.
  - `_build/site.json`: the business facts (name, owner, phone, email, rating, review count and its as-of month,
    Maps link) plus two switches, `lead_api_base` and `turnstile_site_key`. The templates and partials use them as
    `{{key}}` tokens, and the build refuses to run if a guarded fact is typed into a template directly or a stale
    value is left in the output. `<!--if:key-->...<!--end:key-->` keeps a block only when that fact is non-empty,
    `<!--ifnot:key-->` the reverse; the form note and the privacy page switch on `lead_api_base` this way.
  - `styles.css`: edited directly, but no page loads it. The build inlines it into every page as a `<style>` block,
    so a CSS edit does nothing on the live site until you rebuild.
  - `assets/site.js`: the estimate form, the phone action bar and the photo viewer. Every page loads it once, with a
    hash of its content in the query string so a change is never served from an old cache. It holds no business
    fact: the phone, email, API base and Turnstile key reach it through data attributes on the form, which the
    build fills from `site.json`. The build refuses a phone number, email or dash inside it.
- Every asset path is root-absolute (`/assets/...`), because the pages live in subfolders. The build fails on a
  relative `assets/` path.
- After any edit to a template, partial, `site.json`, `styles.css` or `site.js`, run `python3 _build/build_index.py`.
  It writes the pages, `404.html` and `sitemap.xml`, inlines the icon sprite (`_build/icons.svg`) and Harrison's
  vector logo (`assets/davis-landworks-logo.svg`) as SVG symbols, and writes the hero `<picture>` from the files
  in `assets/hero/` wherever a page says `%%HERO_PICTURE%%`.
- The build checks each page: one `h1`, a title of 65 characters or fewer and a description of 160 or fewer, both
  unique across the site, canonical and `og:url` matching the page's path (a noindex page carries the robots tag
  and no canonical instead), every internal link pointing at a built page or an existing file, every in-page anchor
  having a target, and JSON-LD whose business node, Service node and breadcrumbs agree with `site.json` and the
  page's URL. A page without the estimate form has its footer `#estimate` links sent to the home page's form.
- `sitemap.xml` lists every indexed page. Its `lastmod` is the date of the newest commit touching that page's
  template or any shared input (partials, `site.json`, `styles.css`, `site.js`, the build script), or today while
  any of them has uncommitted changes. So it is deterministic once everything is committed.
- Before committing, run `python3 _build/build_index.py --check`. It exits with an error if any built file is out
  of date with its sources. To run it on every commit, install the hook once per clone:
  `cp _build/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`.
- Fonts (Saira and Saira Semi Condensed) are self-hosted in `assets/fonts/`, under the license in
  `_build/LICENSE-saira.txt`.
- Folders and files starting with an underscore are not published. `_config.yml` also keeps
  this README off the live site.

## The estimate form
- With `lead_api_base` empty (the state in this repo until the lead Worker exists), the form posts nothing
  anywhere. It opens a prefilled text message to Harrison. If no text app opens, as on most computers, it shows his
  number and a prefilled email link. The privacy page then says plainly that the site keeps nothing.
- With `lead_api_base` set to the Worker's origin, the form speaks this contract:
  - Phones (coarse pointer or a phone user agent): the text message stays primary. Just before the `sms:` link
    opens, `navigator.sendBeacon` posts the fields to `{base}/api/lead/beacon` as a URL-encoded `text/plain` body.
    The form also offers "Can't text right now? Send it from here instead", which switches to the send path.
  - Computers, and phones that switch: "Send to Harrison" posts JSON to `{base}/api/lead` with `name`, `phone`
    (10 digits), `address`, `service` (`stump`, `grading`, `excavation`, `hauling` or `other`), `size`, `day`,
    `details`, `referrer_host`, `utm_source`, `utm_medium`, `website` (a honeypot that must stay empty) and
    `turnstile_token`; expects `{ok, ref, uploadToken}`; PUTs up to six photos to `{base}/api/lead/{ref}/photo/{n}`
    as raw JPEG with `Authorization: Bearer {uploadToken}`; POSTs `{base}/api/lead/{ref}/complete` with the same
    bearer; then shows the reference number. Photos are redrawn on a canvas at about 1600 px on the long side
    before upload, which drops EXIF and location data. Any failure shows the phone number, a prefilled email and
    Try again.
  - Turnstile loads only on the send path and only when `turnstile_site_key` is set. It runs at submit; a missing
    token is sent as an empty string and the Worker decides.
- `referrer_host` is the hostname of the page that sent the visitor here (empty for this site's own pages);
  `utm_source` and `utm_medium` come from the landing URL. Both are kept in `sessionStorage` for the visit.
- The `<noscript>` text keeps the phone number and a `tel:` link in front of visitors without JavaScript.

## Assets
- `assets/davis-landworks-logo.svg` and `-reversed.svg`: vector rebuild of Harrison's logo.
- `assets/hero/`: the Rayco RG45X photo in 4:5 (desktop) and 3:2 (phones), JPEG and WebP.
- `assets/work/`: grading photos at 800, 1200 and 1600 wide, plus `-full` portrait versions for
  the full-screen viewer.
- All photos are tone and crop edits only, with metadata stripped.
- `_build/icons.svg`: four Lucide icons (arrow-right, check, message-square-text, phone), used under
  the licenses in `_build/LICENSE-lucide.txt`. The stump diagram in `_build/partials/stump_guide.html` is drawn
  by hand for this site.

## Local preview
```
python3 -m http.server 8765
```
Then open http://localhost:8765/, /stump-grinding/, /yard-grading/, /service-area/ and /privacy/.
