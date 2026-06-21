import io
import json
from unittest.mock import patch

from subdomain_enum.sources import Finding
from subdomain_enum.sources.crtsh import _parse, lookup, merge


def test_parse_dedupes_and_strips_wildcards():
    payload = json.dumps([
        {"name_value": "www.example.com\n*.example.com"},
        {"name_value": "api.example.com"},
        {"name_value": "Www.Example.com"},
        {"name_value": "unrelated.test"},
    ]).encode()
    names = _parse(payload, "example.com")
    assert names == ["api.example.com", "example.com", "www.example.com"]


def test_parse_keeps_apex_domain():
    payload = json.dumps([{"name_value": "example.com"}]).encode()
    assert _parse(payload, "example.com") == ["example.com"]


def test_lookup_returns_findings_with_source_ct():
    payload = json.dumps([{"name_value": "api.example.com\nwww.example.com"}]).encode()
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value = io.BytesIO(payload)
        findings = list(lookup("example.com", timeout=5))
    names = {f.name for f in findings}
    sources = {f.source for f in findings}
    assert names == {"api.example.com", "www.example.com"}
    assert sources == {"ct"}


def test_merge_dedupes_and_combines_sources():
    a = [Finding(name="www.example.com", source="dns", addresses=("1.2.3.4",))]
    b = [Finding(name="www.example.com", source="ct"),
         Finding(name="api.example.com", source="ct")]
    merged = merge(a, b)
    assert {f.name for f in merged} == {"www.example.com", "api.example.com"}
    www = next(f for f in merged if f.name == "www.example.com")
    assert "dns" in www.source and "ct" in www.source
    assert www.addresses == ("1.2.3.4",)


def test_merge_sorts_by_name():
    merged = merge([Finding(name="z.x.com", source="ct"), Finding(name="a.x.com", source="ct")])
    assert [f.name for f in merged] == ["a.x.com", "z.x.com"]
