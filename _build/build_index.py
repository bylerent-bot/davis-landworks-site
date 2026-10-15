#!/usr/bin/env python3
"""Build index.html and 404.html for davislandworksva.com.

Run from anywhere:  python3 _build/build_index.py
Check only:         python3 _build/build_index.py --check
                    (rebuilds in memory and exits 1 if index.html or 404.html on disk differ, so a template,
                    site.json or styles.css edit that was never rebuilt is caught before a commit)

Edit _build/index.template.html, _build/404.template.html, _build/site.json and styles.css (never index.html
or 404.html directly). This script:
  - substitutes the facts in _build/site.json into the templates as {{key}} tokens, and refuses to build if a
    fact is hardcoded in a template or a stale review count, month, phone or email is left in the output;
  - inlines styles.css as a <style> block;
  - inlines the icon sprite (_build/icons.svg) and Harrison's vector logo (assets/davis-landworks-logo.svg)
    as SVG symbols;
  - builds the hero <picture> and its preloads from the files present in assets/hero/.
Folders starting with an underscore are not published by GitHub Pages."""
import os, re, glob, sys, json

B = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(B)
DESK_CAP = 1600   # widest 4:5 hero candidate offered to desktops; the 2000w files stay on disk, unreferenced
read = lambda *p: open(os.path.join(*p), encoding='utf-8').read()

facts = json.loads(read(B, 'site.json'))
facts = {k: str(v) for k, v in facts.items() if not k.startswith('_')}
# Facts that must only ever reach the page through a token.
GUARDED = ('phone_display', 'phone_tel', 'phone_schema', 'email', 'maps_url')
PHONE_DIGITS = re.sub(r'\D', '', facts['phone_tel'])[-10:]
PHONE_LOOSE = re.compile(r'\D{0,3}'.join([re.escape(PHONE_DIGITS[:3]), re.escape(PHONE_DIGITS[3:6]), re.escape(PHONE_DIGITS[6:])]))


def fill(tpl, name):
    for k in GUARDED:
        assert facts[k] not in tpl, f'{name}: {k} is hardcoded; use {{{{{k}}}}} instead'
    assert not PHONE_LOOSE.search(tpl), f'{name}: the phone number is hardcoded in some form; use a phone token'
    def sub(m):
        assert m.group(1) in facts, f'{name}: unknown token {m.group(0)}'
        return facts[m.group(1)]
    out = re.sub(r'\{\{([a-z_]+)\}\}', sub, tpl)
    assert '{{' not in out and '}}}' not in out, f'{name}: malformed token left in output'
    return out


def guard(html, name):
    """Fail on any fact in the output that disagrees with site.json."""
    assert '%%' not in html, f'{name}: unfilled %% slot'
    for bad in ('—', '–', '·'):
        assert bad not in html, f'{name}: em dash, en dash or interpunct found'
    for host in ('fonts.googleapis.com', 'fonts.gstatic.com'):
        assert host not in html, f'{name}: {host} is still referenced'
    counts = re.findall(r'(\d+)\s+Google reviews', html)
    assert all(c == facts['review_count'] for c in counts), f'{name}: review count {counts} does not match site.json {facts["review_count"]}'
    months = re.findall(r'from Google,?\s+(?:as of\s+)?([A-Z][a-z]+ \d{4})', html)
    assert all(m == facts['reviews_as_of'] for m in months), f'{name}: as-of month {months} does not match site.json'
    for m in re.findall(r'\(?\b\d{3}\)?[-. ]\d{3}[-. ]\d{4}\b', html):
        d = re.sub(r'\D', '', m)
        assert d == PHONE_DIGITS or d[3:6] == '555', f'{name}: stray phone number {m}'
    for m in re.findall(r'\+1-?\d{3}-?\d{3}-?\d{4}', html):
        assert m in (facts['phone_tel'], facts['phone_schema']), f'{name}: stray phone number {m}'
    for m in re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', html):
        assert m == facts['email'], f'{name}: stray email address {m}'
    return html


# Sprite: icons plus the logo as a symbol.
icons = read(B, 'icons.svg').strip()
logo = read(SITE, 'assets', 'davis-landworks-logo.svg')
paths = re.findall(r'<path fill="(#[0-9A-Fa-f]{6})" fill-rule="evenodd" d="([^"]+)"/>', logo)
assert len(paths) == 2, 'expected two colour paths in the logo'
ink = [d for f, d in paths if f.lower() == '#111111'][0]
gold = [d for f, d in paths if f.lower() == '#aa7b3c'][0]
vb = re.search(r'viewBox="([^"]+)"', logo).group(1)
logo_sym = f'<symbol id="logo" viewBox="{vb}"><path style="fill:var(--logo-ink,#111111)" fill-rule="evenodd" d="{ink}"/><path style="fill:var(--logo-gold,#AA7B3C)" fill-rule="evenodd" d="{gold}"/></symbol>'
wrap = lambda syms: '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">\n' + '\n'.join(syms) + '\n</svg>'
w, h = vb.split()[2:]

# Hero picture and preloads.
H = os.path.join(SITE, 'assets', 'hero')
def have(pat, cap=None):
    out = []
    for p in glob.glob(os.path.join(H, pat)):
        m = re.search(r'-(\d+)\.(jpg|webp)$', p)
        if m and (cap is None or int(m.group(1)) <= cap):
            out.append((int(m.group(1)), os.path.relpath(p, SITE)))
    return sorted(out)
p45j, p45w = have('rayco-rg45x-4x5-*.jpg', DESK_CAP), have('rayco-rg45x-4x5-*.webp', DESK_CAP)
p32j, p32w = have('rayco-rg45x-3x2-*.jpg'), have('rayco-rg45x-3x2-*.webp')
full = glob.glob(os.path.join(H, 'rayco-rg45x-full-*.jpg'))
if not (p45j and p32j and full): sys.exit('hero assets missing')
ss = lambda L: ', '.join(f'{p} {wd}w' for wd, p in L)
mid = [x for x in p32j if x[0] == 1200] or p32j[-1:]
desk = '(max-width: 1199px) 50vw, 55vw'
pic = ['<picture>']
if p45w: pic.append(f'<source media="(min-width: 960px)" type="image/webp" srcset="{ss(p45w)}" sizes="{desk}">')
pic.append(f'<source media="(min-width: 960px)" srcset="{ss(p45j)}" sizes="{desk}">')
if p32w: pic.append(f'<source type="image/webp" srcset="{ss(p32w)}" sizes="100vw">')
pic.append(f'<img src="{mid[0][1]}" srcset="{ss(p32j)}" sizes="100vw" width="1200" height="800" fetchpriority="high" decoding="async" data-full="{os.path.relpath(full[0], SITE)}" alt="Yellow Rayco RG45X stump grinder parked on wood chips in a fenced backyard">')
pic.append('</picture>')
pre = []
if p32w: pre.append(f'<link rel="preload" as="image" type="image/webp" imagesrcset="{ss(p32w)}" imagesizes="100vw" media="(max-width: 959px)" fetchpriority="high" />')
if p45w: pre.append(f'<link rel="preload" as="image" type="image/webp" imagesrcset="{ss(p45w)}" imagesizes="{desk}" media="(min-width: 960px)" fetchpriority="high" />')

css = read(SITE, 'styles.css').strip()
assert '</style' not in css.lower()

tpl = read(B, 'index.template.html')
assert f'viewBox="0 0 {w} {h}"' in tpl, 'logo <svg> tags in the template must use viewBox="0 0 w h" of the symbol'
index = (fill(tpl, 'index.template.html')
         .replace('%%SPRITE%%', wrap([icons, logo_sym]))
         .replace('%%HERO_PICTURE%%', '\n        '.join(pic))
         .replace('%%PRELOAD%%', '\n'.join(pre))
         .replace('%%STYLES%%', '<style>\n' + css + '\n</style>'))
index = guard(index, 'index.html')
ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', index, re.S)
assert len(ld) == 1, 'expected one JSON-LD block'
graph = json.loads(ld[0])['@graph']
biz = [n for n in graph if n.get('@id', '').endswith('#business')][0]
assert biz['telephone'] == facts['phone_schema'] and biz['email'] == facts['email'], 'JSON-LD contact facts disagree with site.json'

nf = (fill(read(B, '404.template.html'), '404.template.html')
      .replace('%%LOGO_SPRITE%%', wrap([logo_sym]))
      .replace('%%LOGO_W%%', w).replace('%%LOGO_H%%', h))
nf = guard(nf, '404.html')

outputs = {'index.html': index, '404.html': nf}

if '--check' in sys.argv[1:]:
    stale = []
    for name, html in outputs.items():
        p = os.path.join(SITE, name)
        if not os.path.exists(p) or open(p, encoding='utf-8').read() != html:
            stale.append(name)
    if stale:
        sys.exit('out of date: ' + ', '.join(stale) + '. Run python3 _build/build_index.py and commit the result.')
    print('check passed: index.html and 404.html match the sources')
    sys.exit(0)

for name, html in outputs.items():
    open(os.path.join(SITE, name), 'w', encoding='utf-8').write(html)
    print('wrote', name, len(html.encode('utf-8')), 'bytes')
