from unittest.mock import AsyncMock, MagicMock
import aiohttp
import lusid.extensions.rest
import lusid.rest
import pytest
import urllib3


class TestAsyncRest:
    @pytest.mark.asyncio
    async def test_request_with_plaintext_content_type_calls_req_with_str_data_param(
        self,
    ):
        rest_client = lusid.rest.RESTClientObject(lusid.Configuration.get_default())
        rest_client.pool_manager = AsyncMock(aiohttp.ClientSession)
        expected_response = "response"
        rest_client.pool_manager.request = AsyncMock(return_value=expected_response)
        print(rest_client.pool_manager.request)
        headers = {"Content-Type": "text/plain"}
        message = "hello world"
        response = await rest_client.request(
            "PUT",
            "www.example.com",
            headers=headers,
            body=message,
            _preload_content=False,
        )
        assert expected_response == response
    
    @pytest.mark.asyncio
    async def test_async_api_client_content_length(self):
        rest_client = lusid.rest.RESTClientObject(lusid.Configuration.get_default())
        rest_client.pool_manager = AsyncMock(aiohttp.ClientSession)

        expected_response = {"Content-Type": "text/plain", "Content-Length":"17", "version": "2.45"}

        rest_client.pool_manager.request = AsyncMock(return_value=expected_response)
        headers = {"Content-Type": "text/plain", "Content-Length":17, "version": 2.45}
        message = "hello world"
        response = await rest_client.request(
            "POST",
            "https://www.lusid.com/api",
            headers=headers,
            body=message,
            _preload_content=False,
        )
        assert expected_response == response


class TestSyncRest:
    def test_request_with_plaintext_content_type_calls_req_with_str_data_param(self):
        rest_client = lusid.extensions.rest.RESTClientObject(
            lusid.Configuration.get_default()
        )
        rest_client.pool_manager = MagicMock(aiohttp.ClientSession)
        expected_response = urllib3.response.HTTPResponse(body="response", status=200)
        rest_client.pool_manager.request = MagicMock(return_value=expected_response)
        print(rest_client.pool_manager.request)
        # rest_client.pool_manager.request = mock_response
        headers = {"Content-Type": "text/plain"}
        message = "hello world"
        response = rest_client.request(
            "PUT",
            "www.example.com",
            headers=headers,
            body=message,
            _preload_content=False,
        )
        assert expected_response == response

    def test_sync_client_content_length(self):
        rest_client = lusid.extensions.rest.RESTClientObject(
            lusid.Configuration.get_default()
        )
        rest_client.pool_manager = MagicMock(aiohttp.ClientSession)
        expected_headers = {"Content-Type": "text/plain", "Content-Length":"17", "version": "2.45"}
        expected_response = urllib3.response.HTTPResponse(headers=expected_headers)
        rest_client.pool_manager.request = MagicMock(return_value=expected_response)


        headers = {"Content-Type": "text/plain", "Content-Length":17, "version": 2.45}
        message = "hello world"
        response = rest_client.pool_manager.request(
            "POST",
            "https://www.lusid.com/api",
            headers=headers,
            body=message,
            _preload_content=False,
        )
        assert expected_response == response