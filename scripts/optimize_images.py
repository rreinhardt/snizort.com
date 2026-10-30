#!/usr/bin/env python3
"""Regenerate responsive, fingerprinted assets. Requires ImageMagick and cwebp."""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
NAMES = {
    'satellite-2019.png': 'st-columbas-isle-satellite-2019',
    'p1.png': 'snizort-statistical-account-part-1',
    'p2.png': 'snizort-statistical-account-part-2',
    'inverness-shire-isle-of-skye-xxiii.6-snizort-survey-date-1877-publication-date-1878.png': 'skeabost-ordnance-survey-1877',
    'skeabost-1885.png': 'skeabost-chapel-muir-1885',
    'slab.png': 'skeabost-effigy-macleod-1910',
    'screen-shot-2019-04-22-at-1.33.23-pm.png': 'skeabost-supernatural-story-1921',
    'canmore_image_DP00038685.jpg': 'effigy-calder-drawing-1921',
    'canmore_image_SC01471995.jpg': 'effigy-photograph-1921',
    'canmore_image_SC01006954.jpg': 'effigy-photograph-2000',
    'slab-2017.jpg': 'effigy-photograph-2017',
    'canmore_image_SC01471994.jpg': 'chapel-ruins-1920s-exterior',
    'canmore_image_SC01471992.jpg': 'chapel-ruins-1920s',
    'canmore_image_SC01006948.jpg': 'chapel-ruins-2000',
    'inside.jpg': 'chapel-interior-2017',
    'img146.jpeg': 'river-snizort-sign-2017',
    'img144.jpeg': 'st-columbas-isle-direction-sign-2017',
    'img138.jpeg': 'st-columbas-isle-graveyard-2017',
    'img147.jpeg': 'st-columbas-isle-grave-mounds-2017',
    'end.jpeg': 'st-columbas-isle-carved-stone-detail',
}
SCANS = {'p1.png', 'p2.png', 'slab.png', 'skeabost-1885.png',
         'screen-shot-2019-04-22-at-1.33.23-pm.png',
         'inverness-shire-isle-of-skye-xxiii.6-snizort-survey-date-1877-publication-date-1878.png'}
GALLERY = set(list(NAMES)[7:-1])

def run(*args):
    return subprocess.check_output(args, text=True).strip()

def fingerprint(path, stem, suffix):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    target = ASSETS / f'{stem}.{digest}.{suffix}'
    shutil.copyfile(path, target)
    return target.relative_to(ROOT).as_posix()

def main():
    for tool in ('magick', 'cwebp'):
        if not shutil.which(tool):
            raise SystemExit(f'Install {tool} before regenerating assets.')
    ASSETS.mkdir(exist_ok=True)
    manifest = {}
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp)
        for original, stem in NAMES.items():
            source = ROOT / original
            width, height = map(int, run('magick', 'identify', '-format', '%w %h', str(source)).split())
            max_width = min(width, 900 if original in GALLERY else 1440)
            widths = sorted({min(width, 450 if original in GALLERY else 480),
                             min(max_width, 900 if original in GALLERY else 960), max_width})
            if original == 'satellite-2019.png':
                widths = sorted({min(width, size) for size in (480, 768, 1024, 1440)})
            variants = []
            for size in widths:
                png, webp = tmp / 'resized.png', tmp / 'image.webp'
                run('magick', str(source), '-auto-orient', '-resize', f'{size}x>', '-strip', str(png))
                run('cwebp', '-quiet', '-m', '6', '-q', '90' if original in SCANS else '82', str(png), '-o', str(webp))
                variants.append({'width': size, 'path': fingerprint(webp, f'{stem}-{size}', 'webp'), 'bytes': webp.stat().st_size})
            manifest[original] = {'width': width, 'height': height, 'variants': variants}
        social = tmp / 'social.jpg'
        run('magick', str(ROOT / 'img138.jpeg'), '-auto-orient', '-resize', '1200x630^',
            '-gravity', 'center', '-extent', '1200x630', '-strip', '-quality', '84', str(social))
        manifest['social'] = fingerprint(social, 'st-columbas-isle-social', 'jpg')
    font = ASSETS / ('Monarch.' + hashlib.sha256((ROOT / 'Monarch.woff').read_bytes()).hexdigest()[:12] + '.woff')
    shutil.copyfile(ROOT / 'Monarch.woff', font)
    css = (ROOT / 'style.css').read_text().replace('url("Monarch.woff")', f'url("{font.name}")')
    css_path = ASSETS / ('site.' + hashlib.sha256(css.encode()).hexdigest()[:12] + '.css')
    css_path.write_text(css)
    page = (ROOT / 'index.html').read_text()
    def update_image(match):
        tag = match[0]
        name = html.unescape(re.search(r'data-original="([^"]+)"', tag)[1])
        data = manifest[name]
        tag = re.sub(r'\s(?:src|srcset|width|height)="[^"]*"', '', tag)
        variants = data['variants']
        default = next((v for v in variants if v['width'] >= (450 if name in GALLERY else 960)), variants[-1])
        attrs = f' src="{default["path"]}" srcset="' + ', '.join(f'{v["path"]} {v["width"]}w' for v in variants) + '"'
        return tag[:-1] + attrs + f' width="{data["width"]}" height="{data["height"]}">'
    page = re.sub(r'<img\b[^>]*data-original="[^"]+"[^>]*>', update_image, page)
    page = re.sub(r'href="(?:style\.css|assets/site\.[a-f0-9]+\.css)"', f'href="{css_path.relative_to(ROOT)}"', page)
    page = re.sub(r'https://snizort\.net/(?:satellite-2019\.png|assets/st-columbas-isle-social\.[a-f0-9]+\.jpg)',
                  'https://snizort.net/' + manifest['social'], page)
    (ROOT / 'index.html').write_text(page)
    (ROOT / 'scripts/image-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    largest = sum(x['variants'][-1]['bytes'] for x in manifest.values() if isinstance(x, dict))
    print(f'Generated {len(NAMES)} responsive image sets; largest variants total {largest / 1_000_000:.2f} MB.')

if __name__ == '__main__':
    main()
