# Davis Landworks website

Source for https://davislandworksva.com, the site for Davis Landworks LLC (Harrison Davis),
stump grinding, grading, light excavation, hauling and cleanup in Hampton Roads.

## How it is built
- Plain static site served by GitHub Pages from `main`. No framework.
- Edit `_build/index.template.html`, then run `python3 _build/build_index.py` to regenerate
  `index.html`. The build inlines the icon sprite (`_build/icons.svg`) and Harrison's vector logo
  (`assets/davis-landworks-logo.svg`) as SVG symbols and writes the hero `<picture>` from the
  files in `assets/hero/`.
- `styles.css` is edited directly.
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
