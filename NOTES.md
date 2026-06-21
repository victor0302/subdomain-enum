# subdomain-enum — progress notes

Running log of what's been built and why. Append-only.

## 2026-06-17 — Issue #1: scaffolding

Laid down the project skeleton so the rest of the tickets have somewhere to land.

- `pyproject.toml` with PEP 621 metadata, a `subdomain-enum` console script entry point
- `src/` layout: `src/subdomain_enum/` package, version string, `cli.py`
- `tests/` with a passing smoke test
- ruff + pytest pinned via the `[dev]` extra

Decisions:
- **`src/` layout over flat layout.** Tests import the installed package — catches "works in-tree, breaks on install" early.
- **setuptools, not hatch/poetry.** Stdlib-adjacent, zero ceremony for a CLI with no exotic build needs.
- **ruff rules: `E, F, I, UP, B`.** Lint + import sort + modernizers + bugbear.

## 2026-06-17 — Issue #2: `enum` subcommand

Built out the CLI surface. Real DNS + crt.sh work lands in #3–#5.

- `subdomain-enum enum <domain>` subcommand
- `-w / --wordlist FILE` (consumed once #6 lands a bundled default)
- `--concurrency N` (default 50)
- `--timeout` per query (default 3.0s)
- `--output {text,json}`
- `--sources {dns,ct,all}` (default `all`)

Decisions:
- **Subcommand from day one.** Cheap to add now, expensive to retrofit. Leaves room for `wordlist info`, `bench`, etc.
- **No SARIF.** Subdomain discovery isn't a finding-shaped problem the way vuln scanners or secret scanners are. Text + JSON cover both human and pipeline use.
- **`--sources` as a fixed set, not a comma-separated list.** Cheap to widen later; we don't need flexibility we haven't proven we want.
- **Defaults tuned conservative** — 50 concurrent queries and a 3s timeout are gentle enough not to hammer a resolver during dev.

## Open follow-ups (tracked as issues)

- #3 async DNS bruteforce with concurrency control
- #4 wildcard DNS detection
- #5 Certificate Transparency lookup (crt.sh)
- #6 bundle a default wordlist
- #7 output formats: fill in real text / JSON bodies
- #8 GitHub Actions: lint + test workflow
