"""Compatibility imports; implementation lives in deal_common.rate_limit."""

from deal_common.rate_limit import SlidingWindowRateLimiter, client_key

__all__ = ['SlidingWindowRateLimiter', 'client_key']
