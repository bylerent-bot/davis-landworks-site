#!/usr/bin/env python3
"""Build index.html for davislandworksva.com.

Run from anywhere:  python3 _build/build_index.py
Edit _build/index.template.html (never index.html directly). This script inlines the
icon sprite (_build/icons.svg) and Harrison's vector logo (assets/davis-landworks-logo.svg)
as SVG symbols, and builds the hero <picture> from the files present in assets/hero/.
Folders starting with an underscore are not published by GitHub Pages."""
import os, re, glob, sys
B = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(B)
tpl = open(os.path.join(B, 'index.template.html')).read()

syms = [open(os.path.join(B, 'icons.svg')).read().strip()]
logo = open(os.path.join(SITE, 'assets', 'davis-landworks-logo.svg')).read()
paths = re.findall(r'<path fill="(#[0-9A-Fa-f]{6})" fill-rule="evenodd" d="([^"]+)"/>', logo)
assert len(paths) == 2, 'expected two colour paths in the logo'
ink = [d for f, d in paths if f.lower() == '#111111'][0]
gold = [d for f, d in paths if f.lower() == '#aa7b3c'][0]
vb = re.search(r'viewBox="([^"]+)"', logo).group(1)
syms.append(f'<symbol id="logo" viewBox="{vb}"><path style="fill:var(--logo-ink,#111111)" fill-rule="evenodd" d="{ink}"/><path style="fill:var(--logo-gold,#AA7B3C)" fill-rule="evenodd" d="{gold}"/></symbol>')
sprite = '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false" style="position:absolute;width:0;height:0;overflow:hidden">\n' + '\n'.join(syms) + '\n</svg>'
w, h = vb.split()[2:]
assert f'viewBox="0 0 {w} {h}"' in tpl, 'logo <svg> tags in the template must use viewBox="0 0 w h" of the symbol'

H = os.path.join(SITE, 'assets', 'hero')
def have(pat):
    out = []
    for p in glob.glob(os.path.join(H, pat)):
        m = re.search(r'-(\d+)\.(jpg|webp)$', p)
        if m: out.append((int(m.group(1)), os.path.relpath(p, SITE)))
    return sorted(out)
p45j, p45w = have('rayco-rg45x-4x5-*.jpg'), have('rayco-rg45x-4x5-*.webp')
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
html = tpl.replace('%%SPRITE%%', sprite).replace('%%HERO_PICTURE%%', '\n        '.join(pic)).replace('%%PRELOAD%%', '\n'.join(pre))
assert '%%' not in html
for bad in ('—', '–', '·'):
    assert bad not in html, 'em dash, en dash or interpunct found'
open(os.path.join(SITE, 'index.html'), 'w').write(html)
print('wrote index.html', len(html), 'bytes')
