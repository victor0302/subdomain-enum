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

## 2026-06-20 — Issue #3: async DNS bruteforce

First real I/O. Adds `dnspython>=2.6` as a runtime dep. Lives in `src/subdomain_enum/sources/dns_brute.py`. The shared `Finding(name, source, addresses)` dataclass lands in `sources/__init__.py` — that's the type every source (DNS, CT, future ones) will yield.

- `bruteforce(domain, words, concurrency, timeout)` is an async generator
- `bruteforce_collect(...)` is a convenience wrapper for tests / non-streaming callers
- A single `asyncio.Semaphore` caps slots; inside each slot A and AAAA fan out in parallel — so the actual in-flight cap is `2 * concurrency`
- Per-query `lifetime` is the timeout passed in
- NXDOMAIN, NoAnswer, NoNameservers, dnspython `Timeout`, `asyncio.TimeoutError` — all swallowed cleanly; the word just doesn't produce a finding
- Wordlist lines are stripped before use; blank lines and `#`-prefixed comments are skipped

Decisions:
- **`dnspython` over `aiodns`.** dnspython's async API is a thin wrapper over the same resolver objects you'd use sync; one library covers both. aiodns is faster but tied to c-ares and has a harder error surface.
- **Semaphore counts "subdomain slots", not "queries".** Fanning A and AAAA inside one slot keeps the API simple — caller asks for `--concurrency 50` and gets 50 subdomains in flight, not 25.
- **Generator + collect helper instead of `return list[...]`.** Streaming lets a CLI print findings as they arrive; the helper keeps tests synchronous-feeling.
- **Strip blank / `#` lines in the parser, not in the consumer.** Wordlist files reliably have both; pushing the cleanup down means every caller doesn't have to remember.
- **Errors are swallowed, not logged.** On a 100k-word list, NXDOMAIN happens 99% of the time — it's not an error, it's the expected case. Real resolver failures (no nameservers) surface the same way, which is a known sharp edge — fine for now, can revisit once the CLI has a `--verbose` mode.

## 2026-06-20 — Issue #4: wildcard DNS detection

Lives in `src/subdomain_enum/wildcard.py` (not under `sources/` — it's not itself a source). Two functions: `detect()` produces a `WildcardReport(is_wildcard, addresses)`, and `suppress()` filters a list of findings against that report.

- `detect()` resolves `nonexistent-{uuid}.<domain>` several times (default 3 probes)
- Short-circuits to `is_wildcard=False` the first time any probe comes back empty
- Across the probes that *did* resolve, the union of IPs is captured as the wildcard set
- `suppress()` drops findings whose addresses are a *subset* of the wildcard IPs; keeps findings with partial / non-overlapping addresses

Decisions:
- **Multiple probes, not one.** A single probe can hit DNS cache or a transient route; three probes makes a wildcard much harder to miss.
- **Short-circuit on first negative.** If even one random label returns NXDOMAIN, this is not a wildcard domain — no point doing the other probes.
- **Suppress by subset, not by intersection.** A subdomain that happens to point at the wildcard IP *and* a unique IP is interesting (it's a real host that also happens to be in the wildcard catch-all). Only drop the ones that are *exclusively* wildcard IPs.
- **`detect()` accepts an injected resolver.** Tests don't need a network round-trip; production code creates its own. Same trick that made #3's tests painless.

## 2026-06-20 — Issue #5: crt.sh CT lookup

Second discovery source. Lives in `src/subdomain_enum/sources/crtsh.py`. Stdlib `urllib` only — no extra deps.

- `lookup(domain, timeout=30)` queries `https://crt.sh/?q=%25.<domain>&output=json` and returns `Finding(name, source="ct")` per unique entry
- `_parse(payload, domain)` does all the cleanup: splits `name_value` on newlines (one row can list several SANs), strips `*.` wildcards, lowercases, keeps only entries that match the apex or `.<domain>` suffix
- New `merge(*iterables)` helper de-dupes across sources, joins `source` fields (`"dns"` + `"ct"` → `"dns,ct"`), unions addresses, and returns the result sorted by name

Decisions:
- **Stdlib `urllib` instead of `httpx`/`requests`.** One HTTP call. Async isn't a win when it's a single I/O at the end of a pipeline; the deps cost outweighs the convenience.
- **30-second timeout.** crt.sh is famously slow on large domains. 3 seconds (the DNS default) is wrong here.
- **`merge` returns a sorted list.** Order needs to be stable for the JSON output (and for diffing reports) — sorting by name in the merge keeps that out of the formatter.
- **Source field is a comma-joined string, not a list.** Easier to format in text output, and trivially splittable on the consumer side. If we ever grow to >5 sources, a list/set is a small refactor.
- **Apex domain kept on purpose.** crt.sh often returns the bare `example.com` for SAN-style certs; dropping it would underreport.

## Open follow-ups (tracked as issues)

- #6 bundle a default wordlist
- #7 output formats: fill in real text / JSON bodies (and wire sources + wildcard suppression in)
- #8 GitHub Actions: lint + test workflow
