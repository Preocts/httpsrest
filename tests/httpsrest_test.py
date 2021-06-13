"""Tests for httprest"""
from typing import Generator

import pytest
from httpsrest import HttpsRest

TEST_HEADERS = {
    "Content": "application/json",
    "Authorization": "bearer = ccc",
}


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
        ("backoff", 10, 10),
        ("backoff", -19, 0),
        ("backoff", 0, 0),
        ("backoff", "foo", -1),
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
        ("port", 80, 80),
        ("port", -19, 443),
        ("port", 0, 443),
        ("port", 65536, 443),
        ("port", "foo", -1),
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


def test_format_payload(base_client: HttpsRest) -> None:
    """Two variants available"""
    payload = {"sample": "test value", "values": None}
    expected_default = '{"sample": "test value", "values": null}'
    expected_urlencoded = "sample=test+value&values=None"

    assert base_client.format_payload(payload) == expected_default

    base_client.set_use_urlencode(True)

    assert base_client.format_payload(payload) == expected_urlencoded


@pytest.mark.parametrize(
    ("encode", "in_", "out"),
    (
        (False, "api/members?test=my test", "/api/members?test=my test"),
        (False, "/api/members?test=my test", "/api/members?test=my test"),
        (True, "api/members?test=my test", "/api/members?test=my%20test"),
        (True, "/api/members?test=my test", "/api/members?test=my%20test"),
    ),
)
def test_format_route_encoding(
    base_client: HttpsRest, encode: bool, in_: str, out: str
) -> None:
    """Test formatting the route with encoding and without"""
    base_client.set_encode_url(encode)
    result = base_client.format_route(in_)
    assert result == out


def test_set_headers(base_client: HttpsRest) -> None:
    """Set headers"""
    base_client.set_headers(TEST_HEADERS)

    assert base_client.headers == TEST_HEADERS

    with pytest.raises(ValueError):
        base_client.set_headers("Hello")  # type: ignore
