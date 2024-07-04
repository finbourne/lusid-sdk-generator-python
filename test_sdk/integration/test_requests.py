from __future__ import annotations
import http.server
import TO_BE_REPLACED.configuration
import pytest
import threading
from TO_BE_REPLACED import ApiClient
import typing


class HttpRequestRecorder(typing.NamedTuple):
    handler: type[http.server.BaseHTTPRequestHandler]
    requests: typing.List[str]


@pytest.fixture
def mock_http_request_handler() -> HttpRequestRecorder:

    requests = []

    class TextHttpRequestHandler(http.server.BaseHTTPRequestHandler):

        def do_PUT(self) -> None:
            content_len = int(self.headers["Content-Length"])
            request_body = self.rfile.read(content_len).decode()
            requests.append(request_body)
            self.send_response(200)
            self.end_headers()

    return HttpRequestRecorder(TextHttpRequestHandler, requests)


@pytest.fixture
def mock_server(
    mock_http_request_handler,
) -> typing.Generator[typing.List[str], None, None]:
    httpd = http.server.HTTPServer(("", 8000), mock_http_request_handler.handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()
    yield mock_http_request_handler.requests
    httpd.shutdown()
    thread.join()


@pytest.mark.asyncio
async def test_async_client_can_send_requests_with_plain_text_bodies(
    mock_server: typing.List[str],
) -> None:
    api_client = TO_BE_REPLACED.ApiClient()
    headers = {"Content-Type": "text/plain"}
    message = "hello world"
    await api_client.request(
        "PUT", "http://localhost:8000", body=message, headers=headers
    )
    assert message == mock_server.pop()
