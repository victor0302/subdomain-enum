from subdomain_enum import __version__
from subdomain_enum.cli import build_parser, main


def test_version():
    assert __version__ == "0.1.0"


def test_parser_accepts_domain():
    args = build_parser().parse_args(["example.com"])
    assert args.domain == "example.com"


def test_main_returns_zero(capsys):
    rc = main(["example.com"])
    assert rc == 0
    assert "subdomain-enum" in capsys.readouterr().out
