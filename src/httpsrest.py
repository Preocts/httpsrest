"""
HTTPS REST API Handler

Author: Preocts <preocts@preocts.com>
Repo: https/github.com/Preocts/httpsrest
"""
import json
import logging
from http.client import CannotSendRequest
from http.client import HTTPException
from http.client import HTTPResponse
from http.client import HTTPSConnection
from http.client import RemoteDisconnected
from typing import Any
from typing import Dict
from typing import MutableSet
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from urllib import parse

TIMEOUT_DEFAULT = 30
THROTTLE_TIMEOUT_DEFAULT = 60
MAX_RETRIES_DEFAULT = 3
RETRY_ON_DEFAULT = {401, 402, 403, 408, 429, 500, 502, 503, 504}
ENCODE_URL_DEFAULT = True
USE_URLENCODE_DEFAULT = False


class HttpsResult(NamedTuple):
    """Data structure for returned results of HTTPS call"""

    json: Dict[str, Any] = {}
    body: str = ""
    retry_count: int = 0
    status: int = 0


class HttpsRestConfig:
    """Dataclass structure for configuration values"""

    def __init__(self) -> None:
        """Define defaults"""
        self.connection_timeout: int = TIMEOUT_DEFAULT
        self.throttle_timeout: int = THROTTLE_TIMEOUT_DEFAULT
        self.max_retries: int = MAX_RETRIES_DEFAULT
        self.retry_on: MutableSet[int] = RETRY_ON_DEFAULT
        self.encode_url: bool = ENCODE_URL_DEFAULT
        self.use_urlencode: bool = USE_URLENCODE_DEFAULT
        self.port: int = 443


class HttpsRest:
    """Simple REST calls to APIs"""

    logger = logging.getLogger(__name__)

    def __init__(self, url: str, base_route: str = "") -> None:
        """url should be domain level only. No routes, no HTTPS://"""
        self._client: Optional[HTTPSConnection] = None
        self._url = self._parse_url(url)
        self._base_route = ""
        self._config = HttpsRestConfig()
        self.set_base_route(base_route)

    @property
    def url(self) -> str:
        """Base url class will use. To update, create new instance"""
        return self._url

    @property
    def base_route(self) -> str:
        """Base route appended to all API calls"""
        return self._base_route

    @property
    def port(self) -> int:
        """Returns port being used. Defaults to 443"""
        return self._config.port

    @property
    def timeout(self) -> int:
        """Time, in seconds, a connection will wait before timing out"""
        return self._config.connection_timeout

    @property
    def throttle_timeout(self) -> int:
        """Time, in seconds, a connection will pause if throttled before continuing"""
        return self._config.throttle_timeout

    @property
    def max_retries(self) -> int:
        """Number of retries that will be attempted before giving up"""
        return self._config.max_retries

    @property
    def encode_url(self) -> bool:
        """If true, all urls are encoded prior to sending"""
        return self._config.encode_url

    @property
    def use_urlencode(self) -> bool:
        """If true, json payloads are translated to URL parameters"""
        return self._config.use_urlencode

    @property
    def retry_on(self) -> Tuple[int, ...]:
        """Returns a tuple of HTTP status codes that will trigger a retry"""
        return tuple(self._config.retry_on)

    def set_port(self, port: int) -> None:
        """Sets port to be used"""
        self._parse_no_negative_int(port)
        self._config.port = port if (port > 1) and (port < 65535) else 443

    def set_timeout(self, seconds: int = TIMEOUT_DEFAULT) -> None:
        """Set the time, in seconds, a connection will wait before timing out"""
        self._config.connection_timeout = self._parse_no_negative_int(seconds)

    def set_throttle_timeout(self, seconds: int = THROTTLE_TIMEOUT_DEFAULT) -> None:
        """Time, in seconds, a connection will pause if throttled before continuing"""
        self._config.throttle_timeout = self._parse_no_negative_int(seconds)

    def set_max_retries(self, count: int = MAX_RETRIES_DEFAULT) -> None:
        """Set the number of retries that will be attempted before giving up"""
        self._config.max_retries = self._parse_no_negative_int(count)

    def set_encode_url(self, encode_url: bool = ENCODE_URL_DEFAULT) -> None:
        """If true, all urls will be encoded prior to sending"""
        self._config.encode_url = bool(encode_url)

    def set_use_urlencode(self, use_urlencode: bool = USE_URLENCODE_DEFAULT) -> None:
        """If true, json payloads are translated to URL parameters"""
        self._config.use_urlencode = bool(use_urlencode)

    def set_retry_on_codes(self, *args: int) -> None:
        """Adds given response codes to set that trigger a retry attemp"""
        for code in args:
            self._config.retry_on.add(code)

    def remove_retry_on_codes(self, *args: int) -> None:
        """Removes given response codes from set that trigger a retry attemp"""
        for code in args:
            self._config.retry_on.discard(code)

    def set_base_route(self, base_route: str) -> str:
        """Set the default route for all calls. Returns stored value."""
        if base_route:
            prefix = "/" if not base_route.startswith("/") else ""
            post_strip = "/" if base_route.endswith("/") else ""
            self._base_route = f"{prefix}{base_route.rstrip(post_strip)}"
        else:
            self._base_route = ""
        return self.base_route

    def format_payload(self, payload: Dict[str, Any]) -> str:
        """Formats paylaod into string"""
        if self._config.use_urlencode:
            return parse.urlencode(payload, doseq=True)
        return json.dumps(payload)

    def format_route(self, route: str) -> str:
        """Formats route, encoding if needed and pre-fixing base_route"""
        if route.startswith("/"):
            combined_route = "".join([self._base_route, route])
        else:
            combined_route = "/".join([self.base_route, route])
        if self._config.encode_url:
            return parse.quote(combined_route, safe="/?=&")
        return combined_route

    def _parse_no_negative_int(self, value: int, default: int = 0) -> int:
        """Returns value or default if value is less than 0"""
        if isinstance(value, int):
            return value if value > default else default
        else:
            raise ValueError("Expected int, got %s", type(value))

    def _parse_url(self, url: str) -> str:
        """Cleans url string, raises if route or query is included"""
        cleaned_url = url.lower().replace("https://", "").replace("http://", "")

        if "/" in cleaned_url:
            self.logger.error("Route in url: %s", cleaned_url)
            raise Exception("Do not include /routes in base url, use .set_base_route()")
        if "?" in cleaned_url:
            self.logger.error("Possible ? parameters in url: %s", cleaned_url)
            raise Exception("Remove URI parameters from base url.")

        return cleaned_url

    def _connect(self) -> None:
        """Opens the connection. Not usually needed to be called directly"""
        try:
            self._client = HTTPSConnection(
                host=self.url,
                port=self.port,
                timeout=self.timeout,
            )
        except HTTPException as err:
            self.logger.error("Connect attempt failed: %s", err)

    def get(self, route: str) -> HttpsResult:
        """Send a GET request"""
        if self._client is None:
            self._connect()
        return self._handle_request("GET", route, None)

    def _handle_request(
        self, method: str, route: str, payload: Optional[str]
    ) -> HttpsResult:
        """Send the HTTPS request and process response"""
        if self._client is None:
            raise Exception("Unexpected call of handle_requests with no client")

        try:
            self._client.request(method.upper(), route, payload, headers={})
            result = self._parse_response(self._client.getresponse())

        except (RemoteDisconnected, CannotSendRequest) as err:
            self.logger.error("Unable to send to remote: '%s'", err)
            result = HttpsResult(status=900)
        except (ConnectionError, TimeoutError) as err:
            self.logger.error("Connection error: '%s'", err)
            result = HttpsResult(status=901)

        return result

    def _parse_response(self, response: HTTPResponse) -> HttpsResult:
        """Parse the response of a HTTPSConnection reqeust"""
        str_body = response.read().decode(encoding="utf-8")
        try:
            json_response = json.loads(str_body)
        except json.JSONDecodeError:
            json_response = {}

        return HttpsResult(
            json=json_response,
            body=str_body,
            retry_count=0,
            status=response.status,
        )
