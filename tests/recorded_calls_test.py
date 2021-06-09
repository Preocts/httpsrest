"""VCR recorded API calls to test module behavior"""
import ssl
from http.client import HTTPSConnection
from typing import Generator
from unittest.mock import patch

import pytest
import vcr
from httpsrest import HttpsRest
from httpsrest import HttpsResult

from tests.localrest import MockServer

RERECORD_ON_RUN = True

MOCK_SSL_FILE = "tests/fixtures/mock_server.pem"
CASSETTE_FILE = "tests/fixtures/cassettes/playback.yaml"

vcr_record = vcr.VCR(
    serializer="yaml",
    cassette_library_dir="tests/fixtures/cassettes",
    record_mode="once",
    match_on=["uri", "method"],
    ignore_localhost=False,
)


@pytest.fixture(scope="session", name="mock_server")
def fixture_mock_server() -> Generator[MockServer, None, None]:
    """Yields a local server daemon"""
    server = MockServer()
    server.start_daemon()
    yield server


@pytest.fixture(scope="function", name="mock_httpsconn")
def fixture_mock_httpsconn(
    mock_server: MockServer,
) -> Generator[HTTPSConnection, None, None]:
    """Create a SSL contect connection object"""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    context.load_cert_chain(certfile=MOCK_SSL_FILE, password=MOCK_SSL_FILE)
    httpsconn = HTTPSConnection(
        host="localhost",
        port=mock_server.port,
        context=context,
        timeout=10,
    )
    yield httpsconn


# @vcr_record.use_cassette(CASSETTE_FILE)
@pytest.fixture(scope="function", name="base_client")
def fixture_base_client(
    mock_httpsconn: HTTPSConnection,
) -> Generator[HttpsRest, None, None]:
    """Yields a default init'ed class instance pointed to localhost"""
    client = HttpsRest("localhost")
    with patch.object(client, "_client", mock_httpsconn):
        yield client


@pytest.mark.parametrize(
    ("method", "route", "status"),
    (
        ("get", "/200", 200),
        ("get", "/401", 401),
    ),
)
def test_valid_get(
    base_client: HttpsRest, method: str, route: str, status: int
) -> None:
    """Method tests"""
    base_client.set_timeout(1)
    attrib = getattr(base_client, method)
    result: HttpsResult = attrib(route)
    assert result.status == status
    assert result.json and result.body
    assert isinstance(result.json, dict)


# ctx = ssl.create_default_context()
# ctx.check_hostname = False
# ctx.verify_mode = ssl.CERT_NONE
# [12:06 PM]
# try adding this
# [12:06 PM]
# also, add context = ctx in urlopen
