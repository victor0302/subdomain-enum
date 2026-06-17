import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subdomain-enum",
        description="Enumerate subdomains for a given domain.",
    )
    parser.add_argument("domain", nargs="?", help="Target domain (e.g. example.com).")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(f"subdomain-enum: scaffolding only; nothing to enumerate yet for {args.domain}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
