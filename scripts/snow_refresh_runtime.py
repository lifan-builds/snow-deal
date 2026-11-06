"""Report browser requirements for the snow workflow's selected retailers."""

import os
from collections.abc import Iterable
from pathlib import Path

from aggregator.config import STORES, StoreConfig


def browser_required(selection: str, stores: Iterable[StoreConfig]) -> bool:
    """Skip Chromium only for an explicit selection of known HTTP retailers."""
    if not selection:
        return True
    by_name = {store.name: store for store in stores}
    # Keep exact names, as the workflow's comma split and Click choices do.
    # Malformed/unknown input still reaches the existing CLI validation.
    return any(
        name not in by_name or by_name[name].use_browser
        for name in selection.split(',')
    )


def main() -> None:
    required = browser_required(os.environ.get('REFRESH_STORES', ''), STORES)
    result = f'browser_required={str(required).lower()}\n'
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with Path(output).open('a', encoding='utf-8') as destination:
            destination.write(result)
    else:
        print(result, end='')


if __name__ == '__main__':
    main()
