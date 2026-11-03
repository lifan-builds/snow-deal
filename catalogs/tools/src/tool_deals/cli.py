from deal_common.catalog.cli import catalog_cli
from tool_deals.catalog import CATALOG

cli = catalog_cli(CATALOG)

if __name__ == "__main__":
    cli()
