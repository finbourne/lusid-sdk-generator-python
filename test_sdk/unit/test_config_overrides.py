from typing import Optional
import aiohttp
import pytest
import urllib3
import TO_BE_REPLACED
from TO_BE_REPLACED.api import TEST_API
from TO_BE_REPLACED.api_client import ApiClient
from TO_BE_REPLACED.configuration import Configuration, Timeouts
from TO_BE_REPLACED.exceptions import ApiException
from TO_BE_REPLACED.extensions.api_client import SyncApiClient
from TO_BE_REPLACED.extensions.api_client_factory import ApiClientFactory, SyncApiClientFactory
from TO_BE_REPLACED.extensions.configuration_loaders import ArgsConfigurationLoader
from TO_BE_REPLACED.extensions.configuration_options import ConfigurationOptions

class MockPoolManager:
    def __init__(self, return_status_code: int = 200):
        self.timeouts = []
        self.callCount = 0
        self.return_status_code = return_status_code
    
    def request(self, method, url, **kwargs):
        self.callCount += 1
        if "timeout" in kwargs:
            self.timeouts.append(kwargs["timeout"])
        return MockResponse(self.return_status_code)
    
    async def close(self):
        ...
        
class MockResponse:
    def __init__(self, status_code: int):
        self.status = status_code
        self.reason = "test"
        self.data = "test".encode('utf-8')
        self.headers = {"Retry-After":0}
        
    def getheader(self, header: str):
        if header == "Retry-After":
            return 0
        return None
    
    def getheaders(self):
        return self.headers
    
    async def read(self):
        return self.data

    def __await__(self):
        async def closure():
            return self
        return closure().__await__()


# contains tests that are common to both async and sync api clients, whether created manually or with an api client factory
class BaseTests:
    
    def _override_deserialize(_, __):
        return ""
    
    async def _run_timeout_test(
        self,
        create_api_client_with_factory: bool,
        async_req: Optional[bool],
        is_async: bool,
        configuration_timeouts: Timeouts,
        factory_opts: ConfigurationOptions,
        request_timeout,
        request_opts: ConfigurationOptions,
        expected_total_timeout: Optional[float],
        expected_connect_timeout: Optional[float],
        expected_read_timeout: Optional[float]
    ):
        mock_pool_manager = MockPoolManager()
        if create_api_client_with_factory:
            api = self._create_api_instance_with_factory(
                is_async=is_async, 
                rate_limit_retries_config=None,
                configuration_timeouts=configuration_timeouts, 
                opts=factory_opts, 
                mock_pool_manager=mock_pool_manager)
        else:
            api = self._create_api_instance_without_factory(is_async, configuration_timeouts, mock_pool_manager)
        
        # to avoid having to return data that can be deserialised into real types
        # (which will vary from api to api and can change over time)
        # override the deserialize method
        api.api_client.deserialize = BaseTests._override_deserialize
        
        try:
            result = api.TEST_METHOD
                _request_timeout=request_timeout,
                async_req=async_req,
                opts=request_opts)
        finally:
            if is_async:
                await api.api_client.close()
            else:
                api.api_client.close()
        
        if async_req:
            result = result.get(timeout=60)
        
        if is_async:
            await result
        
        assert mock_pool_manager.callCount == 1
        assert len(mock_pool_manager.timeouts) == 1
        timeout = mock_pool_manager.timeouts[0]
        
        if is_async:
            # the timeout is of type aiohttp.ClientTimeout
            assert timeout.total == expected_total_timeout
            assert timeout.connect == expected_connect_timeout
            assert timeout.sock_read == expected_read_timeout
        else:
            # the timeout is of type urllib3.Timeout
            assert timeout.total == expected_total_timeout
            assert timeout._connect == expected_connect_timeout
            assert timeout._read == expected_read_timeout

    def _create_api_instance_without_factory(
        self,
        is_async: bool,
        configuration_timeouts: Timeouts,
        mock_pool_manager: MockPoolManager,
    ):
        configuration = Configuration(access_token="token", host="http://localhost", timeouts=configuration_timeouts)
        api_client_type = ApiClient if is_async else SyncApiClient
        api_client = api_client_type(configuration=configuration)
        api_client.rest_client.pool_manager = mock_pool_manager
        return TEST_API(api_client)

    def _create_api_instance_with_factory(
        self,
        is_async: bool,
        rate_limit_retries_config: Optional[int],
        configuration_timeouts: Timeouts,
        opts: ConfigurationOptions,
        mock_pool_manager: MockPoolManager,
    ):
        configuration_loader = ArgsConfigurationLoader(
            access_token="token", 
            api_url="http://localhost",
            total_timeout_ms=configuration_timeouts.total_timeout_ms,
            connect_timeout_ms=configuration_timeouts.connect_timeout_ms,
            read_timeout_ms=configuration_timeouts.read_timeout_ms,
            rate_limit_retries=rate_limit_retries_config
        )
        api_client_factory_type = ApiClientFactory if is_async else SyncApiClientFactory
        api_client_factory = api_client_factory_type(
            config_loaders=[configuration_loader], 
            opts=opts
        )
        api = api_client_factory.build(TEST_API)
        api.api_client.rest_client.rest_object.pool_manager = mock_pool_manager
        return api

    async def test_timeout_when_set_on_request_timeout_via_int(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(3000, 2000, 1000),
            factory_opts=None,
            request_timeout=10,
            request_opts=None,
            expected_total_timeout=10,
            expected_connect_timeout=2,
            expected_read_timeout=1
        )

    async def test_timeout_when_set_on_request_timeout_via_float(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(3000, 2000, 1000),
            factory_opts=None,
            request_timeout=10.1,
            request_opts=None,
            expected_total_timeout=10.1,
            expected_connect_timeout=2,
            expected_read_timeout=1
        )

    async def test_timeout_when_set_on_request_opts_only(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=1100,
                read_timeout_ms=2100
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.1,
            expected_read_timeout=2.1
        )

    # some timeouts specified in opts
    # no request_timeout
    # all timeouts specified in configuration
    # expect values from configuration to be used where not specified in opts
    async def test_timeout_when_partially_set_on_request_opts(self, create_api_client_with_factory, async_req, is_async):

        # specify total and connect
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=10200,
                connect_timeout_ms=1200,
                read_timeout_ms=3400
            ),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=1100,
                read_timeout_ms=None
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.1,
            expected_read_timeout=3.4
        )

        # specify connect and read
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=10200,
                connect_timeout_ms=1200,
                read_timeout_ms=3400
            ),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=None,
                connect_timeout_ms=1100,
                read_timeout_ms=2100
            ),
            expected_total_timeout=10.2,
            expected_connect_timeout=1.1,
            expected_read_timeout=2.1
        )

        # specify total and read
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=10200,
                connect_timeout_ms=1200,
                read_timeout_ms=3400
            ),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=None,
                read_timeout_ms=2100
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.2,
            expected_read_timeout=2.1
        )

        # specify total only
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=10200,
                connect_timeout_ms=1200,
                read_timeout_ms=3400
            ),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=None,
                read_timeout_ms=None
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.2,
            expected_read_timeout=3.4
        )

        # specify connect only
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=10200,
                connect_timeout_ms=1200,
                read_timeout_ms=3400
            ),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=None,
                connect_timeout_ms=1100,
                read_timeout_ms=None
            ),
            expected_total_timeout=10.2,
            expected_connect_timeout=1.1,
            expected_read_timeout=3.4
        )

        # specify read only
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=10200,
                connect_timeout_ms=1200,
                read_timeout_ms=3400
            ),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=None,
                connect_timeout_ms=None,
                read_timeout_ms=2100
            ),
            expected_total_timeout=10.2,
            expected_connect_timeout=1.2,
            expected_read_timeout=2.1
        )

    async def test_timeout_when_set_on_config_only(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=3000, 
                connect_timeout_ms=2000, 
                read_timeout_ms=1000),
            factory_opts=None,
            request_timeout=None,
            request_opts=None,
            expected_total_timeout=3,
            expected_connect_timeout=2,
            expected_read_timeout=1
        )

    async def test_timeout_when_set_on_request_timeout_only(self, create_api_client_with_factory, async_req, is_async):
        request_timeout = aiohttp.ClientTimeout(total=10.2, connect=1.2, sock_read=3.4) if is_async else urllib3.Timeout(total=10.2, connect=1.2, read=3.4)
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=None,
            expected_total_timeout=10.2,
            expected_connect_timeout=1.2,
            expected_read_timeout=3.4
        )

    # all timeouts specified in opts
    # all timeouts specified in request_timeout
    # expect values from opts to be used
    async def test_request_opts_override_request_timeout(self, create_api_client_with_factory, async_req, is_async):
        request_timeout = aiohttp.ClientTimeout(total=10.2, connect=1.2, sock_read=3.4) if is_async else urllib3.Timeout(total=10.2, connect=1.2, read=3.4)
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=1100,
                read_timeout_ms=2100
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.1,
            expected_read_timeout=2.1
        )

    # some timeouts specified in opts
    # all timeouts specified in request_timeout
    # expect values from request_timeout to be used where not specified in opts
    async def test_timeout_when_set_on_request_timeout_and_partially_set_on_request_opts(self, create_api_client_with_factory, async_req, is_async):

        # specify total and connect
        request_timeout = aiohttp.ClientTimeout(total=10.2, connect=1.2, sock_read=3.4) if is_async else urllib3.Timeout(total=10.2, connect=1.2, read=3.4)
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=1100,
                read_timeout_ms=None
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.1,
            expected_read_timeout=3.4
        )

        # specify connect and read
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=None,
                connect_timeout_ms=1100,
                read_timeout_ms=2100
            ),
            expected_total_timeout=10.2,
            expected_connect_timeout=1.1,
            expected_read_timeout=2.1
        )

        # specify total and read
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=None,
                read_timeout_ms=2100
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.2,
            expected_read_timeout=2.1
        )

        # specify total only
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=5100,
                connect_timeout_ms=None,
                read_timeout_ms=None
            ),
            expected_total_timeout=5.1,
            expected_connect_timeout=1.2,
            expected_read_timeout=3.4
        )

        # specify connect only
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=None,
                connect_timeout_ms=1100,
                read_timeout_ms=None
            ),
            expected_total_timeout=10.2,
            expected_connect_timeout=1.1,
            expected_read_timeout=3.4
        )

        # specify read only
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=None,
                connect_timeout_ms=None,
                read_timeout_ms=2100
            ),
            expected_total_timeout=10.2,
            expected_connect_timeout=1.2,
            expected_read_timeout=2.1
        )

    # some timeouts specified in opts
    # some timeouts specified in request_timeout
    # some timeouts specified in configuration
    # expect precedence to be opts > request_timeout > configuration
    async def test_timeout_when_partially_set_on_request_timeout_and_partially_set_on_request_opts(self, create_api_client_with_factory, async_req, is_async):
        request_timeout = aiohttp.ClientTimeout(total=6, connect=5, sock_read=None) if is_async else urllib3.Timeout(total=6, connect=5, read=None)
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=3000, 
                connect_timeout_ms=2000, 
                read_timeout_ms=1000),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=9000,
                connect_timeout_ms=None,
                read_timeout_ms=None
            ),
            expected_total_timeout=9,
            expected_connect_timeout=5,
            expected_read_timeout=1
        )

    async def test_timeout_when_both_request_timeout_and_request_opts_all_values_set_to_none(self, create_api_client_with_factory, async_req, is_async):
        request_timeout = aiohttp.ClientTimeout(total=None, connect=None, sock_read=None) if is_async else urllib3.Timeout(total=None, connect=None, read=None)
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(
                total_timeout_ms=3000, 
                connect_timeout_ms=2000, 
                read_timeout_ms=1000),
            factory_opts=None,
            request_timeout=request_timeout,
            request_opts=ConfigurationOptions(
                total_timeout_ms=None,
                connect_timeout_ms=None,
                read_timeout_ms=None
            ),
            expected_total_timeout=3,
            expected_connect_timeout=2,
            expected_read_timeout=1
        )

    # ensure the zeros are not treated as 'falsey' causing us to use the default value
    async def test_zero_timeouts_respected_in_config(self, create_api_client_with_factory, async_req, is_async):
        # urllib3 used in sync does not allow the timeout to be set to zero - ensure it's converted to None
        expected_timeout = 0 if is_async else None
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(0, 0, 0),
            factory_opts=None,
            request_timeout=None,
            request_opts=None,
            expected_total_timeout=expected_timeout,
            expected_connect_timeout=expected_timeout,
            expected_read_timeout=expected_timeout
        )

    # ensure the zeros are not treated as 'falsey' causing us to use the default value
    async def test_zero_timeouts_respected_in_request_opts(self, create_api_client_with_factory, async_req, is_async):
        # urllib3 used in sync does not allow the timeout to be set to zero - ensure it's converted to None
        expected_timeout = 0 if is_async else None
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(5000, 5000, 5000),
            factory_opts=None,
            request_timeout=None,
            request_opts=ConfigurationOptions(
                total_timeout_ms=0,
                connect_timeout_ms=0,
                read_timeout_ms=0
            ),
            expected_total_timeout=expected_timeout,
            expected_connect_timeout=expected_timeout,
            expected_read_timeout=expected_timeout
        )

# contains tests that are common to async clients created either manually or through the api client factory
class BaseAsyncTests(BaseTests):
    # ensure the zeros are not treated as 'falsey' causing us to use the default value
    async def test_zero_timeouts_respected_in_request_timeout(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(5000, 5000, 5000),
            factory_opts=None,
            request_timeout=aiohttp.ClientTimeout(total=0, connect=0, sock_read=0),
            request_opts=None,
            expected_total_timeout=0,
            expected_connect_timeout=0,
            expected_read_timeout=0
        )

# contains tests that are common to sync clients created either manually or through the api client factory
class BaseSyncTests(BaseTests):
    
    # this tuple is only valid with urllib3.Timeout 
    async def test_timeout_when_set_on_request_via_tuple(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=None,
            request_timeout=(1,2),
            request_opts=None,
            expected_total_timeout=Configuration.DEFAULT_TOTAL_TIMEOUT_MS / 1000.0,
            expected_connect_timeout=1,
            expected_read_timeout=2
        )

# contains test that are common to sync and async clients created through the api client factory
# NOTE: that the retries tests are not in BaseTests because the api client created manually does not have the retrying rest client
class BaseApiClientFromFactoryTests(BaseTests):
    
    async def _run_rate_limit_test(
        self,
        async_req: Optional[bool],
        is_async: bool,
        rate_limit_retries_config: int,
        factory_opts: ConfigurationOptions,
        request_opts: ConfigurationOptions,
        return_status_code: int,
        expected_times_called: int
    ):
        mock_pool_manager = MockPoolManager(return_status_code)
        api = self._create_api_instance_with_factory(
            is_async=is_async, 
            rate_limit_retries_config=rate_limit_retries_config,
            configuration_timeouts=Timeouts.get_default(), 
            opts=factory_opts, 
            mock_pool_manager=mock_pool_manager)
        
        try:
            result = api.TEST_METHOD
                async_req=async_req,
                opts=request_opts)
            
            if async_req:
                result = result.get(timeout=60)
            
            if is_async:
                await result
        except(ApiException):
            ...
        finally:
            if is_async:
                await api.api_client.close()
            else:
                api.api_client.close()
        
        assert mock_pool_manager.callCount == expected_times_called

    # ensure the zeros are not treated as 'falsey' causing us to use the default value
    async def test_zero_timeouts_respected_in_factory_opts(self, create_api_client_with_factory, async_req, is_async):
        # urllib3 used in sync does not allow the timeout to be set to zero - ensure it's converted to None
        expected_timeout = 0 if is_async else None
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts(5000, 5000, 5000),
            factory_opts=ConfigurationOptions(
                total_timeout_ms=0,
                connect_timeout_ms=0,
                read_timeout_ms=0
            ),
            request_timeout=None,
            request_opts=None,
            expected_total_timeout=expected_timeout,
            expected_connect_timeout=expected_timeout,
            expected_read_timeout=expected_timeout
        )

    # ensure the zeros are not treated as 'falsey' causing us to use the default value
    async def test_zero_rate_limit_retries_respected_in_configuration(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=0,
            factory_opts=None,
            request_opts=None,
            return_status_code=429,
            expected_times_called=1
        )

    # ensure the zeros are not treated as 'falsey' causing us to use the default value
    async def test_zero_rate_limit_retries_respected_in_factory_opts(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=None,
            factory_opts=ConfigurationOptions(rate_limit_retries=0),
            request_opts=None,
            return_status_code=429,
            expected_times_called=1
        )

    # ensure the zeros are not treated as 'falsey' causing us to use the default value
    async def test_zero_rate_limit_retries_respected_in_request_opts(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=None,
            factory_opts=None,
            request_opts=ConfigurationOptions(rate_limit_retries=0),
            return_status_code=429,
            expected_times_called=1
        )

    async def test_timeout_when_set_on_factory_opts(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=Timeouts.get_default(),
            factory_opts=ConfigurationOptions(
                total_timeout_ms=5002,
                connect_timeout_ms=4002,
                read_timeout_ms=3002
            ),
            request_timeout=None,
            request_opts=None,
            expected_total_timeout=5.002,
            expected_connect_timeout=4.002,
            expected_read_timeout=3.002
        )

    async def test_timeout_when_partially_set_on_factory_opts(self, create_api_client_with_factory, async_req, is_async):
        await self._run_timeout_test(
            create_api_client_with_factory=create_api_client_with_factory,
            async_req=async_req,
            is_async=is_async,
            configuration_timeouts=ConfigurationOptions(
                total_timeout_ms=3000,
                connect_timeout_ms=2000,
                read_timeout_ms=1000
            ),
            factory_opts=ConfigurationOptions(
                total_timeout_ms=5002
            ),
            request_timeout=None,
            request_opts=None,
            expected_total_timeout=5.002,
            expected_connect_timeout=2,
            expected_read_timeout=1
        )
    
    async def test_default_rate_limit_retries_if_none_set(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=None,
            factory_opts=None,
            request_opts=None,
            return_status_code=429,
            expected_times_called=Configuration.DEFAULT_RATE_LIMIT_RETRIES + 1
        )

    async def test_retries_config_used_when_not_429_response(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=10,
            factory_opts=None,
            request_opts=None,
            return_status_code=409,
            expected_times_called=Configuration.DEFAULT_RETRIES + 1
        )
    
    async def test_rate_limit_retries_set_on_request_when_set_in_config(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=5,
            factory_opts=None,
            request_opts=None,
            return_status_code=429,
            expected_times_called=6
        )

    async def test_rate_limit_retries_set_on_request_when_set_in_factory_opts(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=None,
            factory_opts=ConfigurationOptions(rate_limit_retries=6),
            request_opts=None,
            return_status_code=429,
            expected_times_called=7
        )

    async def test_rate_limit_retries_set_on_request_when_set_in_request_opts(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=None,
            factory_opts=None,
            request_opts=ConfigurationOptions(rate_limit_retries=7),
            return_status_code=429,
            expected_times_called=8
        )

    async def test_rate_limit_retries_set_on_request_when_factory_opts_override_config(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=5,
            factory_opts=ConfigurationOptions(rate_limit_retries=6),
            request_opts=None,
            return_status_code=429,
            expected_times_called=7
        )

    async def test_rate_limit_retries_set_on_request_when_request_opts_override_config(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=5,
            factory_opts=None,
            request_opts=ConfigurationOptions(rate_limit_retries=7),
            return_status_code=429,
            expected_times_called=8
        )

    async def test_rate_limit_retries_set_on_request_when_request_opts_override_factory_opts(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=None,
            factory_opts=ConfigurationOptions(rate_limit_retries=6),
            request_opts=ConfigurationOptions(rate_limit_retries=7),
            return_status_code=429,
            expected_times_called=8
        )

    async def test_rate_limit_retries_set_on_request_when_request_opts_override_factory_opts_override_config(self, create_api_client_with_factory, async_req, is_async):
        await self._run_rate_limit_test(
            async_req=async_req,
            is_async=is_async,
            rate_limit_retries_config=5,
            factory_opts=ConfigurationOptions(rate_limit_retries=6),
            request_opts=ConfigurationOptions(rate_limit_retries=7),
            return_status_code=429,
            expected_times_called=8
        )

@pytest.mark.parametrize("create_api_client_with_factory, async_req, is_async",
    [(True, True, True), 
    (True, False, True), 
    (True, None, True)])
@pytest.mark.asyncio
class TestWithAsyncApiClientFromFactory(BaseApiClientFromFactoryTests, BaseAsyncTests):
    ...

@pytest.mark.parametrize("create_api_client_with_factory, async_req, is_async",
    [(False, True, True), 
    (False, False, True), 
    (False, None, True)])
@pytest.mark.asyncio
class TestWithAsyncApiClientManualCreation(BaseAsyncTests):
    ...

@pytest.mark.parametrize("create_api_client_with_factory, async_req, is_async",
    [(True, True, False), 
    (True, False, False), 
    (True, None, False)])
@pytest.mark.asyncio
class TestWithSyncApiClientFromFactory(BaseApiClientFromFactoryTests, BaseSyncTests):
    ...

@pytest.mark.parametrize("create_api_client_with_factory, async_req, is_async",
    [(False, True, False), 
    (False, False, False), 
    (False, None, False)])
@pytest.mark.asyncio
class TestWithSyncApiClientManualCreation(BaseSyncTests):
    ...
