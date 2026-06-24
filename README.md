# subdomain-enum

Enumerate subdomains for a given domain.

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
subdomain-enum <domain>
```

## Develop

```bash
ruff check .
pytest
```

## Bundled wordlist

A small (~800 entry) curated wordlist ships at `src/subdomain_enum/data/default-wordlist.txt`. It's loaded automatically when `-w/--wordlist` is not provided. The list was hand-curated from common subdomain conventions (no upstream attribution required) — feel free to point `-w` at a larger list (e.g. SecLists) for deeper sweeps.
