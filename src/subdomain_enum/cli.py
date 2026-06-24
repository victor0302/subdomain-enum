from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from . import wildcard
from .output import render_json, render_text
from .sources import Finding, dns_brute
from .sources import crtsh as crtsh_source
from .sources.crtsh import merge

OUTPUT_CHOICES: tuple[str, ...] = ("text", "json")
SOURCE_CHOICES: tuple[str, ...] = ("dns", "ct", "all")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subdomain-enum",
        description="Enumerate subdomains for a given domain.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    enum = subparsers.add_parser("enum", help="Enumerate subdomains for DOMAIN.")
    enum.add_argument("domain", help="Target domain (e.g. example.com).")
    enum.add_argument("-w", "--wordlist", help="Path to a wordlist file.")
    enum.add_argument("--concurrency", type=int, default=50, help="Max in-flight queries.")
    enum.add_argument("--timeout", type=float, default=3.0, help="Per-query timeout in seconds.")
    enum.add_argument("--output", choices=OUTPUT_CHOICES, default="text")
    enum.add_argument("--sources", choices=SOURCE_CHOICES, default="all")
    enum.add_argument(
        "--with-ips",
        action="store_true",
        help="Include resolved IPs in text output.",
    )
    enum.add_argument(
        "--no-wildcard-suppress",
        action="store_true",
        help="Skip wildcard detection / suppression.",
    )
    return parser


def _read_wordlist(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


async def _gather(
    domain: str,
    wordlist: list[str],
    concurrency: int,
    timeout: float,
    sources: str,
    suppress_wildcards: bool,
) -> list[Finding]:
    batches: list[list[Finding]] = []
    if sources in ("dns", "all") and wordlist:
        dns_findings = await dns_brute.bruteforce_collect(
            domain, wordlist, concurrency=concurrency, timeout=timeout
        )
        if suppress_wildcards:
            report = await wildcard.detect(domain, timeout=timeout)
            dns_findings = wildcard.suppress(dns_findings, report)
        batches.append(dns_findings)
    if sources in ("ct", "all"):
        try:
            ct_findings = list(crtsh_source.lookup(domain, timeout=max(timeout, 30.0)))
        except OSError as exc:
            print(f"warning: crt.sh lookup failed: {exc}", file=sys.stderr)
            ct_findings = []
        batches.append(ct_findings)
    return merge(*batches)


def run_enum(
    domain: str,
    wordlist_path: str | None,
    concurrency: int,
    timeout: float,
    output: str,
    sources: str,
    *,
    with_ips: bool,
    suppress_wildcards: bool,
) -> int:
    if not domain:
        print("error: domain is required", file=sys.stderr)
        return 2
    words: list[str] = []
    if wordlist_path:
        try:
            words = _read_wordlist(Path(wordlist_path))
        except FileNotFoundError as exc:
            print(f"error: wordlist not found: {exc}", file=sys.stderr)
            return 2

    if sources in ("dns", "all") and not words and sources != "ct":
        print(
            "warning: no wordlist provided; DNS bruteforce will be skipped",
            file=sys.stderr,
        )

    findings = asyncio.run(
        _gather(domain, words, concurrency, timeout, sources, suppress_wildcards)
    )

    if output == "json":
        print(render_json(findings))
    else:
        print(render_text(findings, with_ips=with_ips))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "enum":
        return run_enum(
            args.domain,
            args.wordlist,
            args.concurrency,
            args.timeout,
            args.output,
            args.sources,
            with_ips=args.with_ips,
            suppress_wildcards=not args.no_wildcard_suppress,
        )
    return 2


if __name__ == "__main__":
    sys.exit(main())
