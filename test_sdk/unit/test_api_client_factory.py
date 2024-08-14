from aiohttp import ClientSession, TCPConnector, TraceConfig
from TO_BE_REPLACED import SyncApiClientFactory, ApiClientFactory, FileTokenConfigurationLoader
from TO_BE_REPLACED.api_response import ApiResponse
from TO_BE_REPLACED.api_client import ApiClient as AsyncApiClient
from TO_BE_REPLACED.extensions.api_client import SyncApiClient
from TO_BE_REPLACED.extensions.api_client_factory import set_additional_api_client_headers
from TO_BE_REPLACED.configuration import Configuration
from unittest.mock import MagicMock, patch
from TO_BE_REPLACED.TEST_API_MODULE import TEST_API as TestApi
from TO_BE_REPLACED.extensions.api_configuration import ApiConfiguration
from TO_BE_REPLACED.extensions.socket_keep_alive import keep_alive_socket_options
from TO_BE_REPLACED.extensions.tcp_keep_alive_connector import (
    TCPKeepAliveHTTPSConnectionPool,
    TCPKeepAliveHTTPConnectionPool,
)
import pytest
import pytest_asyncio
from unittest import mock


@pytest.fixture
def patch_get_access_token():
    with patch(
        "TO_BE_REPLACED.extensions.api_client_builder._get_access_token",
        return_value="fake_token",
    ):
        yield


@pytest_asyncio.fixture(params=(SyncApiClient, AsyncApiClient))
async def api_client(request):
    return request.param()


@pytest.mark.asyncio
async def test_set_additional_api_client_headers_sets_app_name(api_client):
    app_name = "test_app_name"
    set_additional_api_client_headers(api_client, app_name)
    assert api_client.default_headers["X-LUSID-Application"] == app_name


@pytest.mark.asyncio
async def test_set_additional_api_client_headers_sets_correlation_id_from_parameters(
    api_client,
):
    corr_id = "test_correlation_id"
    set_additional_api_client_headers(api_client, correlation_id=corr_id)
    assert api_client.default_headers["CorrelationId"] == corr_id


@pytest.mark.asyncio
async def test_set_additional_api_client_headers_sets_correlation_id_from_env_var(
    api_client,
):
    corr_id = "test_correlation_id"
    with patch.dict("os.environ", {"FBN_CORRELATION_ID": corr_id}, clear=True):
        set_additional_api_client_headers(api_client, correlation_id=corr_id)
        assert api_client.default_headers["CorrelationId"] == corr_id


@pytest.mark.asyncio
async def test_set_additional_api_client_headers_sets_nothing_if_no_params_passed(
    api_client,
):
    set_additional_api_client_headers(api_client)
    assert api_client.default_headers.get("CorrelationId") is None
    assert api_client.default_headers.get("X-LUSID-Application") is None


class TestSyncApiClientFactory:
    def test_build_returns_api_instance_with_sync_client(self):
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            with patch(
                "TO_BE_REPLACED.extensions.api_client_factory.set_additional_api_client_headers"
            ) as set_additional_api_client_headers_mock:
                get_api_configuration_mock.return_value = api_client_config_mock

                api_client_factory = SyncApiClientFactory(config_loaders=[])
        with api_client_factory:
            instance = api_client_factory.build(TestApi)
        get_api_configuration_mock.assert_called_once_with(config_loaders=[])
        api_client_config_mock.build_api_client_config.assert_called_once_with(
            tcp_keep_alive=True,
            socket_options=keep_alive_socket_options(),
            id_provider_response_handler=None,
        )
        args, kwargs = set_additional_api_client_headers_mock.call_args
        assert isinstance(args[0], SyncApiClient)
        assert kwargs.get("app_name") is None
        assert kwargs.get("correlation_id") is None
        assert isinstance(instance.api_client, SyncApiClient)

    def test_build_with_socket_options_and_tcp_keep_alive_True_sets_socket_options_on_config(
        self,
    ):
        socket_options = [("test_option", "test_option_level", "test_option_value")]
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            get_api_configuration_mock.return_value = api_client_config_mock
            api_client_factory = SyncApiClientFactory(
                config_loaders=[], socket_options=socket_options
            )
        with api_client_factory:
            instance = api_client_factory.build(TestApi)
        get_api_configuration_mock.assert_called_once_with(config_loaders=[])
        api_client_config_mock.build_api_client_config.assert_called_once_with(
            tcp_keep_alive=True,
            socket_options=socket_options,
            id_provider_response_handler=None,
        )
        assert (
            {
                "http": TCPKeepAliveHTTPConnectionPool,
                "https": TCPKeepAliveHTTPSConnectionPool,
            }
            == instance.api_client.rest_client.rest_object.pool_manager.pool_classes_by_scheme
        )


class TestAsyncApiClientFactory:
    @pytest.mark.asyncio
    async def test_build_returns_api_instance_with_async_client(self):
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            with patch(
                "TO_BE_REPLACED.extensions.api_client_factory.set_additional_api_client_headers"
            ) as set_additional_api_client_headers_mock:
                get_api_configuration_mock.return_value = api_client_config_mock

                api_client_factory = ApiClientFactory(config_loaders=[])
        async with api_client_factory:
            instance = api_client_factory.build(TestApi)
        get_api_configuration_mock.assert_called_once_with(config_loaders=[])
        api_client_config_mock.build_api_client_config.assert_called_once_with(
            tcp_keep_alive=True,
            socket_options=keep_alive_socket_options(),
            id_provider_response_handler=None,
        )
        args, kwargs = set_additional_api_client_headers_mock.call_args
        assert isinstance(args[0], AsyncApiClient)
        assert kwargs.get("app_name") is None
        assert kwargs.get("correlation_id") is None
        assert isinstance(instance.api_client, AsyncApiClient)

    @pytest.mark.asyncio
    async def test_build_with_client_session_and_tcp_keep_alive_True_uses_TcpKeepAliveConnector(
        self,
    ):
        client_session_mock = MagicMock(spec=ClientSession)
        base_connector = TCPConnector()
        client_session_mock.connector = base_connector
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            with patch(
                "TO_BE_REPLACED.extensions.api_client_factory.TcpKeepAliveConnector"
            ) as connector_mock:
                get_api_configuration_mock.return_value = api_client_config_mock
                api_client_factory = ApiClientFactory(
                    config_loaders=[],
                    client_session=client_session_mock,
                    tcp_keep_alive=True,
                )
        async with api_client_factory:
            api_instance = api_client_factory.build(TestApi)
        connector_mock.assert_called_once_with(
            connector=base_connector, socket_options=keep_alive_socket_options()
        )
        assert (
            connector_mock.return_value
            == api_instance.api_client.rest_client.rest_object.pool_manager.connector
        )

    @pytest.mark.asyncio
    async def test_build_with_tcp_keep_alive_True_uses_TcpKeepAliveConnector(self):
        base_connector = TCPConnector()
        api_client = AsyncApiClient()
        base_connector = api_client.rest_client.pool_manager.connector
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            get_api_configuration_mock.return_value = api_client_config_mock
            with patch(
                "TO_BE_REPLACED.extensions.api_client_factory.TcpKeepAliveConnector"
            ) as connector_mock:
                with patch(
                    "TO_BE_REPLACED.extensions.api_client_factory.ApiClient",
                ) as api_client_mock:
                    api_client_mock.return_value = api_client
                    api_client_factory = ApiClientFactory(
                        config_loaders=[], tcp_keep_alive=True
                    )
        async with api_client_factory:
            api_instance = api_client_factory.build(TestApi)
        connector_mock.assert_called_once_with(
            connector=base_connector, socket_options=keep_alive_socket_options()
        )
        assert (
            connector_mock.return_value
            == api_instance.api_client.rest_client.rest_object.pool_manager.connector
        )

    @pytest.mark.asyncio
    async def test_build_with_socket_options_uses_TcpKeepAliveConnector_with_socket_options(
        self,
    ):
        socket_options = [("test_option", "test_option_level", "test_option_value")]
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            get_api_configuration_mock.return_value = api_client_config_mock
            with patch(
                "TO_BE_REPLACED.extensions.api_client_factory.TcpKeepAliveConnector"
            ) as connector_mock:
                api_client_factory = ApiClientFactory(
                    config_loaders=[], socket_options=socket_options
                )
        async with api_client_factory:
            api_instance = api_client_factory.build(TestApi)
        args, kwargs = connector_mock.call_args
        assert socket_options == kwargs["socket_options"]
        assert (
            connector_mock.return_value
            == api_instance.api_client.rest_client.rest_object.pool_manager.connector
        )

    @pytest.mark.asyncio
    async def test_build_with_trace_config_builds_api_client_with_trace_configs(
        self,
    ):
        trace_configs = [TraceConfig()]
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            get_api_configuration_mock.return_value = api_client_config_mock
            with patch(
                "TO_BE_REPLACED.extensions.api_client_factory.ClientSession"
            ) as client_session_mock:
                ApiClientFactory(config_loaders=[], trace_configs=trace_configs)
        args, kwargs = client_session_mock.call_args
        assert trace_configs == kwargs["trace_configs"]

    @pytest.mark.asyncio
    async def test_build_with_client_session_with_trace_config_builds_api_client_with_trace_configs(
        self,
    ):
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            get_api_configuration_mock.return_value = api_client_config_mock
            with patch(
                "TO_BE_REPLACED.extensions.api_client_factory.ClientSession"
            ) as client_session_mock:
                ApiClientFactory(config_loaders=[], client_session=client_session_mock)
        args, kwargs = client_session_mock.call_args
        assert client_session_mock.trace_configs == kwargs["trace_configs"]

    @pytest.mark.asyncio
    async def test_build_with_client_connector(self):
        base_connector = TCPConnector()
        api_client = AsyncApiClient()
        base_connector = api_client.rest_client.pool_manager.connector
        client_session = ClientSession(connector=base_connector)
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            get_api_configuration_mock.return_value = api_client_config_mock
            with patch(
                    "TO_BE_REPLACED.extensions.api_client_factory.ApiClient",
                ) as api_client_mock:
                    api_client_mock.return_value = api_client
                    api_client_factory = ApiClientFactory(
                        config_loaders=[], tcp_keep_alive=True, client_session=client_session
                    )
        async with api_client_factory:
            api_instance = api_client_factory.build(TestApi)
        
        assert (
            False
            == api_instance.api_client.rest_client.rest_object.pool_manager.connector_owner
        )

    @pytest.mark.asyncio
    async def test_build_without_client_connector(self):
        api_client = AsyncApiClient()
        api_client_config_mock = MagicMock(spec=ApiConfiguration)
        api_client_config_mock.build_api_client_config.return_value = Configuration()
        with patch(
            "TO_BE_REPLACED.extensions.api_client_factory.get_api_configuration"
        ) as get_api_configuration_mock:
            get_api_configuration_mock.return_value = api_client_config_mock
            with patch(
                    "TO_BE_REPLACED.extensions.api_client_factory.ApiClient",
                ) as api_client_mock:
                    api_client_mock.return_value = api_client
                    api_client_factory = ApiClientFactory(
                        config_loaders=[], tcp_keep_alive=True
                    )
        async with api_client_factory:
            api_instance = api_client_factory.build(TestApi)
       
        assert (
            True
            == api_instance.api_client.rest_client.rest_object.pool_manager.connector_owner
        )

class TestApiClientFileTokenConfiguration:
    def test_api_client_with_config(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="sample_token")):
            
            file_token_loader = FileTokenConfigurationLoader(access_token_location="test_file")
            config = file_token_loader.load_config()
            assert "sample_token" == config["access_token"]

    def test_api_with_no_path(self):
        config_loader = FileTokenConfigurationLoader(access_token_location="")
        config = config_loader.load_config()
        assert config["access_token"] is None
    
    def test_api_with_incorrect_path(self):
        # Mock the open function to raise FileNotFoundError when called
        with mock.patch("builtins.open", mock.mock_open()) as mocked_open:
            mocked_open.side_effect = FileNotFoundError
            
            file_token_loader = FileTokenConfigurationLoader(access_token_location="invalid_path")

            caught_exception = False    
            try:
                config = file_token_loader.load_config()
            except FileNotFoundError:
                caught_exception = True
            
            assert(caught_exception is True)
            