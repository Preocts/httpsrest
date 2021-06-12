"""
HTTPS REST API Handler

Author: Preocts <preocts@preocts.com>
Repo: https/github.com/Preocts/httpsrest
"""
import json
import logging
import time
from http.client import HTTPException
from http.client import HTTPResponse
from http.client import HTTPSConnection
from typing import Any
from typing import Dict
from typing import MutableSet
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import TypedDict
from urllib import parse


class HttpsResult(NamedTuple):
    """Data structure for returned results of HTTPS call"""

    json: Dict[str, Any] = {}
    body: str = ""
    retry: bool = False
    attempts: int = 0
    status: int = 0


class _HttpsResult(TypedDict):
    """Private data class for passing mutable results to processes"""

    json: Dict[str, Any]
    body: str
    retry: bool
    attempts: int
    status: int


class HttpsRestConfig:
    """Dataclass structure for configuration values"""

    def __init__(self) -> None:
        """Define defaults"""
        self.sleep_base_time: int = 5
        self.connection_timeout: int = 30
        self.throttle_timeout: int = 60
        self.max_retries: int = 3
        self.retry_on: MutableSet[int] = {401, 402, 403, 408, 429, 500, 502, 503, 504}
        self.encode_url: bool = True
        self.use_urlencode: bool = False
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

    def set_timeout(self, seconds: int) -> None:
        """Set the time, in seconds, a connection will wait before timing out"""
        self._config.connection_timeout = self._parse_no_negative_int(seconds)

    def set_throttle_timeout(self, seconds: int) -> None:
        """Time, in seconds, a connection will pause if throttled before continuing"""
        self._config.throttle_timeout = self._parse_no_negative_int(seconds)

    def set_max_retries(self, count: int) -> None:
        """Set the number of retries that will be attempted before giving up"""
        self._config.max_retries = self._parse_no_negative_int(count)

    def set_encode_url(self, encode_url: bool) -> None:
        """If true, all urls will be encoded prior to sending"""
        self._config.encode_url = bool(encode_url)

    def set_use_urlencode(self, use_urlencode: bool) -> None:
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
            self.logger.debug("Route in url: %s", cleaned_url)
            raise Exception("Do not include /routes in base url, use .set_base_route()")
        if "?" in cleaned_url:
            self.logger.debug("Possible ? parameters in url: %s", cleaned_url)
            raise Exception("Remove URI parameters from base url.")

        return cleaned_url

    def _connect(self) -> HTTPSConnection:
        """Returns a connection. Not usually needed to be called directly"""
        return HTTPSConnection(host=self.url, port=self.port, timeout=self.timeout)

    def close(self) -> None:
        """Close any existing connection"""
        if self._client is not None:
            self._client = None

    def get(self, route: str) -> HttpsResult:
        """Send a GET request"""
        return self._handle_request("GET", route, None)

    def delete(self, route: str) -> HttpsResult:
        """Send a DELETE request"""
        return self._handle_request("DELETE", route, None)

    def post(self, route: str, payload: Dict[str, Any]) -> HttpsResult:
        """Send a POST request"""
        return self._handle_request("POST", route, self.format_payload(payload))

    def put(self, route: str, payload: Dict[str, Any]) -> HttpsResult:
        """Send a PUT request"""
        return self._handle_request("POST", route, self.format_payload(payload))

    def patch(self, route: str, payload: Dict[str, Any]) -> HttpsResult:
        """Send a PATCH request"""
        return self._handle_request("PATCH", route, self.format_payload(payload))

    def _handle_request(
        self, method: str, route: str, payload: Optional[str]
    ) -> HttpsResult:
        """Send the HTTPS request, process response, and handle retries"""
        result = self._build_response()  # Default empty response

        while result["retry"] and self.max_retries >= result["attempts"]:
            self._execute_sleep(result)

            response = self._get_reponse(method, route, payload)
            result["attempts"] += 1
            if response is not None:
                result["body"] = response.read().decode()
                result["json"] = self._parse_json_body(result["body"])
                result["status"] = response.status
                result["retry"] = self._needs_retry(result["status"])
            else:
                result["retry"] = True

        return HttpsResult(**result)

    def _get_reponse(
        self, method: str, route: str, payload: Optional[str]
    ) -> Optional[HTTPResponse]:
        """Send request, return response"""
        if self._client is None:
            self._client = self._connect()

        try:
            self._client.request(method.upper(), route, payload, headers={})
            return self._client.getresponse()

        except (
            HTTPException,
            ConnectionResetError,
            ConnectionError,
            TimeoutError,
        ) as err:
            self.logger.debug("Connection error: '%s'", err)
            self.close()  # Forces the connection to reset

        return None

    def _parse_json_body(self, body: str) -> Dict[str, Any]:
        """Parse the response of a HTTPSConnection reqeust"""
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def _needs_retry(self, status: int) -> bool:
        """Returns true if a retry is needed by status code"""
        return status in self._config.retry_on

    def _execute_sleep(self, result: _HttpsResult) -> None:
        """Runs sleep against a multiple of attempts"""
        time.sleep(self._config.sleep_base_time * result["attempts"])

    @staticmethod
    def _build_response() -> _HttpsResult:
        """Create private object"""
        return {"json": {}, "body": "", "retry": True, "attempts": 0, "status": 0}
