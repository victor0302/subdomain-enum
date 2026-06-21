import asyncio
from unittest.mock import AsyncMock, patch

import dns.resolver

from subdomain_enum.sources.dns_brute import bruteforce_collect


def _answer(addresses):
    return [type("R", (), {"address": a})() for a in addresses]


def test_collects_hits_and_skips_misses():
    async def fake_resolve(qname, rdtype, lifetime):
        if qname == "www.example.com" and rdtype == "A":
            return _answer(["93.184.216.34"])
        if qname == "api.example.com" and rdtype == "AAAA":
            return _answer(["2606:2800:220:1:248:1893:25c8:1946"])
        raise dns.resolver.NXDOMAIN()

    with patch("dns.asyncresolver.Resolver") as cls:
        cls.return_value.resolve = AsyncMock(side_effect=fake_resolve)
        results = asyncio.run(
            bruteforce_collect("example.com", ["www", "api", "missing"], concurrency=10)
        )
    by_name = {r.name: r for r in results}
    assert set(by_name) == {"www.example.com", "api.example.com"}
    assert by_name["www.example.com"].addresses == ("93.184.216.34",)
    assert by_name["api.example.com"].addresses == ("2606:2800:220:1:248:1893:25c8:1946",)
    assert all(r.source == "dns" for r in results)


def test_timeout_does_not_crash():
    async def always_timeout(qname, rdtype, lifetime):
        raise dns.exception.Timeout()

    import dns.exception

    with patch("dns.asyncresolver.Resolver") as cls:
        cls.return_value.resolve = AsyncMock(side_effect=always_timeout)
        results = asyncio.run(bruteforce_collect("example.com", ["a", "b"], concurrency=5))
    assert results == []


def test_skips_blank_and_comment_words():
    with patch("dns.asyncresolver.Resolver") as cls:
        cls.return_value.resolve = AsyncMock(side_effect=dns.resolver.NXDOMAIN())
        asyncio.run(bruteforce_collect("example.com", ["", "  ", "# comment", "x"]))
        called = cls.return_value.resolve.await_args_list
    qnames = {call.args[0] for call in called}
    assert qnames == {"x.example.com"}


def test_concurrency_semaphore_limits_in_flight():
    in_flight = 0
    peak = 0

    async def slow(qname, rdtype, lifetime):
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        raise dns.resolver.NXDOMAIN()

    with patch("dns.asyncresolver.Resolver") as cls:
        cls.return_value.resolve = AsyncMock(side_effect=slow)
        asyncio.run(
            bruteforce_collect("example.com", [f"w{i}" for i in range(20)], concurrency=3)
        )
    # Each slot fans out A + AAAA in parallel, so peak ≤ 2 * concurrency.
    assert peak <= 6
