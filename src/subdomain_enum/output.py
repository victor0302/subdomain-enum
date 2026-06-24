from __future__ import annotations

import json
from collections.abc import Iterable

from .sources import Finding


def _to_dict(f: Finding) -> dict:
    return {
        "subdomain": f.name,
        "ips": list(f.addresses),
        "source": f.source,
    }


def render_text(findings: Iterable[Finding], *, with_ips: bool = False) -> str:
    fs = sorted(findings, key=lambda f: f.name)
    if not fs:
        return "No subdomains found."
    if not with_ips:
        return "\n".join(f.name for f in fs)
    lines: list[str] = []
    for f in fs:
        ips = ", ".join(f.addresses) if f.addresses else "(no addresses)"
        lines.append(f"{f.name}\t{ips}")
    return "\n".join(lines)


def render_json(findings: Iterable[Finding]) -> str:
    fs = sorted(findings, key=lambda f: f.name)
    return json.dumps([_to_dict(f) for f in fs], indent=2)
