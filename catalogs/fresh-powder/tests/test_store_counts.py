"""Retailer facets count the same selected offers as the visible snow query."""

import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import aggregator.db as db_module
import pytest
from aggregator.models import AggregatedDeal
from deal_common.offers import VariantOffer


@pytest.fixture
def store_count_db(tmp_path):
    path = tmp_path / 'store-counts.db'
    now = datetime.now(UTC).replace(tzinfo=None)

    def deal(key, store='Evo', *, category='skis', at=now, price=250, name=None):
        return AggregatedDeal(
            id=None, store=store, name=name or f'Atomic {key} Skis 2025',
            url=f'https://example.com/{key}', current_price=price, original_price=1000,
            discount_pct=100 - price / 10, category=category, sizes='S, M',
            length_min=170, length_max=180, scraped_at=at, brand='atomic',
        )

    def offer(product, key, size, price, stock='in_stock'):
        return VariantOffer(
            variant_key=key, size=size, options=f'Size: {size}',
            current_price=price, original_price=1000, availability=stock,
            url=product.url + '?variant=' + key,
        )

    equipment = deal('equipment')
    equipment.offers = [offer(equipment, '1', 'M', 250), offer(equipment, '2', 'S', 800)]
    unknown = deal('unknown-stock', price=200)
    unknown.offers = [offer(unknown, '3', 'S', 200, 'unknown')]
    competing = deal('competing', 'Backcountry', price=300)
    competing.offers = [offer(competing, '4', 'S', 300), offer(competing, '5', 'M', 350)]
    rows = [
        equipment, unknown, competing,
        deal('legacy', 'Backcountry', price=400),
        deal('jacket', category='jackets', name='Atomic Shell Jacket 2025', price=100),
        deal('children', name='Atomic Kids Skis 2025'),
        deal('cad', 'The Circle Whistler'),
        deal('old-batch', at=now - timedelta(minutes=10)),
        deal('stale', 'Stale Store', at=now - timedelta(days=2)),
        deal('future', 'Future Store', at=now + timedelta(days=1)),
    ]

    async def initialize():
        await db_module.init_db(path)
        await db_module.upsert_deals(rows, path)

    asyncio.run(initialize())
    return path


def test_store_counts_use_visible_eligibility_without_changing_health_counts(store_count_db):
    async def run():
        all_items = await db_module.query_deals(count_by_store=True, db_path=store_count_db)
        assert all_items == {'Backcountry': 2, 'Evo': 3, 'The Circle Whistler': 1}
        equipment = await db_module.query_deals(
            count_by_store=True, include_clothing=False, db_path=store_count_db)
        assert equipment == {'Backcountry': 2, 'Evo': 2, 'The Circle Whistler': 1}
        # Selecting a retailer must leave the other retailer choices discoverable.
        assert await db_module.query_deals(
            store='Evo', count_by_store=True, db_path=store_count_db) == all_items
        health = {row['store']: row['deal_count'] for row in await db_module.store_status(store_count_db)}
        assert health['Evo'] == 4  # Ingestion still includes the excluded children row.
        assert health['Stale Store'] == health['Future Store'] == 1

    asyncio.run(run())


def test_store_counts_select_exact_variant_before_discount_and_stock(store_count_db):
    async def run():
        assert await db_module.query_deals(
            size='S', min_discount=40, count_by_store=True, db_path=store_count_db,
        ) == {'Backcountry': 1}
        # The inexpensive M sibling cannot inflate the requested S discount.
        assert await db_module.query_deals(
            size='S', count_by_store=True, db_path=store_count_db,
        ) == {'Backcountry': 1, 'Evo': 1}
        assert await db_module.query_deals(
            size='S', max_price=500, count_by_store=True, db_path=store_count_db,
        ) == {'Backcountry': 1}

    asyncio.run(run())


@pytest.mark.parametrize('filters', [
    {'include_clothing': False}, {'category': 'jackets'}, {'currency': 'CAD'},
    {'min_price': 300, 'max_price': 500}, {'min_reference': 1100},
    {'q': 'competing'}, {'brand': 'salomon'}, {'year_from': 2026},
    {'size_min': 175, 'size_max': 185}, {'reviewed_only': True},
    {'tax_free_only': True, 'tax_free_stores': {'Evo'}}, {'sort_by': 'price_low'},
])
def test_store_counts_share_all_other_query_filters(store_count_db, filters):
    async def run():
        counts = await db_module.query_deals(
            **filters, count_by_store=True, limit=1, offset=100, db_path=store_count_db)
        expected = {}
        for store in ['Evo', 'Backcountry', 'The Circle Whistler', 'Stale Store', 'Future Store']:
            count = await db_module.query_deals(
                **filters, store=store, count_only=True, db_path=store_count_db)
            if count:
                expected[store] = count
        assert counts == expected

    asyncio.run(run())


def test_store_counts_issue_one_grouped_query(store_count_db, monkeypatch):
    statements = []
    original_connect = db_module._connect

    @asynccontextmanager
    async def traced_connect(*args, **kwargs):
        async with original_connect(*args, **kwargs) as connection:
            await connection.set_trace_callback(statements.append)
            yield connection

    monkeypatch.setattr(db_module, '_connect', traced_connect)
    counts = asyncio.run(db_module.query_deals(count_by_store=True, db_path=store_count_db))
    assert sum(counts.values()) == 6
    queries = [s for s in statements if s.lstrip().upper().startswith(('WITH ', 'SELECT '))]
    assert len(queries) == 1
    assert 'GROUP BY deals.store' in queries[0]
