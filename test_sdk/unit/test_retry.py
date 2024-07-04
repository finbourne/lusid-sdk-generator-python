from unittest import mock
from TO_BE_REPLACED.extensions.retry import RetryingRestWrapper, RetryingRestWrapperAsync
from TO_BE_REPLACED.extensions.rest import RESTClientObject
from TO_BE_REPLACED.rest import RESTClientObject as AsyncRestClientObject
from TO_BE_REPLACED.configuration import Configuration
from TO_BE_REPLACED import ApiException
from TO_BE_REPLACED.rest import RESTResponse
import pytest


class TestSyncRetryRestWrapper():
    def test_on_success_returns_result_and_makes_request_once(self):
        rest_object_mock = RESTClientObject(Configuration())
        rest_object_mock.request = mock.MagicMock(return_value="OK")
        retry_object = RetryingRestWrapper(rest_object=rest_object_mock)
        result = retry_object.request("GET", "")
        assert result == "OK"
        rest_object_mock.request.assert_called_once_with('GET', '', None, None, None, None, True, None)

    def test_on_failure_retries_once(self):
        rest_object_mock = RESTClientObject(Configuration())
        http_resp = RESTResponse(resp=mock.MagicMock(), data=None)
        http_resp.getheaders = mock.MagicMock(return_value={"Retry-After": 1})
        rest_object_mock.request = mock.MagicMock(side_effect=[ApiException(http_resp=http_resp), "OK"])
        retry_object = RetryingRestWrapper(rest_object=rest_object_mock, retries=1)
        result = retry_object.request("GET", "")
        assert result == "OK"
        rest_object_mock.request.assert_called_with('GET', '', None, None, None, None, True, None)
        assert rest_object_mock.request.call_count == 2

    def test_on_repeated_failures_throws_ApiException(self):
        rest_object_mock = RESTClientObject(Configuration())
        http_resp = RESTResponse(resp=mock.MagicMock(), data=None)
        http_resp.getheaders = mock.MagicMock(return_value={"Retry-After": 1})
        api_exception = ApiException(http_resp=http_resp)
        rest_object_mock.request = mock.MagicMock(side_effect=[api_exception, api_exception])
        retry_object = RetryingRestWrapper(rest_object=rest_object_mock, retries=1)
        with pytest.raises(ApiException):
            result = retry_object.request("GET", "")
            assert result == "OK"
            assert rest_object_mock.request.call_count == 2


@pytest.mark.asyncio
class TestASyncRetryRestWrapper():
    async def test_on_success_returns_result_and_makes_request_once(self):
        rest_object_mock = AsyncRestClientObject(Configuration())
        rest_object_mock.request = mock.AsyncMock(return_value="OK")
        retry_object = RetryingRestWrapperAsync(rest_object=rest_object_mock)
        result = await retry_object.request("GET", "")
        assert result == "OK"
        rest_object_mock.request.assert_called_once_with('GET', '', None, None, None, None, True, None)
        await rest_object_mock.close()

    async def test_on_failure_retries_once(self):
        rest_object_mock = AsyncRestClientObject(Configuration())
        http_resp = RESTResponse(resp=mock.MagicMock(), data=None)
        http_resp.getheaders = mock.MagicMock(return_value={"Retry-After": 1})
        rest_object_mock.request = mock.AsyncMock(side_effect=[ApiException(http_resp=http_resp), "OK"])
        retry_object = RetryingRestWrapperAsync(rest_object=rest_object_mock, retries=1)
        result = await retry_object.request("GET", "")
        assert result == "OK"
        rest_object_mock.request.assert_called_with('GET', '', None, None, None, None, True, None)
        assert rest_object_mock.request.call_count == 2
        await rest_object_mock.close()

    async def test_on_repeated_failures_throws_ApiException(self):
        rest_object_mock = AsyncRestClientObject(Configuration())
        http_resp = RESTResponse(resp=mock.MagicMock(), data=None)
        http_resp.getheaders = mock.MagicMock(return_value={"Retry-After": 1})
        api_exception = ApiException(http_resp=http_resp)
        rest_object_mock.request = mock.AsyncMock(side_effect=[api_exception, api_exception])
        retry_object = RetryingRestWrapperAsync(rest_object=rest_object_mock, retries=1)
        with pytest.raises(ApiException):
            result = await retry_object.request("GET", "")
            assert result == "OK"
            assert rest_object_mock.request.call_count == 2
        await rest_object_mock.close()
