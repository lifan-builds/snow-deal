#!/usr/bin/env python3
"""Read-only audit of public comparison pages and a bounded merchant sample.

No app imports, credentials, browser state or database access. Merchant HTTP
reachability is not proof of variant availability or price agreement.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup


def fetch(url):
    try:
        request = Request(url, headers={'User-Agent': 'FreshPowder-public-quality-audit/1.0'})
        with urlopen(request, timeout=15) as response:
            return response.status, response.read(3_000_000).decode('utf-8', errors='replace')
    except HTTPError as error:
        return error.code, ''
    except (URLError, TimeoutError, OSError):
        return 0, ''


def audit_model(url):
    status, html = fetch(url)
    soup = BeautifulSoup(html, 'html.parser')
    canonical = soup.select_one('link[rel=canonical]')
    offers = []
    for row in soup.select('.retailer-offer'):
        checked = row.select_one('.offer-checked')
        price = row.select_one('.offer-price')
        offers.append({'model_url': url, 'merchant_url': row.get('data-href'),
                       'store': row.get('data-store'), 'name': row.get('data-name'),
                       'price_label': price.get_text(' ', strip=True) if price else None,
                       'checked_label': checked.get_text(' ', strip=True) if checked else None})
    schemas = []
    for script in soup.select('script[type="application/ld+json"]'):
        try: schemas.append(json.loads(script.string or script.get_text()))
        except ValueError: pass
    product = next((s for s in schemas if isinstance(s, dict) and s.get('@type') == 'Product'), {})
    schema_count = product.get('offers', {}).get('offerCount', 0)
    return {'url': url, 'http_status': status, 'canonical_matches': bool(canonical and canonical.get('href') == url),
            'rendered_offers': len(offers), 'schema_offer_count': schema_count,
            'schema_count_matches': schema_count == len(offers), 'offers': offers}


def merchant_check(offer):
    status, html = fetch(offer['merchant_url'])
    # The HTML title is a diagnostic clue, never a fuzzy identity acceptance.
    soup = BeautifulSoup(html, 'html.parser') if html else None
    title = soup.title.get_text(' ', strip=True)[:250] if soup and soup.title else None
    return {**offer, 'merchant_http_status': status, 'merchant_title': title,
            'disposition': 'reachable_requires_variant_review' if status == 200 else 'unverified_access_or_link_issue',
            'variant_price_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', default='https://freshpowder.clifan.com')
    parser.add_argument('--merchant-sample', type=int, default=0)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 0 <= args.merchant_sample <= 50: parser.error('merchant sample must be 0–50')
    base = args.site.rstrip('/')
    status, xml = fetch(base+'/sitemap.xml')
    if status != 200: raise SystemExit('Could not read public sitemap')
    urls = [node.text for node in ET.fromstring(xml).iter() if node.tag.endswith('loc')]
    model_urls = [url for url in urls if url.startswith(base+'/products/')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages = list(pool.map(audit_model, model_urls))
    by_store = defaultdict(list)
    for page in pages:
        for offer in page['offers']:
            if offer['merchant_url']: by_store[offer['store']].append(offer)
    sample = []
    # Deterministic round-robin across merchants, not a top-discount sample.
    while len(sample) < args.merchant_sample and any(by_store.values()):
        for store in sorted(by_store):
            if by_store[store] and len(sample) < args.merchant_sample:
                sample.append(by_store[store].pop(0))
    with ThreadPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(merchant_check, sample))
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'site': base,
              'sitemap_urls': len(urls), 'model_pages': len(pages),
              'page_issues': [p['url'] for p in pages if p['http_status'] != 200 or not p['canonical_matches'] or not p['schema_count_matches']],
              'rendered_offer_total': sum(p['rendered_offers'] for p in pages),
              'merchant_sample_size': len(checks),
              'merchant_http_counts': dict(Counter(str(c['merchant_http_status']) for c in checks)),
              'limitations': 'Public comparison pages only; sample is store-balanced, not traffic-ranked or statistically representative. HTTP 200 does not verify product identity, price, condition, stock or selected variant. Non-200 can be an access restriction. No raw merchant HTML retained.',
              'pages': pages, 'merchant_checks': checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'pages','merchant_checks'}},indent=2))


if __name__ == '__main__': main()
