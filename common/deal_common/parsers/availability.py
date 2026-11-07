"""Source-specific shipping evidence shared by Shopify ingestion and audit."""
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from deal_common.parsers.harvey import shipping_notice as harvey_shipping_notice


def shipping_notice(item: dict, variant: dict, url: str) -> str:
    host = (urlsplit(url).hostname or '').removeprefix('www.')
    if host in {'cyberweld.com', 'store.cyberweld.com'}:
        tags = item.get('tags') or []
        if isinstance(tags, str):
            tags = tags.split(',')
        if any(str(tag).strip().casefold() == 'auto_outofstock' for tag in tags):
            return 'Retailer marks this product out of stock.'
    if host == 'bakersgas.com':
        # Feed body_html and the independently fetched product.js description
        # carry the same active notice. Service-parts promises are not stock.
        for field in ('body_html', 'description'):
            body = BeautifulSoup(str(item.get(field) or ''), 'html.parser')
            for element in body(['script', 'style']):
                element.decompose()
            text = ' '.join(body.stripped_strings)
            notice = re.search(r'\b(?:machine|welder|product|item)\s+is\s+(?:currently\s+)?'
                               r'on\s+back[- ]?order\b[^.!?]{0,120}[.!?]?', text, re.IGNORECASE)
            if notice:
                return 'Retailer shipping notice: ' + notice[0].strip()
    if host == 'weldingsuppliesfromioc.com':
        for field in ('body_html', 'description'):
            body = BeautifulSoup(str(item.get(field) or ''), 'html.parser')
            for element in body(['script', 'style', 'template']):
                element.decompose()
            text = ' '.join(body.stripped_strings)
            notice = re.search(
                r'(?:^|(?<=[.!?])\s+)(These\s+(?:generators|machines|packages)\s+are\s+'
                r'(?:typically\s+)?made[- ]to[- ]order\s+from\s+(?:Miller(?:\s+Electric)?|Lincoln)\.\s+'
                r'Please\s+(?:allow\s+\d{1,2}-\d{1,2}\s+weeks\s+for\s+'
                r'(?:your\s+order\s+to\s+ship|shipment|shipping)|'
                r'expect\s+a\s+\d{1,2}-\d{1,2}\s+week\s+lead\s+time)\.)',
                text, re.IGNORECASE,
            )
            if notice:
                return 'Retailer shipping notice: ' + notice[1]
    return harvey_shipping_notice(item, variant, url)
