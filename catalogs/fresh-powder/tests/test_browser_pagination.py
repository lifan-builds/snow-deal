"""Observed newsletter-overlay regression; failed traversal stays incomplete."""
import asyncio

import pytest
from aggregator.browser import _try_next_page


@pytest.mark.parametrize(("host", "popup", "growth", "close_fails", "succeeds"), [
    ("www.skiessentials.com", True, True, False, True),
    ("skiessentials.com", True, True, False, True),
    ("www.skiessentials.com", False, True, False, True),
    ("other.example", True, True, False, False),
    ("www.skiessentials.com", True, False, False, False),
    ("www.skiessentials.com", True, True, True, False),
])
def test_show_more_dismisses_only_known_popup(host, popup, growth, close_fails, succeeds):
    class Element:
        def __init__(self, page, kind):
            self.page, self.kind = page, kind

        async def get_attribute(self, name):
            return None

        async def is_visible(self):
            return True

        async def click(self):
            if self.kind == "close":
                if close_fails:
                    raise TimeoutError("Close control failed")
                self.page.popup = False
                self.page.closed = True
            else:
                if self.page.popup:
                    raise TimeoutError("Newsletter intercepts pointer events")
                self.page.products += 48 if growth else 0

    class Page:
        url = f"https://{host}/collections/alpine-skis"
        products = 48
        closed = False
        waited_for_growth = False

        def __init__(self):
            self.popup = popup

        async def query_selector(self, selector):
            if selector == 'button:has-text("SHOW MORE")':
                return Element(self, "next")
            assert selector == '[role="dialog"][aria-label="POPUP Form"] button[aria-label="Close dialog"]'
            return Element(self, "close") if self.popup else None

        def locator(self, selector):
            assert selector == '[data-testid="product-card-title"]'
            return self

        async def count(self):
            return self.products

        async def wait_for_function(self, script, *, arg, timeout):
            self.waited_for_growth = True
            assert arg == 48
            if self.products <= arg:
                raise TimeoutError("Product count did not increase")

        async def wait_for_load_state(self, state):
            assert state == "domcontentloaded"

    async def run():
        page = Page()
        if succeeds:
            assert await _try_next_page(page, 'button:has-text("SHOW MORE")')
            assert page.products == 96
            assert page.waited_for_growth
            assert page.closed == popup
        else:
            with pytest.raises(RuntimeError, match="Next-page navigation failed"):
                await _try_next_page(page, 'button:has-text("SHOW MORE")')
            if host == "other.example":
                assert not page.closed

    asyncio.run(run())
