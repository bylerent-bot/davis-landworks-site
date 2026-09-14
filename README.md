# Davis Landworks — website

Static one-page marketing/booking site for **Davis Landworks LLC** (Harrison Davis) —
stump grinding, grading, light excavation, hauling and cleanup in Virginia Beach / Hampton Roads.
A friend-favor build by Patrick Clark.

## Stack
Plain static site — `index.html` + `styles.css` + `assets/`. No build step, no framework.
Lucide icons are inlined as an SVG sprite; the booking form opens the visitor's Messages app
pre-addressed to Harrison (SMS deep-link, no backend). Migrated 2026-09-14 off ChatGPT's
"Sites" builder (Vite/vinext → Cloudflare), preserving the design verbatim.

## Deploy
GitHub Pages from `main` root, under the `bylerent-bot` org — same pattern as the Byler Cove
sites. Custom domain via a `CNAME` file once the domain is registered.

## Local preview
```
cd davis-landworks-site && python3 -m http.server 8765
# open http://localhost:8765/index.html
```
