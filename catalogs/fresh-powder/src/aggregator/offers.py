"""Persist selectable offers and select a matching offer before sorting/pagination."""
from deal_common.offers import size_key

SCHEMA = """
CREATE TABLE IF NOT EXISTS deal_offers (
    product_url TEXT NOT NULL, variant_key TEXT NOT NULL, url TEXT NOT NULL,
    size TEXT, size_key TEXT NOT NULL, options TEXT NOT NULL,
    current_price REAL NOT NULL, original_price REAL NOT NULL, discount_pct REAL NOT NULL,
    availability TEXT NOT NULL, image_url TEXT, reference_basis TEXT NOT NULL,
    PRIMARY KEY(product_url, variant_key)
);
CREATE TABLE IF NOT EXISTS offer_observations (
    product_url TEXT NOT NULL, variant_key TEXT NOT NULL, observed_at TEXT NOT NULL,
    price REAL NOT NULL, reference_price REAL NOT NULL, currency TEXT NOT NULL,
    availability TEXT NOT NULL, reference_basis TEXT NOT NULL, product_name TEXT NOT NULL,
    PRIMARY KEY(product_url, variant_key, observed_at)
);
"""


async def write_offers(db, deal):
    # Replace only this observed product's current variants; retain dated evidence.
    await db.execute('DELETE FROM deal_offers WHERE product_url = ?', (deal.url,))
    for offer in deal.offers:
        if offer.discount_pct <= 0:
            continue
        await db.execute('INSERT INTO deal_offers VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            deal.url, offer.variant_key, offer.url, offer.size, size_key(offer.size), offer.options,
            offer.current_price, offer.original_price, offer.discount_pct, offer.availability,
            offer.image_url, offer.reference_basis,
        ))
        await db.execute('INSERT OR REPLACE INTO offer_observations VALUES (?,?,?,?,?,?,?,?,?)', (
            deal.url, offer.variant_key, deal.scraped_at.isoformat(), offer.current_price,
            offer.original_price, deal.currency, offer.availability, offer.reference_basis, deal.name,
        ))


def selection_sql(*, size='', size_min=None, size_max=None, min_price=0, max_price=0,
                  min_reference=0, min_discount=0):
    # Old snapshots cache rounded percentages. Derive decisions from their prices
    # without migrating the snapshot or altering historical observations.
    pct = 'price_discount(o.current_price, o.original_price)'
    conditions = ['o.current_price >= 1', f'{pct} > 0', f'{pct} < 95']
    params = []
    for sql, value in [('o.current_price >= ?', min_price), ('o.current_price <= ?', max_price),
                       ('o.original_price >= ?', min_reference), (f'{pct} >= ?', min_discount)]:
        if value:
            conditions.append(sql)
            params.append(value)
    if size:
        conditions.extend(['o.size_key = ?', "o.availability = 'in_stock'"])
        params.append(size_key(size))
    if size_min is not None or size_max is not None:
        conditions.append("matches_length(o.size, ?, ?) = 1 AND d.category IN ('skis', 'snowboards')")
        params.extend([size_min, size_max])
    # Keep product identity stable; expose the selected variant only as the purchase URL.
    fields = ['id', 'store', 'name', 'url', 'category', 'length_min', 'length_max', 'scraped_at',
              'brand', 'first_seen', 'currency', 'product_type', 'exclusion_reason']
    columns = ', '.join('d.' + field for field in fields)
    for field in ['current_price', 'original_price', 'image_url']:
        columns += f', CASE WHEN o.product_url IS NOT NULL THEN o.{field} ELSE d.{field} END AS {field}'
    columns += f', CASE WHEN o.product_url IS NOT NULL THEN {pct} ELSE price_discount(d.current_price, d.original_price) END AS discount_pct'
    columns += ', CASE WHEN o.product_url IS NOT NULL THEN o.size ELSE d.sizes END AS sizes'
    columns += ", o.url AS offer_url, o.variant_key, o.options AS offer_options, COALESCE(o.availability, 'unknown') AS availability, COALESCE(o.reference_basis, 'retailer_reference') AS reference_basis"
    return f"""WITH ranked_offers AS (
        SELECT o.*, ROW_NUMBER() OVER (
            PARTITION BY o.product_url ORDER BY {pct} DESC, o.current_price, o.variant_key
        ) AS priority
        FROM deal_offers o JOIN deals d ON d.url = o.product_url
        WHERE {' AND '.join(conditions)}
    ), effective AS (
        SELECT {columns} FROM deals d
        LEFT JOIN ranked_offers o ON o.product_url = d.url AND o.priority = 1
        WHERE o.product_url IS NOT NULL
           OR NOT EXISTS (SELECT 1 FROM deal_offers any_offer WHERE any_offer.product_url = d.url)
    ) """, params
