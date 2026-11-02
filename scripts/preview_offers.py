"""Serve synthetic offer examples on loopback, without existing data or credentials.

Run: .venv/bin/python scripts/preview_offers.py
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if '--serve' not in sys.argv:
        with tempfile.TemporaryDirectory(prefix='freshpowder-offer-preview-') as directory:
            env = {k:os.environ[k] for k in ('PATH','LANG') if k in os.environ}
            env.update(PYTHONPATH=os.pathsep.join([str(ROOT/'common'),str(ROOT/'catalogs/fresh-powder/src')]),
                       DATABASE_PATH=str(Path(directory)/'demo.db'), AUTH_DB_PATH=str(Path(directory)/'auth.db'),
                       PUBLIC_MODE='1', DISABLE_APP_LIFESPAN='1', SITE_URL='http://127.0.0.1:8765')
            return subprocess.call([sys.executable,__file__,'--serve'],env=env)
    import asyncio
    from datetime import datetime, timezone
    from aggregator.db import init_db, upsert_deals
    from aggregator.auth_db import init_auth_db
    from aggregator.models import AggregatedDeal
    from deal_common.offers import VariantOffer
    import uvicorn
    now=datetime.now(timezone.utc).replace(tzinfo=None)
    deals=[]
    for i,(name,category,size,price,original) in enumerate([
        ('Sample Carbon Skis 2025','skis','180',320,1000),
        ('Sample All-Mountain Skis 2024','skis','180',350,900),
        ('Sample Touring Boots 2025','ski boots','27.5',240,800),
        ('Sample Freeride Snowboard 2025','snowboards','156',280,700),
        ('Sample Legacy Skis 00 - 01','skis','190',150,600),
        ('Sample Alpine Boots 2024','ski boots','26.5',300,600),
    ]):
        url=f'https://example.com/preview-{i}'
        offers=[VariantOffer('one',url+'?variant=one',price,original,size,size+' / Forest','in_stock'),
                VariantOffer('two',url+'?variant=two',price+100,original,'160','160 / Ochre','in_stock')]
        deals.append(AggregatedDeal(None,'Preview Store',name,url,price,original,round(100*(1-price/original),1),
                                   category,size,None,None,now,offers=offers))
    asyncio.run(init_db())
    asyncio.run(init_auth_db())
    asyncio.run(upsert_deals(deals))
    uvicorn.run('aggregator.web.app:create_app',factory=True,host='127.0.0.1',port=8765,log_level='warning')


if __name__=='__main__':
    raise SystemExit(main())
