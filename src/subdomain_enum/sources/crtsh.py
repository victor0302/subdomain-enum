from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections.abc import Iterable

from . import Finding

CRTSH_URL = "https://crt.sh/?q={query}&output=json"


def _fetch(domain: str, timeout: float) -> bytes:
    query = urllib.parse.quote(f"%.{domain}", safe="")
    url = CRTSH_URL.format(query=query)
    with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (https only)
        return resp.read()


def _parse(payload: bytes, domain: str) -> list[str]:
    rows = json.loads(payload)
    suffix = f".{domain}"
    names: set[str] = set()
    for row in rows:
        name_value = row.get("name_value", "")
        for raw in name_value.splitlines():
            name = raw.strip().lstrip("*.").lower()
            if not name:
                continue
            if name == domain or name.endswith(suffix):
                names.add(name)
    return sorted(names)


def lookup(domain: str, timeout: float = 30.0) -> Iterable[Finding]:
    payload = _fetch(domain, timeout)
    return [Finding(name=n, source="ct") for n in _parse(payload, domain)]


def merge(*results: Iterable[Finding]) -> list[Finding]:
    by_name: dict[str, Finding] = {}
    for batch in results:
        for f in batch:
            existing = by_name.get(f.name)
            if existing is None:
                by_name[f.name] = f
                continue
            sources = sorted(set(existing.source.split(",")) | {f.source})
            addresses = tuple(sorted(set(existing.addresses) | set(f.addresses)))
            by_name[f.name] = Finding(name=f.name, source=",".join(sources), addresses=addresses)
    return sorted(by_name.values(), key=lambda f: f.name)
