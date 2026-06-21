from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field

import dns.asyncresolver
import dns.exception
import dns.resolver

from .sources import Finding


@dataclass(frozen=True)
class WildcardReport:
    is_wildcard: bool
    addresses: frozenset[str] = field(default_factory=frozenset)


async def _resolve_addresses(
    resolver: dns.asyncresolver.Resolver, qname: str, timeout: float
) -> set[str]:
    addrs: set[str] = set()
    for rdtype in ("A", "AAAA"):
        try:
            answer = await resolver.resolve(qname, rdtype, lifetime=timeout)
        except (
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers,
            dns.exception.Timeout,
            asyncio.TimeoutError,
        ):
            continue
        addrs.update(r.address for r in answer)
    return addrs


async def detect(
    domain: str,
    probes: int = 3,
    timeout: float = 3.0,
    resolver: dns.asyncresolver.Resolver | None = None,
) -> WildcardReport:
    res = resolver or dns.asyncresolver.Resolver()
    addresses: set[str] = set()
    for _ in range(probes):
        random_label = f"nonexistent-{uuid.uuid4().hex[:12]}"
        addrs = await _resolve_addresses(res, f"{random_label}.{domain}", timeout)
        if not addrs:
            return WildcardReport(is_wildcard=False)
        addresses.update(addrs)
    return WildcardReport(is_wildcard=True, addresses=frozenset(addresses))


def suppress(findings: Iterable[Finding], report: WildcardReport) -> list[Finding]:
    if not report.is_wildcard:
        return list(findings)
    kept: list[Finding] = []
    for f in findings:
        if f.addresses and set(f.addresses).issubset(report.addresses):
            continue
        kept.append(f)
    return kept
