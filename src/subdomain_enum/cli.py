from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import wordlist as wordlist_module

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
    return parser


def _emit(findings: list[str], output: str) -> str:
    if output == "json":
        return json.dumps({"subdomains": findings}, indent=2)
    if not findings:
        return "No subdomains found."
    return "\n".join(findings)


def run_enum(domain: str, wordlist: str | None, _concurrency: int,
             _timeout: float, output: str, _sources: str) -> int:
    if not domain:
        print("error: domain is required", file=sys.stderr)
        return 2
    try:
        words = wordlist_module.load(Path(wordlist) if wordlist else None)
    except FileNotFoundError as exc:
        print(f"error: wordlist not found: {exc}", file=sys.stderr)
        return 2
    source = wordlist or "bundled default"
    print(f"loaded {len(words)} words from {source}", file=sys.stderr)
    findings: list[str] = []
    print(_emit(findings, output))
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
        )
    return 2


if __name__ == "__main__":
    sys.exit(main())
