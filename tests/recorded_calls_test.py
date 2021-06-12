"""VCR recorded API calls to test module behavior"""
import ssl
from http.client import HTTPSConnection
from typing import Generator
from unittest.mock import patch

import pytest
from httpsrest import HttpsRest
from httpsrest import HttpsResult

from tests.localrest import MockServer

RERECORD_ON_RUN = True

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

    client.close()


@pytest.mark.parametrize(("method"), (("put"), ("post"), ("patch")))
def test_methods_with_payloads(base_client: HttpsRest, method: str) -> None:
    """Method tests"""
    payload = {"sample": "testing"}
    route = "/200"
    expected = 200
    base_client.set_timeout(1)
    base_client.set_max_retries(1)
    attrib = getattr(base_client, method)
    result: HttpsResult = attrib(route, payload)

    assert result.status == expected
    assert result.json and result.body
    assert isinstance(result.json, dict)


@pytest.mark.parametrize(("method"), (("get"), ("delete")))
def test_valid_methods_without_payloads(base_client: HttpsRest, method: str) -> None:
    """Method tests"""
    route = "/200"
    expected = 200
    base_client.set_timeout(1)
    base_client.set_max_retries(1)
    attrib = getattr(base_client, method)
    result: HttpsResult = attrib(route)
    assert result.status == expected
    assert result.json and result.body
    assert isinstance(result.json, dict)


def test_retry_codes(base_client: HttpsRest) -> None:
    """Ensure retry"""
    route = "/" + str(base_client.retry_on[0])
    excepted = base_client.retry_on[0]
    base_client.set_timeout(1)
    base_client.set_max_retries(1)
    result = base_client.get(route)

    assert result.status == excepted
    assert result.attempts == 2


# ctx = ssl.create_default_context()
# ctx.check_hostname = False
# ctx.verify_mode = ssl.CERT_NONE
# [12:06 PM]
# try adding this
# [12:06 PM]
# also, add context = ctx in urlopen
