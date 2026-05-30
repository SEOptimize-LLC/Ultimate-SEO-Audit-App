"""Tests for text_loader.detect_body_column and load_page_text."""

import asyncio

import pandas as pd

from Skills.semantic_site_map.text_loader import (
    _clean_noise,
    detect_body_column,
    load_page_text,
)


def test_clean_noise_strips_bare_urls():
    raw = "Read more at https://example.com/foo about teachers"
    out = _clean_noise(raw)
    assert "https://example.com/foo" not in out
    assert "teachers" in out


def test_clean_noise_keeps_markdown_anchor_drops_target():
    raw = "Check [our blog](https://example.com/blog) for tips"
    out = _clean_noise(raw)
    assert "our blog" in out
    assert "example.com" not in out


def test_clean_noise_handles_multiple_urls_per_line():
    raw = "[A](https://x.com/a) and [B](https://x.com/b) and bare https://x.com/c"
    out = _clean_noise(raw)
    assert "A" in out and "B" in out
    assert "x.com" not in out


def test_build_text_strips_urls_from_body():
    import pandas as pd_local
    from Skills.semantic_site_map.text_loader import _build_text_from_sf

    df = pd_local.DataFrame({
        "url": ["https://x.com/a"],
        "title": ["Teacher Guide"],
        "Content": [
            "Body about teachers. [Home](https://x.com/) "
            "[Login](https://x.com/login) https://x.com/contact"
        ],
    })
    out = _build_text_from_sf(df, "Content")
    text = out["text"].iloc[0]
    assert "teachers" in text
    assert "Home" in text  # anchor preserved
    assert "x.com" not in text  # URL targets stripped


def test_detects_content_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "Content": ["body text"]})
    assert detect_body_column(df) == "Content"


def test_detects_body_text_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "Body Text": ["body text"]})
    assert detect_body_column(df) == "Body Text"


def test_detects_custom_extraction_column():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "Custom Extraction 1": ["body text"],
    })
    assert detect_body_column(df) == "Custom Extraction 1"


def test_returns_none_when_no_body_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "title": ["t"]})
    assert detect_body_column(df) is None


def test_ignores_empty_body_column():
    df = pd.DataFrame({"url": ["https://x.com/a"], "Content": [None]})
    assert detect_body_column(df) is None


def test_lowercase_column_match():
    df = pd.DataFrame({"url": ["https://x.com/a"], "content": ["body text"]})
    assert detect_body_column(df) == "content"


def test_load_page_text_uses_sf_column_when_present():
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "title": ["A", "B"],
        "meta_desc": ["da", "db"],
        "h1": ["H1a", "H1b"],
        "Content": ["body a", "body b"],
    })
    result = asyncio.run(load_page_text(df, cache_path=None))
    assert set(result["url"]) == {"https://x.com/a", "https://x.com/b"}
    assert "body a" in result.loc[result["url"] == "https://x.com/a", "text"].iloc[0]
    assert "body b" in result.loc[result["url"] == "https://x.com/b", "text"].iloc[0]


def test_load_page_text_combines_title_meta_h1_with_body():
    df = pd.DataFrame({
        "url": ["https://x.com/a"],
        "title": ["Title A"],
        "meta_desc": ["Meta A"],
        "h1": ["H1 A"],
        "Content": ["Body A"],
    })
    result = asyncio.run(load_page_text(df, cache_path=None))
    text = result["text"].iloc[0]
    assert "Title A" in text
    assert "Meta A" in text
    assert "H1 A" in text
    assert "Body A" in text


def test_load_page_text_filters_non_200():
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "title": ["A", "B"],
        "status_code": [200, 404],
        "Content": ["body a", "body b"],
    })
    result = asyncio.run(load_page_text(df, cache_path=None))
    assert list(result["url"]) == ["https://x.com/a"]


def test_load_page_text_filters_noindex():
    df = pd.DataFrame({
        "url": ["https://x.com/a", "https://x.com/b"],
        "title": ["A", "B"],
        "meta_robots": ["index,follow", "noindex,follow"],
        "Content": ["body a", "body b"],
    })
    result = asyncio.run(load_page_text(df, cache_path=None))
    assert list(result["url"]) == ["https://x.com/a"]
