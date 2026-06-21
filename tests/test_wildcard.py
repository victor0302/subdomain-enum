import asyncio
from unittest.mock import AsyncMock, patch

import dns.resolver

from subdomain_enum.sources import Finding
from subdomain_enum.wildcard import WildcardReport, detect, suppress


def _answer(addresses):
    return [type("R", (), {"address": a})() for a in addresses]


def test_detect_no_wildcard_returns_negative_report():
    with patch("dns.asyncresolver.Resolver") as cls:
        cls.return_value.resolve = AsyncMock(side_effect=dns.resolver.NXDOMAIN())
        report = asyncio.run(detect("example.com", probes=3))
    assert report.is_wildcard is False
    assert report.addresses == frozenset()


def test_detect_wildcard_captures_addresses():
    async def fake_resolve(qname, rdtype, lifetime):
        if rdtype == "A":
            return _answer(["10.0.0.1"])
        return _answer([])

    with patch("dns.asyncresolver.Resolver") as cls:
        cls.return_value.resolve = AsyncMock(side_effect=fake_resolve)
        report = asyncio.run(detect("example.com", probes=2))
    assert report.is_wildcard is True
    assert report.addresses == frozenset({"10.0.0.1"})


def test_detect_short_circuits_on_first_clean_probe():
    calls: list[str] = []

    async def fake_resolve(qname, rdtype, lifetime):
        calls.append(qname)
        raise dns.resolver.NXDOMAIN()

    with patch("dns.asyncresolver.Resolver") as cls:
        cls.return_value.resolve = AsyncMock(side_effect=fake_resolve)
        asyncio.run(detect("example.com", probes=5))
    # First probe = first qname; we issue A then AAAA so 2 calls max for one qname.
    assert len({c for c in calls}) == 1


def test_suppress_removes_pure_wildcard_hits():
    report = WildcardReport(is_wildcard=True, addresses=frozenset({"10.0.0.1"}))
    findings = [
        Finding(name="real.example.com", source="dns", addresses=("93.184.216.34",)),
        Finding(name="wild.example.com", source="dns", addresses=("10.0.0.1",)),
    ]
    kept = suppress(findings, report)
    assert [f.name for f in kept] == ["real.example.com"]


def test_suppress_keeps_partial_overlap():
    report = WildcardReport(is_wildcard=True, addresses=frozenset({"10.0.0.1"}))
    findings = [
        Finding(name="x.example.com", source="dns", addresses=("10.0.0.1", "1.2.3.4")),
    ]
    kept = suppress(findings, report)
    assert kept == findings


def test_suppress_noop_when_not_wildcard():
    report = WildcardReport(is_wildcard=False)
    findings = [Finding(name="a.example.com", source="dns", addresses=("10.0.0.1",))]
    assert suppress(findings, report) == findings
