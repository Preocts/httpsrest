"""
Mocks a localhost webserver so we can record API calls

Requires a `server.pem` file to be generated. Do NOT commit this file

>>> openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
"""
import json
import socket
import ssl
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from threading import Thread
from typing import Tuple

SSL_FILE = "tests/fixtures/mock_server.pem"
DEFAULT_RETURN_BODY = json.dumps({"response": "Good"})
ERROR_RETURN_BODY = json.dumps({"response": "Not good"})


class MockHandler(BaseHTTPRequestHandler):
    """Mock HTTPRequestHandler"""

    def sendback_answer(self) -> None:
        return_code = int(self.requestline.split()[1].strip("/"))
        if return_code in range(200, 299):
            exit_response: Tuple[str, int] = (DEFAULT_RETURN_BODY, return_code)
        else:
            exit_response = (ERROR_RETURN_BODY, return_code)

        self.send_response(exit_response[1])
        self.end_headers()
        self.wfile.write(exit_response[0].encode())

    def do_GET(self) -> None:
        """Process GET request"""
        self.sendback_answer()

    def do_DELETE(self) -> None:
        """Process GET request"""
        self.sendback_answer()

    def do_POST(self) -> None:
        """Process POST request"""
        self.sendback_answer()

    def do_PUT(self) -> None:
        """Process PUT request"""
        self.sendback_answer()

    def do_PATCH(self) -> None:
        """Process PATCH request"""
        self.sendback_answer()


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
