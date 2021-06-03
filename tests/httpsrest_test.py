"""Tests for httprest"""
from typing import Generator

import pytest
from httpsrest import HttpsRest


@pytest.fixture(scope="function", name="base_client")
def fixture_base_client() -> Generator[HttpsRest, None, None]:
    """Yields a default init'ed class instance pointed to localhost"""
    client = HttpsRest("localhost")
    yield client


@pytest.mark.parametrize(
    ("url", "expected", "raised"),
    (
        ("https://example.com", "example.com", False),
        ("http://example.com", "example.com", False),
        ("example.com", "example.com", False),
        ("https://example.com/api/path", "", True),
        ("http://example.com/api/path", "", True),
        ("example.com?limit=100", "", True),
    ),
)
def test_url_parsing(url: str, expected: str, raised: bool) -> None:
    """Remove HTTPS:// and HTTP://"""
    if raised:
        with pytest.raises(Exception):
            client = HttpsRest(url)

    else:

        client = HttpsRest(url)
        assert client.url == expected


@pytest.mark.parametrize(
    ("base_route", "expected"),
    (
        ("api/path/", "/api/path"),
        ("/api/path/", "/api/path"),
        ("api/path", "/api/path"),
        ("/api/path", "/api/path"),
    ),
)
def test_set_base_route(base_client: HttpsRest, base_route: str, expected: str) -> None:
    """Setting base route of all API calls"""
    base_client.set_base_route(base_route)
    assert base_client.base_route == expected


@pytest.mark.parametrize(
    ("attrib", "set_", "get_"),
    (
        ("timeout", 10, 10),
        ("timeout", -19, 0),
        ("timeout", 0, 0),
        ("timeout", "foo", -1),
        ("throttle_timeout", 10, 10),
        ("throttle_timeout", -19, 0),
        ("throttle_timeout", 0, 0),
        ("throttle_timeout", "foo", -1),
        ("max_retries", 10, 10),
        ("max_retries", -19, 0),
        ("max_retries", 0, 0),
        ("max_retries", "foo", -1),
    ),
)
def test_get_set_config_ints(
    base_client: HttpsRest, attrib: str, set_: int, get_: int
) -> None:
    """Tests setters and getters for config items that are ints"""
    setter = getattr(base_client, f"set_{attrib}")
    if get_ >= 0:
        setter(set_)
        assert getattr(base_client, attrib) == get_
    else:
        with pytest.raises(ValueError):
            setter(set_)


@pytest.mark.parametrize(
    ("attrib", "set_", "get_"),
    (
        ("encode_url", True, True),
        ("encode_url", False, False),
        ("encode_url", 0, False),
        ("encode_url", "foo", True),
        ("use_urlencode", True, True),
        ("use_urlencode", False, False),
        ("use_urlencode", 0, False),
        ("use_urlencode", "foo", True),
    ),
)
def test_get_set_config_bool(
    base_client: HttpsRest, attrib: str, set_: bool, get_: bool
) -> None:
    """Tests setters and getters for config items that are bools"""
    setter = getattr(base_client, f"set_{attrib}")
    setter(set_)
    assert getattr(base_client, attrib) == get_


def test_retry_on_set_remove_get(base_client: HttpsRest) -> None:
    """Tests setter, getter, and remover for retry code set"""
    start_len = len(base_client.retry_on)
    base_client.set_retry_on_codes(1, 2, -3, 4)
    assert len(base_client.retry_on) == start_len + 4
    assert 4 in base_client.retry_on

    base_client.remove_retry_on_codes(1, 2, -3, 4)
    assert len(base_client.retry_on) == start_len
    assert 4 not in base_client.retry_on
