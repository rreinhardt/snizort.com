# St Columba’s Isle

A buildless static collection about St Columba’s Isle (Skeabost Island), in the River Snizort on the Isle of Skye. The canonical public URL is https://snizort.net/.

## Edit and preview

Edit `index.html` and the source stylesheet `style.css`. Preserve source quotations and distinguish editorial notes from historical accounts. The statistical-account excerpt is labeled **1790s**: the series ran from 1791–99, and catalogue accounts differ on the precise parish-account date. References identify vol. 18, pp. 185–186. MacCulloch’s 1905 extract includes only the passages about Skeabost; the later discussion of the separate Kilmuir site has been omitted.

```sh
python3 -m http.server 8765 --bind 127.0.0.1
```

Open http://127.0.0.1:8765/. No JavaScript framework or runtime dependencies are needed to serve the site.

## Images and cache-safe assets

The root-level photographs, maps, scans and font are the original files. The original files are retained in the repository; the page displays optimized versions. Optimized WebP images, the social-sharing JPEG, CSS and the font are served from `assets/` with content fingerprints in their filenames.

After changing **images or `style.css`**, regenerate the display assets and HTML references:

```sh
# Requires ImageMagick (`magick`) and libwebp (`cwebp`).
python3 scripts/optimize_images.py
python3 scripts/check_site.py
```

`optimize_images.py` uses `data-original` attributes to associate display images with their originals. It writes `scripts/image-manifest.json`, responsive sizes, a 1200 × 630 social JPEG, fingerprinted CSS/font files, and updates image and stylesheet references in `index.html`. It does not upscale source images or replace originals. Keep the image mapping and checks in sync if adding a new photograph. Old fingerprinted assets are retained so cached HTML can still use them.

The first satellite image is eager and high priority. Other images are lazy, have explicit dimensions, and use `srcset`/`sizes`. The source scans are always visible beside their HTML transcriptions. The font uses `font-display: swap`.

## Netlify deployment

The existing public site's response headers identify Netlify. Publish the repository root, including `assets/`, `_headers`, `_redirects`, `robots.txt` and `sitemap.xml`. No build is required because optimized assets are checked in. Local code changes do not deploy until committed/pushed to the connected production branch or uploaded through the existing Netlify workflow.

- `_headers` sets one-year immutable caching for fingerprinted assets, one-week caching for original images/font, and revalidation for HTML and the source stylesheet.
- Netlify already serves HTML with gzip; do not set `Content-Encoding` manually.
- `_redirects` consolidates HTTP and `www.snizort.net` URLs onto HTTPS at the canonical host and redirects `/index.html` to `/`.
- An alias hostname must be connected to this Netlify site with valid DNS/TLS before redirects can work. No `.com` domain ownership or connection has been assumed. If a `.com` alias is owned and connected, add corresponding absolute-host redirect rules there.
- Update `sitemap.xml`’s `lastmod`, the visible update date and JSON-LD `dateModified` when making substantive content updates, not on every deploy.

After deployment, check the live document, an asset and redirects:

```sh
curl -I --compressed https://snizort.net/
curl -I https://snizort.net/assets/ACTUAL-FINGERPRINTED-FILE.webp
curl -I http://snizort.net/
curl -I https://www.snizort.net/
curl -I https://snizort.net/index.html
```

Expect an HTML 200, immutable caching for the fingerprinted asset, and permanent redirects to the canonical address. Use an actual path from the page for the asset check.

## Search and performance follow-up

These account/deployment actions require the existing site owner's access and cannot be completed by local HTML edits:

1. In Google Search Console, verify/select the `snizort.net` property. Use its verification token or DNS record; do not invent a token in this repository.
2. Submit `https://snizort.net/sitemap.xml`, inspect the homepage URL and request indexing after deployment.
3. Record queries and impressions for St Columba’s Isle, Skeabost Island and Snizort Cathedral. Compare after Google has recrawled; rankings are not guaranteed by these changes.
4. Run PageSpeed Insights on the deployed page and compare field Core Web Vitals when data is available. Local Lighthouse is a lab check, not a measurement of production users.
5. Check JSON-LD with Schema.org Validator. The page describes a historical place, not an operating business, and does not claim ratings, opening hours or unverified access arrangements.

Sources: [Google SEO guidance](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [image lazy loading](https://web.dev/articles/browser-level-image-lazy-loading), [Netlify headers](https://docs.netlify.com/manage/routing/headers/), [Netlify redirect options](https://docs.netlify.com/manage/routing/redirects/redirect-options/).
