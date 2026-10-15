# Davis Landworks website

Source for https://davislandworksva.com, the site for Davis Landworks LLC (Harrison Davis),
stump grinding, grading, light excavation, hauling and cleanup in Hampton Roads.

## How it is built
- Plain static site served by GitHub Pages from `main`. No framework.
- Never edit `index.html` or `404.html` by hand. They are built from these sources:
  - `_build/index.template.html` and `_build/404.template.html`: the page markup.
  - `_build/site.json`: the business facts (name, owner, phone, email, rating, review count and its
    as-of month, Maps link). The templates use them as `{{key}}` tokens, and the build refuses to run
    if one of them is typed into a template directly or a stale value is left in the output.
  - `styles.css`: edited directly, but no page loads it. The build inlines it into `index.html` as a
    `<style>` block, so a CSS edit does nothing on the live site until you rebuild.
- After any edit to a template, `site.json` or `styles.css`, run `python3 _build/build_index.py`. It
  writes `index.html` and `404.html`, inlines the icon sprite (`_build/icons.svg`) and Harrison's
  vector logo (`assets/davis-landworks-logo.svg`) as SVG symbols, and writes the hero `<picture>`
  from the files in `assets/hero/`.
- Before committing, run `python3 _build/build_index.py --check`. It exits with an error if
  `index.html` or `404.html` is out of date with its sources. To run it on every commit, install the
  hook once per clone: `cp _build/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`.
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
