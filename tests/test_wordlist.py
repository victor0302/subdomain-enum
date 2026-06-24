from subdomain_enum import wordlist


def test_default_wordlist_loads():
    words = wordlist.load()
    assert len(words) > 500
    assert "www" in words
    assert "admin" in words
    assert "api" in words


def test_default_wordlist_no_comments_or_blanks():
    words = wordlist.load()
    assert all(w for w in words)
    assert all(not w.startswith("#") for w in words)


def test_custom_wordlist(tmp_path):
    f = tmp_path / "words.txt"
    f.write_text("# header\nfoo\nbar\n\n# trailing\nbaz\n")
    assert wordlist.load(f) == ["foo", "bar", "baz"]


def test_missing_wordlist_raises(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        wordlist.load(tmp_path / "nope.txt")


def test_default_path_exists():
    assert wordlist.default_path().exists()
