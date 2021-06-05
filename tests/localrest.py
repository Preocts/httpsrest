"""
Mocks a localhost webserver so we can record API calls

Requires a `server.pem` file to be generated. Do NOT commit this file

>>> openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
"""
import socket
import ssl
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Thread
from typing import Tuple

SSL_FILE = "tests/fixtures/mock_server.pem"


class MockHandler(BaseHTTPRequestHandler):
    """Mock HTTPRequestHandler"""

    def do_GET(self) -> None:
        """Process GET request"""
        exit_response: Tuple[str, int] = ("mock", 200)
        # route = self.requestline.split()[1]
        self.send_response(exit_response[1])
        self.end_headers()
        self.wfile.write(exit_response[0].encode())

    def do_POST(self) -> None:
        """Process POST request"""
        exit_response: Tuple[str, int] = ("mock", 200)
        # route = self.requestline.split()[1]
        self.send_response(exit_response[1])
        self.end_headers()
        self.wfile.write(exit_response[0].encode())


class MockServer:
    """Mock HTTPS server"""

    def __init__(self) -> None:
        self.address, self.port = MockServer.find_free_port()
        self.server = HTTPServer(("localhost", self.port), MockHandler)
        self.server.socket = ssl.wrap_socket(
            sock=self.server.socket,
            certfile=SSL_FILE,
            server_side=True,
            ssl_version=ssl.PROTOCOL_TLS,
        )

        self.thread = Thread(target=self.server.serve_forever)
        self.thread.setDaemon(True)

    @staticmethod
    def find_free_port() -> Tuple[str, int]:
        """Just watch out for the guards"""
        sock = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
        sock.bind(("localhost", 0))
        address, port = sock.getsockname()
        sock.close()
        return (address, port)

    def start_daemon(self) -> None:
        """Start server daemon"""
        self.thread.start()


if __name__ == "__main__":
    mock_api = MockServer()
    mock_api.start_daemon()
    print(mock_api.address, mock_api.port)

    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain(certfile=SSL_FILE, password=SSL_FILE)
    client = HTTPSConnection("localhost", mock_api.port, context=context)

    client.request(
        "GET",
        "",
        None,
        headers={"Auth": "rooHappy"},
    )

    response = client.getresponse()
    print(response.status)
    print(response.read().decode("utf-8"))
    print("*" * 79)
