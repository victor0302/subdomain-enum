import json

from subdomain_enum.output import render_json, render_text
from subdomain_enum.sources import Finding


def _f(name, source="dns", addresses=()):
    return Finding(name=name, source=source, addresses=tuple(addresses))


def test_text_empty():
    assert render_text([]) == "No subdomains found."


def test_text_one_per_line_sorted():
    out = render_text([_f("z.example.com"), _f("a.example.com"), _f("m.example.com")])
    assert out == "a.example.com\nm.example.com\nz.example.com"


def test_text_with_ips():
    out = render_text(
        [_f("a.example.com", addresses=("1.2.3.4", "::1"))],
        with_ips=True,
    )
    assert "a.example.com" in out
    assert "1.2.3.4" in out
    assert "::1" in out


def test_text_with_ips_handles_empty_addresses():
    out = render_text([_f("a.example.com", addresses=())], with_ips=True)
    assert "a.example.com" in out
    assert "no addresses" in out


def test_json_array_sorted_with_schema():
    findings = [
        _f("z.example.com", source="ct"),
        _f("a.example.com", source="dns", addresses=("1.2.3.4",)),
    ]
    payload = json.loads(render_json(findings))
    assert payload == [
        {"subdomain": "a.example.com", "ips": ["1.2.3.4"], "source": "dns"},
        {"subdomain": "z.example.com", "ips": [], "source": "ct"},
    ]
