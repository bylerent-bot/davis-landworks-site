#!/usr/bin/env python3
"""Build every page of davislandworksva.com.

Run from anywhere:  python3 _build/build_index.py
Check only:         python3 _build/build_index.py --check
                    (rebuilds in memory and exits 1 if any output on disk differs, so a template, partial,
                    site.json or styles.css edit that was never rebuilt is caught before a commit)

Sources (never edit the outputs by hand):
  _build/<name>.template.html   one per page; index.template.html is the home page and <slug>.template.html
                                becomes <slug>/index.html (see PAGES below)
  _build/404.template.html      the branded not-found page
  _build/partials/*.html        shared markup, dropped into a page where it says %%NAME%% (icons, head_assets,
                                header, proof, review_quotes, area_band, estimate, footer, scripts); a partial
                                may itself say %%NAME%% for another partial
  _build/site.json              the business facts, used as {{key}} tokens; <!--if:key-->...<!--end:key--> keeps
                                its content only when the fact is non-empty, <!--ifnot:key--> the reverse
  styles.css                    inlined into every page as a <style> block
  assets/site.js                the form, action bar and photo viewer script, loaded by every page with a content
                                hash in the query string so a change is never served stale; facts reach it through
                                data attributes the templates fill from site.json, never by editing the script
  _build/icons.svg and assets/davis-landworks-logo.svg, inlined as SVG symbols

Each page in PAGES may carry slot values (%%NAME%% in a partial, filled per page) and may be marked noindex,
which keeps it out of the sitemap and requires a robots noindex tag instead of a canonical.

Outputs: index.html, <slug>/index.html for each page, 404.html and sitemap.xml.

Guards: a fact typed into a template or partial instead of a token fails the build, as does a stale review
count or as-of month, a stray phone number or email, an em dash, a relative assets/ path (pages live in
subfolders, so every asset path is root-absolute), a missing or duplicate h1, a canonical or og:url that does
not match the page's path, a duplicate title or description, an internal link to a page or file that does not
exist, an in-page anchor with no target, and JSON-LD whose business facts disagree with site.json.
Folders starting with an underscore are not published by GitHub Pages."""
import os, re, glob, sys, json, subprocess, datetime, hashlib

B = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(B)
DESK_CAP = 1600   # widest 4:5 hero candidate offered to desktops; the 2000w files stay on disk, unreferenced
read = lambda *p: open(os.path.join(*p), encoding='utf-8').read()

# template file, output file, URL path, whether search engines may index it (noindex pages stay out of the
# sitemap), and per-page slot values: %%NAME%% in a partial is filled with the page's value, which may itself
# name a partial.
def page(tpl, out, path, index=True, **slots):
    return {'tpl': tpl, 'out': out, 'path': path, 'index': index, 'slots': slots}

# ESTIMATE_ASIDE: what sits under the form's intro column (the home page carries the stump size guide there).
# SIZE_HELP: where the form's "How to measure" link goes (the guide on the page, or the one on the stump page).
PAGES = [
    page('index.template.html', 'index.html', '/', ESTIMATE_ASIDE='%%STUMP_ASIDE%%', SIZE_HELP='#stump-size'),
    page('stump-grinding.template.html', 'stump-grinding/index.html', '/stump-grinding/', ESTIMATE_ASIDE='', SIZE_HELP='#stump-size'),
    page('yard-grading.template.html', 'yard-grading/index.html', '/yard-grading/', ESTIMATE_ASIDE='', SIZE_HELP='/stump-grinding/#stump-size'),
    page('service-area.template.html', 'service-area/index.html', '/service-area/', ESTIMATE_ASIDE='', SIZE_HELP='/stump-grinding/#stump-size'),
]
NAV = [('/stump-grinding/', 'Stump grinding'), ('/yard-grading/', 'Yard grading'), ('/service-area/', 'Service area'), ('/#reviews', 'Reviews')]
TITLE_MAX, DESC_MAX = 65, 160

facts = json.loads(read(B, 'site.json'))
facts = {k: str(v) for k, v in facts.items() if not k.startswith('_')}
SITE_URL = facts['site_url'].rstrip('/')
# Facts that must only ever reach the page through a token.
GUARDED = ('phone_display', 'phone_tel', 'phone_schema', 'email', 'maps_url')
PHONE_DIGITS = re.sub(r'\D', '', facts['phone_tel'])[-10:]
PHONE_LOOSE = re.compile(r'\D{0,3}'.join([re.escape(PHONE_DIGITS[:3]), re.escape(PHONE_DIGITS[3:6]), re.escape(PHONE_DIGITS[6:])]))


def no_hardcoded(tpl, name):
    for k in GUARDED:
        assert facts[k] not in tpl, f'{name}: {k} is hardcoded; use {{{{{k}}}}} instead'
    assert not PHONE_LOOSE.search(tpl), f'{name}: the phone number is hardcoded in some form; use a phone token'


COND = re.compile(r'<!--(if|ifnot):([a-z_]+)-->(.*?)<!--end:\2-->', re.S)


def fill(tpl, name):
    no_hardcoded(tpl, name)
    def cond(m):
        kind, key, body = m.groups()
        assert key in facts, f'{name}: unknown fact {key} in <!--{kind}:{key}-->'
        return body if bool(facts[key]) == (kind == 'if') else ''
    tpl = COND.sub(cond, tpl)
    assert '<!--if' not in tpl and '<!--end:' not in tpl, f'{name}: unbalanced <!--if--> block'
    def sub(m):
        assert m.group(1) in facts, f'{name}: unknown token {m.group(0)}'
        return facts[m.group(1)]
    out = re.sub(r'\{\{([a-z_]+)\}\}', sub, tpl)
    assert '{{' not in out and '}}}' not in out, f'{name}: malformed token left in output'
    return out


def guard(html, name):
    """Fail on any fact in the output that disagrees with site.json, and on the house style rules."""
    assert '%%' not in html, f'{name}: unfilled %% slot'
    for bad in ('—', '–', '·'):
        assert bad not in html, f'{name}: em dash, en dash or interpunct found'
    for host in ('fonts.googleapis.com', 'fonts.gstatic.com'):
        assert host not in html, f'{name}: {host} is still referenced'
    rel = re.search(r'(?<![\w/.-])assets/', html)
    assert not rel, f'{name}: relative assets/ path at offset {rel.start()}; use /assets/ (pages live in subfolders)'
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


def meta(html, name, attr='name'):
    m = re.search(r'<meta %s="%s" content="([^"]*)"' % (attr, re.escape(name)), html)
    return m.group(1) if m else None


def check_page(html, name, path, all_paths, index=True):
    """Per-page structure checks: head tags match the path, one h1, links resolve, JSON-LD agrees."""
    url = SITE_URL + path
    title = re.search(r'<title>(.*?)</title>', html, re.S)
    assert title, f'{name}: no <title>'
    title = re.sub(r'\s+', ' ', title.group(1)).strip()
    assert len(title) <= TITLE_MAX, f'{name}: title is {len(title)} characters, over {TITLE_MAX}: {title}'
    desc = meta(html, 'description')
    assert desc and len(desc) <= DESC_MAX, f'{name}: description missing or over {DESC_MAX} characters'
    canon = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    noindex = '<meta name="robots" content="noindex"' in html
    if index:
        assert canon and canon.group(1) == url, f'{name}: canonical {canon and canon.group(1)} should be {url}'
        assert not noindex, f'{name}: indexed page carries a noindex tag'
    else:
        assert noindex and not canon, f'{name}: a noindex page needs the robots tag and no canonical'
    assert meta(html, 'og:url', 'property') == url, f'{name}: og:url should be {url}'
    for tag, attr in (('og:title', 'property'), ('og:description', 'property'), ('og:image', 'property'), ('twitter:title', 'name'), ('twitter:description', 'name'), ('twitter:image', 'name')):
        assert meta(html, tag, attr), f'{name}: missing {tag}'
    h1 = re.findall(r'<h1[\s>]', html)
    assert len(h1) == 1, f'{name}: expected one h1, found {len(h1)}'
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    for href in re.findall(r'\s(?:href|src|data-full)="([^"]+)"', html):
        if href.startswith(('http', 'tel:', 'sms:', 'mailto:')):
            continue
        if href.startswith('#'):
            assert href == '#' or href[1:] in ids, f'{name}: anchor {href} has no target on the page'
            continue
        assert href.startswith('/'), f'{name}: link {href} is not root-absolute'
        target, _, frag = href.partition('#')
        target = target.split('?')[0]
        if target.endswith('/'):
            assert target in all_paths, f'{name}: link {href} points at a page that is not built'
            if frag:
                assert (target, frag) in ANCHORS, f'{name}: link {href} points at an anchor that does not exist'
        else:
            assert os.path.isfile(os.path.join(SITE, target.lstrip('/'))), f'{name}: link {href} points at a file that does not exist'
    for src in re.findall(r'srcset="([^"]+)"', html):
        for part in src.split(','):
            p = part.strip().split()[0]
            assert p.startswith('/') and os.path.isfile(os.path.join(SITE, p.lstrip('/'))), f'{name}: srcset entry {p} does not exist'
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert blocks, f'{name}: no JSON-LD block'
    for raw in blocks:
        data = json.loads(raw)
        nodes = data.get('@graph', [data])
        for n in nodes:
            if n.get('@id', '').endswith('#business'):
                if 'telephone' in n: assert n['telephone'] == facts['phone_schema'], f'{name}: JSON-LD telephone disagrees with site.json'
                if 'email' in n: assert n['email'] == facts['email'], f'{name}: JSON-LD email disagrees with site.json'
                if 'url' in n: assert n['url'] == facts['site_url'], f'{name}: JSON-LD business url disagrees with site.json'
            if n.get('@type') == 'BreadcrumbList':
                items = n['itemListElement']
                assert items[-1]['item'] == url, f'{name}: breadcrumb ends at {items[-1]["item"]}, not {url}'
                assert items[0]['item'] == facts['site_url'], f'{name}: breadcrumb does not start at the home page'
            if n.get('@type') == 'Service':
                assert n.get('provider', {}).get('@id') == SITE_URL + '/#business', f'{name}: Service node is not linked to the business'
                assert n.get('url') == url, f'{name}: Service node url should be {url}'
            if n.get('@type') == 'WebPage':
                assert n.get('url') == url, f'{name}: WebPage url should be {url}'
    return title, desc


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

# Hero picture and preloads (root-absolute, so any page can carry the hero).
H = os.path.join(SITE, 'assets', 'hero')
def have(pat, cap=None):
    out = []
    for p in glob.glob(os.path.join(H, pat)):
        m = re.search(r'-(\d+)\.(jpg|webp)$', p)
        if m and (cap is None or int(m.group(1)) <= cap):
            out.append((int(m.group(1)), '/' + os.path.relpath(p, SITE)))
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
pic.append(f'<img src="{mid[0][1]}" srcset="{ss(p32j)}" sizes="100vw" width="1200" height="800" fetchpriority="high" decoding="async" data-full="/{os.path.relpath(full[0], SITE)}" alt="Yellow Rayco RG45X stump grinder parked on wood chips in a fenced backyard">')
pic.append('</picture>')
pre = []
if p32w: pre.append(f'<link rel="preload" as="image" type="image/webp" imagesrcset="{ss(p32w)}" imagesizes="100vw" media="(max-width: 959px)" fetchpriority="high" />')
if p45w: pre.append(f'<link rel="preload" as="image" type="image/webp" imagesrcset="{ss(p45w)}" imagesizes="{desk}" media="(min-width: 960px)" fetchpriority="high" />')
HERO_PICTURE = '\n        '.join(pic)
PRELOAD = '\n'.join(pre)

css = read(SITE, 'styles.css').strip()
assert '</style' not in css.lower()
STYLES = '<style>\n' + css + '\n</style>'

# The one script file. Facts never live in it (it reads them from the form's data attributes), and its content
# hash goes in the query string of every <script src> so a change is never served from an old cache.
site_js = read(SITE, 'assets', 'site.js')
no_hardcoded(site_js, 'assets/site.js')
for bad in ('\u2014', '\u2013'):
    assert bad not in site_js, 'assets/site.js: em or en dash found'
JS_VERSION = hashlib.sha1(site_js.encode('utf-8')).hexdigest()[:10]

# Partials: _build/partials/<name>.html fills %%NAME%%.
partials = {}
for p in sorted(glob.glob(os.path.join(B, 'partials', '*.html'))):
    key = os.path.basename(p)[:-5].upper()
    partials[key] = read(p).rstrip('\n')
    no_hardcoded(partials[key], 'partials/' + os.path.basename(p))
assert partials, 'no partials found'


def nav_for(path):
    out = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == path else ''
        out.append(f'    <a href="{href}"{cur}>{label}</a>')
    return '\n'.join(out)


def assemble(tpl, pg):
    assert f'viewBox="0 0 {w} {h}"' in partials['HEADER'], 'logo <svg> tags must use viewBox="0 0 w h" of the symbol'
    name, path = pg['tpl'], pg['path']
    html = tpl
    for _ in range(6):   # partials and slots may nest (the form holds a slot that holds a partial that holds another)
        before = html
        for key, body in partials.items():
            html = html.replace(f'%%{key}%%', body)
        for key, body in pg['slots'].items():
            html = html.replace(f'%%{key}%%', body)
        if html == before:
            break
    html = (html.replace('%%NAV%%', nav_for(path))
                .replace('%%SPRITE%%', wrap([icons, logo_sym]))
                .replace('%%PRELOAD%%', PRELOAD if '%%HERO_PICTURE%%' in html else '')
                .replace('%%HERO_PICTURE%%', HERO_PICTURE)
                .replace('%%STYLES%%', STYLES)
                .replace('%%JS_VERSION%%', JS_VERSION))
    html = fill(html, name)
    if ' id="estimate"' not in html:   # a page without the form sends the footer's estimate links to the home page
        html = html.replace('href="#estimate"', 'href="/#estimate"')
    return guard(html, name)


# Git-derived lastmod for the sitemap: the newest commit touching the page's template or any shared input,
# or today while any of them has uncommitted changes. Deterministic once everything is committed.
def git(*args):
    try:
        r = subprocess.run(['git', '-C', SITE] + list(args), capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None

SHARED = [os.path.relpath(p, SITE) for p in glob.glob(os.path.join(B, 'partials', '*.html'))] + [
    '_build/site.json', '_build/build_index.py', '_build/icons.svg', 'styles.css', 'assets/site.js', 'assets/davis-landworks-logo.svg']
TODAY = datetime.date.today().isoformat()

def lastmod(tpl_name):
    files = ['_build/' + tpl_name] + SHARED
    status = git('status', '--porcelain', '--', *files)
    if status is None or status:
        return TODAY
    return git('log', '-1', '--format=%cs', '--', *files) or TODAY


outputs, seen_titles, seen_descs, ANCHORS = {}, {}, {}, set()
all_paths = {pg['path'] for pg in PAGES}
built = []
for pg in PAGES:
    html = assemble(read(B, pg['tpl']), pg)
    for i in re.findall(r'\sid="([^"]+)"', html):
        ANCHORS.add((pg['path'], i))
    built.append((pg, html))
for pg, html in built:
    tpl_name = pg['tpl']
    title, desc = check_page(html, tpl_name, pg['path'], all_paths, pg['index'])
    assert title not in seen_titles, f'{tpl_name}: title duplicates {seen_titles[title]}: {title}'
    assert desc not in seen_descs, f'{tpl_name}: description duplicates {seen_descs[desc]}'
    seen_titles[title], seen_descs[desc] = tpl_name, tpl_name
    outputs[pg['out']] = html
home = outputs['index.html']
biz = [n for n in json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', home, re.S).group(1))['@graph'] if n.get('@id', '').endswith('#business')]
assert len(biz) == 1 and biz[0]['telephone'] == facts['phone_schema'] and biz[0]['email'] == facts['email'], 'home JSON-LD business node is missing or disagrees with site.json'

nf = (fill(read(B, '404.template.html'), '404.template.html')
      .replace('%%LOGO_SPRITE%%', wrap([logo_sym]))
      .replace('%%LOGO_W%%', w).replace('%%LOGO_H%%', h))
nf = guard(nf, '404.html')
for href in re.findall(r'\shref="(/[^"#]*)"', nf):
    assert href in all_paths or os.path.isfile(os.path.join(SITE, href.lstrip('/'))), f'404.html: link {href} does not resolve'
outputs['404.html'] = nf

sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for pg in PAGES:
    if pg['index']:
        sm.append(f'  <url><loc>{SITE_URL + pg["path"]}</loc><lastmod>{lastmod(pg["tpl"])}</lastmod></url>')
sm.append('</urlset>')
outputs['sitemap.xml'] = '\n'.join(sm) + '\n'

if '--check' in sys.argv[1:]:
    stale = []
    for name, html in outputs.items():
        p = os.path.join(SITE, name)
        if not os.path.exists(p) or open(p, encoding='utf-8').read() != html:
            stale.append(name)
    if stale:
        sys.exit('out of date: ' + ', '.join(stale) + '. Run python3 _build/build_index.py and commit the result.')
    print('check passed:', ', '.join(outputs), 'match the sources')
    sys.exit(0)

for name, html in outputs.items():
    p = os.path.join(SITE, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(html)
    print('wrote', name, len(html.encode('utf-8')), 'bytes')
