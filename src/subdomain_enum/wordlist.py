from __future__ import annotations

from importlib import resources
from pathlib import Path

DEFAULT_WORDLIST_RESOURCE = "default-wordlist.txt"


def load(path: Path | None = None) -> list[str]:
    if path is not None:
        text = path.read_text()
    else:
        text = resources.files("subdomain_enum.data").joinpath(
            DEFAULT_WORDLIST_RESOURCE
        ).read_text()
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    ]


def default_path() -> Path:
    return Path(
        str(
            resources.files("subdomain_enum.data").joinpath(DEFAULT_WORDLIST_RESOURCE)
        )
    )
