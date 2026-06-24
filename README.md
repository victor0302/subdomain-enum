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

## Output formats

### Text

One subdomain per line, sorted. Pass `--with-ips` to append resolved IPs (tab-separated).

```
api.example.com
www.example.com

# --with-ips
api.example.com	93.184.216.34
www.example.com	93.184.216.34, 2606:2800:220:1:248:1893:25c8:1946
```

### JSON

Array of objects, sorted by `subdomain`:

```json
[
  {"subdomain": "api.example.com", "ips": ["93.184.216.34"], "source": "dns"},
  {"subdomain": "www.example.com", "ips": [], "source": "ct"}
]
```

`source` is `dns`, `ct`, or `dns,ct` when the same subdomain came from both.
