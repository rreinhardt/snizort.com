#!/usr/bin/env python3
"""Check local assets, navigation, structured data, image sizes and sitemap."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images, self.styles = [], [], [], []
        self.h1s = 0
        self.schema = []
        self.in_schema = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'h1': self.h1s += 1
        if tag == 'a' and a.get('href'): self.links.append(a['href'])
        if tag == 'img': self.images.append(a)
        if tag == 'link' and a.get('rel') == 'stylesheet': self.styles.append(a['href'])
        if tag == 'script': self.in_schema = a.get('type') == 'application/ld+json'
    def handle_endtag(self, tag):
        if tag == 'script': self.in_schema = False
    def handle_data(self, data):
        if self.in_schema: self.schema.append(data)

def main():
    page = Page()
    source = (ROOT / 'index.html').read_text()
    page.feed(source)
    assert page.h1s == 1, 'Expected one primary heading'
    assert len(page.ids) == len(set(page.ids)), 'Duplicate IDs'
    assert len(page.images) == 20, 'Expected all original images'
    for href in page.links + page.styles:
        u = urlsplit(href)
        if u.scheme or u.netloc: continue
        if u.path: assert (ROOT / unquote(u.path.lstrip('/'))).is_file(), f'Missing file: {href}'
        if u.fragment: assert u.fragment in page.ids, f'Missing anchor: {href}'
    for i, img in enumerate(page.images):
        assert img.get('alt'), 'Missing image description'
        assert int(img['width']) > 0 and int(img['height']) > 0
        assert (ROOT / img['data-original']).is_file(), 'Missing original'
        assert (ROOT / img['src']).is_file(), 'Missing display image'
        assert img['loading'] == ('eager' if i == 0 else 'lazy')
        assert 'sizes' in img and 'srcset' in img
        for entry in img['srcset'].split(','):
            name, width = entry.strip().split()
            assert (ROOT / name).is_file() and re.fullmatch(r'\d+w', width)
    assert page.images[0].get('fetchpriority') == 'high'
    schema = json.loads(''.join(page.schema))
    assert schema['@context'] == 'https://schema.org'
    assert any('WebPage' == x['@type'] for x in schema['@graph'])
    assert any(x['@id'] == 'https://snizort.net/#place' for x in schema['@graph'])
    assert 'name="keywords"' not in source
    assert 'href="https://snizort.net/"' in source
    for css in page.styles:
        for asset in re.findall(r'url\("([^"]+)"\)', (ROOT / css).read_text()):
            assert (ROOT / css).parent.joinpath(asset).is_file(), 'Missing font'
    for asset in (ROOT / 'assets').iterdir():
        m = re.search(r'\.([a-f0-9]{12})\.[^.]+$', asset.name)
        if m: assert hashlib.sha256(asset.read_bytes()).hexdigest().startswith(m[1]), f'Fingerprint mismatch: {asset}'
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap = ET.parse(ROOT / 'sitemap.xml')
    assert sitemap.find('.//s:loc', ns).text == 'https://snizort.net/'
    assert 'Sitemap: https://snizort.net/sitemap.xml' in (ROOT / 'robots.txt').read_text()
    manifest = json.loads((ROOT / 'scripts/image-manifest.json').read_text())
    original = sum((ROOT / name).stat().st_size for name in manifest if name != 'social')
    largest = sum(data['variants'][-1]['bytes'] for data in manifest.values() if isinstance(data, dict))
    print(f'PASS: {len(page.images)} responsive images; local links, anchors, fonts, fingerprints, JSON-LD and sitemap valid.')
    print(f'Image payload: {original / 1e6:.2f} MB originals -> {largest / 1e6:.2f} MB largest display variants ({100 * (1 - largest/original):.1f}% smaller).')

if __name__ == '__main__':
    main()
