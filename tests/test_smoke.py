import json

import pytest

from subdomain_enum import __version__
from subdomain_enum.cli import build_parser, main


def test_version():
    assert __version__ == "0.1.0"


def test_parser_requires_subcommand():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parser_enum_defaults():
    args = build_parser().parse_args(["enum", "example.com"])
    assert args.command == "enum"
    assert args.domain == "example.com"
    assert args.concurrency == 50
    assert args.timeout == 3.0
    assert args.output == "text"
    assert args.sources == "all"


def test_parser_enum_overrides():
    args = build_parser().parse_args([
        "enum", "example.com",
        "-w", "words.txt",
        "--concurrency", "100",
        "--timeout", "1.5",
        "--output", "json",
        "--sources", "ct",
    ])
    assert args.wordlist == "words.txt"
    assert args.concurrency == 100
    assert args.timeout == 1.5
    assert args.output == "json"
    assert args.sources == "ct"


def test_dns_only_with_no_wordlist_yields_empty(capsys):
    rc = main(["enum", "example.com", "--sources", "dns"])
    assert rc == 0
    out = capsys.readouterr()
    assert "No subdomains found." in out.out
    assert "no wordlist" in out.err.lower()


def test_dns_only_no_wordlist_json(capsys):
    rc = main(["enum", "example.com", "--sources", "dns", "--output", "json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == []
