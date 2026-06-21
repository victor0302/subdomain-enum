from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable

import dns.asyncresolver
import dns.exception
import dns.rdatatype
import dns.resolver

from . import Finding


async def _resolve_type(
    resolver: dns.asyncresolver.Resolver, qname: str, rdtype: str, timeout: float
) -> list[str]:
    try:
        answer = await resolver.resolve(qname, rdtype, lifetime=timeout)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return []
    except (dns.exception.Timeout, asyncio.TimeoutError):
        return []
    return [r.address for r in answer]


async def _resolve_subdomain(
    resolver: dns.asyncresolver.Resolver,
    sem: asyncio.Semaphore,
    qname: str,
    timeout: float,
) -> Finding | None:
    async with sem:
        a, aaaa = await asyncio.gather(
            _resolve_type(resolver, qname, "A", timeout),
            _resolve_type(resolver, qname, "AAAA", timeout),
        )
    addresses = tuple(sorted(set(a + aaaa)))
    if not addresses:
        return None
    return Finding(name=qname, source="dns", addresses=addresses)


async def bruteforce(
    domain: str,
    words: Iterable[str],
    concurrency: int = 50,
    timeout: float = 3.0,
) -> AsyncIterator[Finding]:
    resolver = dns.asyncresolver.Resolver()
    sem = asyncio.Semaphore(concurrency)
    cleaned = (w.strip() for w in words)
    tasks = [
        asyncio.create_task(_resolve_subdomain(resolver, sem, f"{w}.{domain}", timeout))
        for w in cleaned
        if w and not w.startswith("#")
    ]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        if result is not None:
            yield result


async def bruteforce_collect(
    domain: str,
    words: Iterable[str],
    concurrency: int = 50,
    timeout: float = 3.0,
) -> list[Finding]:
    return [f async for f in bruteforce(domain, words, concurrency, timeout)]
