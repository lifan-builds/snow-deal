from deal_common.catalog.cli import catalog_cli
from cycling_deals.catalog import CATALOG

cli = catalog_cli(CATALOG)

if __name__ == "__main__":
    cli()
