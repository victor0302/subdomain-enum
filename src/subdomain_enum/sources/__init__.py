from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Finding:
    name: str
    source: str
    addresses: tuple[str, ...] = field(default_factory=tuple)
