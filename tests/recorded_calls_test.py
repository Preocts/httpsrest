"""VCR recorded API calls to test module behavior"""
import ssl
from http.client import HTTPSConnection
from typing import Generator
from unittest.mock import patch

import pytest
from httpsrest import HttpsRest

from tests.localrest import MockServer

MOCK_SSL_FILE = "tests/fixtures/mock_server.pem"


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


@pytest.fixture(scope="function", name="base_client")
def fixture_base_client(
    mock_httpsconn: HTTPSConnection,
) -> Generator[HttpsRest, None, None]:
    """Yields a default init'ed class instance pointed to localhost"""
    client = HttpsRest("localhost")
    with patch.object(client, "_client", mock_httpsconn):
        yield client


def test_valid_get(base_client: HttpsRest) -> None:
    """GET test"""
    base_client.set_timeout(1)
    result = base_client.get("/my/path")
    assert result == 200
