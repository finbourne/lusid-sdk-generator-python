from TO_BE_REPLACED.extensions.api_client import SyncApiClient
from TO_BE_REPLACED.configuration import Configuration
from TO_BE_REPLACED.api_client import ApiClient as AsyncApiClient
import pytest
from unittest.mock import MagicMock, patch
from asyncio import Future


@pytest.mark.asyncio
async def test_async_api_client_encodes_query_params_correctly():
    config = Configuration(host="https://example.com")
    api_client = AsyncApiClient(config)
    query_param = ("1", "a+b c")
    expected_encoded_url = "https://example.com/path?1=a%2Bb%20c"
    mock_response = MagicMock()
    mock_response.status = "200"
    mock_request = Future()
    mock_request.set_result(mock_response)
    with patch.object(
        api_client, "request", return_value=mock_request
    ) as mock_request_function:
        # mock_request_function.return_value = AsyncMock()
        await api_client.call_api(
            "/path",
            "POST",
            query_params=[query_param],
            collection_formats=["multi"],
            _preload_content=False,
        )
        args, kwargs = mock_request_function.call_args
        print(args)
        assert expected_encoded_url == args[1]

def test_sync_api_client_encodes_query_params_correctly():
    config = Configuration(host="https://example.com")
    api_client = SyncApiClient(config)
    query_param = ("1", "a+b c")
    expected_encoded_url = "https://example.com/path?1=a%2Bb%20c"
    with patch.object(
        api_client, "request"
    ) as mock_request_function:
        mock_request_function.return_value.status = "200"
        # mock_request_function.return_value = AsyncMock()
        api_client.call_api(
            "/path",
            "POST",
            query_params=[query_param],
            collection_formats=["multi"],
            _preload_content=False,
        )
        args, kwargs = mock_request_function.call_args
        print(args)
        assert expected_encoded_url == args[1]
