from unittest.mock import patch
from TO_BE_REPLACED.configuration import Configuration
from TO_BE_REPLACED.extensions.configuration_options import ConfigurationOptions
from TO_BE_REPLACED.extensions.proxy_config import ProxyConfig
from TO_BE_REPLACED.extensions.api_configuration import ApiConfiguration
import pytest


@pytest.fixture
def patch_get_access_token():
    with patch.object(
        ApiConfiguration,
        "get_access_token",
        return_value="fake_token",
    ) as get_access_token_mock:
        yield get_access_token_mock


def test_get_access_token_with_access_token_and_url_returns_access_token():
    expected_result = "test_token"
    config = ApiConfiguration(access_token=expected_result, api_url="bla")
    result = config.get_access_token(config)
    assert result == expected_result


def test_get_access_token_with_access_token_set_and_url_returns_access_token():
    expected_result = "test_token"
    config = ApiConfiguration(api_url="bla")
    config.access_token = expected_result
    result = config.get_access_token(config)
    assert result == expected_result


def test_get_access_token_with_OIDC_params_returns_refreshing_token():
    config = ApiConfiguration(
        api_url="bla",
        password="password",
        username="me",
        client_id="test_id",
        client_secret="shhhh",
        token_url="fake_url",
    )
    with patch(
        "TO_BE_REPLACED.extensions.api_configuration.RefreshingToken"
    ) as mock_refreshing_token:
        config.get_access_token()
        mock_refreshing_token.assert_called_once_with(
            api_configuration=config, id_provider_response_handler=None
        )


def test_get_acccess_token_without_access_token_and_OIDC_params_raises_ValueError():
    config = ApiConfiguration()
    with pytest.raises(ValueError):
        config.get_access_token()


def test_build_api_client_config_without_api_url_raises_ValueError():
    config = ApiConfiguration(
        password="password",
        username="me",
        client_id="test_id",
        client_secret="shhhh",
        token_url="fake_url",
    )
    with pytest.raises(ValueError):
        config.build_api_client_config()


def test_build_api_client_config_with_proxy_config_sets_proxy_config_on_api_client_config(
    patch_get_access_token,
):
    expected_address = "http://sample_proxy_address"
    expected_username = "sample_proxy_username"
    expected_password = "sample_proxy_password"

    proxy_config = ProxyConfig(expected_address, expected_username, expected_password)

    config = ApiConfiguration(
        password="password",
        username="me",
        client_id="test_id",
        client_secret="shhhh",
        token_url="fake_url",
        api_url="fake_url",
        proxy_config=proxy_config,
    )

    api_client_config = config.build_api_client_config()
    assert api_client_config.proxy == expected_address
    assert api_client_config.proxy_headers == proxy_config.headers


def test_build_api_client_config_with_api_url_sets_api_client_host(
    patch_get_access_token,
):
    config = ApiConfiguration(
        password="password",
        username="me",
        client_id="test_id",
        client_secret="shhhh",
        token_url="fake_url",
        api_url="sample_api_url",
    )

    api_client = config.build_api_client_config()
    assert "sample_api_url" == api_client.host

def test_build_api_client_config_sets_defaults_if_unset(
    patch_get_access_token,
):
    config = ApiConfiguration(
        password="password",
        username="me",
        client_id="test_id",
        client_secret="shhhh",
        token_url="fake_url",
        api_url="sample_api_url",
    )

    api_client = config.build_api_client_config()
    assert api_client.timeouts.total_timeout_ms == Configuration.DEFAULT_TOTAL_TIMEOUT_MS
    assert api_client.timeouts.connect_timeout_ms == Configuration.DEFAULT_CONNECT_TIMEOUT_MS
    assert api_client.timeouts.read_timeout_ms == Configuration.DEFAULT_READ_TIMEOUT_MS
    assert api_client.rate_limit_retries == Configuration.DEFAULT_RATE_LIMIT_RETRIES

def test_build_api_client_uses_opts_overrides(
    patch_get_access_token,
):
    config = ApiConfiguration(
        password="password",
        username="me",
        client_id="test_id",
        client_secret="shhhh",
        token_url="fake_url",
        api_url="sample_api_url",
        total_timeout_ms=3000,
        connect_timeout_ms=2000,
        read_timeout_ms=1000,
        rate_limit_retries=5,
    )

    opts = ConfigurationOptions(
        total_timeout_ms=6000,
        connect_timeout_ms=5000,
        read_timeout_ms=4000,
        rate_limit_retries=10
    )
    api_client = config.build_api_client_config(opts=opts)
    assert api_client.timeouts.total_timeout_ms == 6000
    assert api_client.timeouts.connect_timeout_ms == 5000
    assert api_client.timeouts.read_timeout_ms == 4000
    assert api_client.rate_limit_retries == 10
