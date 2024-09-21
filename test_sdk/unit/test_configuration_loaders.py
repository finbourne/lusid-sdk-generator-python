import json
import pytest
from TO_BE_REPLACED.extensions import (
    SecretsFileConfigurationLoader,
    EnvironmentVariablesConfigurationLoader,
    ArgsConfigurationLoader,
    FileTokenConfigurationLoader,
)
from TO_BE_REPLACED.extensions.api_client_factory import get_api_configuration
from unittest import mock


class TestSecretsFileConfigurationLoader:
    def test_load_config_loads_api_config(self):
        expected_config = {
            "token_url": "sample_tokenUrl",
            "api_url": "sample_apiUrl",
            "username": "sample_username",
            "password": "sample_password",
            "client_id": "sample_clientId",
            "client_secret": "sample_clientSecret",
            "app_name": "sample_applicationName",
            "certificate_filename": "sample_clientCertificate",
            "access_token": "accessToken",
            "proxy_address": None,
            "proxy_username": None,
            "proxy_password": None,
            "total_timeout_ms": 3000,
            "connect_timeout_ms": 2000,
            "read_timeout_ms": 1000,
            "rate_limit_retries": 5,
        }

        secrets_file_contents = {
            "api": {
                "tokenUrl": "sample_tokenUrl",
                "TO_BE_REPLACEDUrl": "sample_apiUrl",
                "username": "sample_username",
                "password": "sample_password",
                "clientId": "sample_clientId",
                "clientSecret": "sample_clientSecret",
                "applicationName": "sample_applicationName",
                "clientCertificate": "sample_clientCertificate",
                "accessToken": "accessToken",
                "totalTimeoutMs": 3000,
                "connectTimeoutMs": 2000,
                "readTimeoutMs": 1000,
                "rateLimitRetries": 5,
            }
        }
        api_secrets_file = "secrets.json"
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=json.dumps(secrets_file_contents))
        ) as openMock:
            config_loader = SecretsFileConfigurationLoader(api_secrets_file)
            result = config_loader.load_config()
            openMock.assert_called_once_with(api_secrets_file)
            assert result == expected_config

    def test_load_config_loads_proxy_config(self):
        expected_config = {
            "token_url": None,
            "api_url": None,
            "username": None,
            "password": None,
            "client_id": None,
            "client_secret": None,
            "app_name": None,
            "certificate_filename": None,
            "access_token": None,
            "proxy_address": "sample_address",
            "proxy_username": "sample_username",
            "proxy_password": "sample_password",
            "total_timeout_ms": None,
            "connect_timeout_ms": None,
            "read_timeout_ms": None,
            "rate_limit_retries": None,
        }

        secrets_file_contents = {
            "proxy": {
                "address": "sample_address",
                "username": "sample_username",
                "password": "sample_password",
            }
        }
        api_secrets_file = "secrets.json"
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=json.dumps(secrets_file_contents))
        ) as openMock:
            config_loader = SecretsFileConfigurationLoader(api_secrets_file)
            result = config_loader.load_config()
            openMock.assert_called_once_with(api_secrets_file)
            assert result == expected_config


class TestEnvironmentVariablesConfigurationLoader:
    def test_load_config_loads_api_config(self):
        url_env_var="FBN_TO_BE_REPLACED_API_URL".upper()
        environment_variables = {
            "FBN_TOKEN_URL": "sample_tokenUrl",
            url_env_var: "sample_apiUrl",
            "FBN_USERNAME": "sample_username",
            "FBN_PASSWORD": "sample_password",
            "FBN_CLIENT_ID": "sample_clientId",
            "FBN_CLIENT_SECRET": "sample_clientSecret",
            "FBN_APP_NAME": "sample_applicationName",
            "FBN_CLIENT_CERTIFICATE": "sample_clientCertificate",
            "FBN_ACCESS_TOKEN": "accessToken",
            "FBN_TOTAL_TIMEOUT_MS": "3000",
            "FBN_CONNECT_TIMEOUT_MS": "2000",
            "FBN_READ_TIMEOUT_MS": "1000",
            "FBN_RATE_LIMIT_RETRIES": "5"
        }
        expected_config = {
            "token_url": "sample_tokenUrl",
            "api_url": "sample_apiUrl",
            "username": "sample_username",
            "password": "sample_password",
            "client_id": "sample_clientId",
            "client_secret": "sample_clientSecret",
            "app_name": "sample_applicationName",
            "certificate_filename": "sample_clientCertificate",
            "access_token": "accessToken",
            "proxy_address": None,
            "proxy_username": None,
            "proxy_password": None,
            "total_timeout_ms": 3000,
            "connect_timeout_ms": 2000,
            "read_timeout_ms": 1000,
            "rate_limit_retries": 5,
        }
        with mock.patch.dict("os.environ", environment_variables, clear=True):
            config_loader = EnvironmentVariablesConfigurationLoader()
            result = config_loader.load_config()
            assert result == expected_config

    def test_load_config_loads_proxy_config(self):
        environment_variables = {
            "FBN_PROXY_ADDRESS": "sample_address",
            "FBN_PROXY_USERNAME": "sample_username",
            "FBN_PROXY_PASSWORD": "sample_password",
        }
        expected_config = {
            "token_url": None,
            "api_url": None,
            "username": None,
            "password": None,
            "client_id": None,
            "client_secret": None,
            "app_name": None,
            "certificate_filename": None,
            "access_token": None,
            "proxy_address": "sample_address",
            "proxy_username": "sample_username",
            "proxy_password": "sample_password",
            "total_timeout_ms": None,
            "connect_timeout_ms": None,
            "read_timeout_ms": None,
            "rate_limit_retries": None,
        }
        with mock.patch.dict("os.environ", environment_variables, clear=True):
            config_loader = EnvironmentVariablesConfigurationLoader()
            result = config_loader.load_config()
            assert expected_config == result

    @pytest.mark.parametrize("key, config_name",
    [("FBN_TOTAL_TIMEOUT_MS", "total_timeout_ms"),
     ("FBN_CONNECT_TIMEOUT_MS", "connect_timeout_ms"),
     ("FBN_READ_TIMEOUT_MS", "read_timeout_ms"),
     ("FBN_RATE_LIMIT_RETRIES", "rate_limit_retries")])
    def test_load_config_throws_if_invalid_int_values(self, key, config_name):
        environment_variables = {
            key: "not-a-number"
        }
        with mock.patch.dict("os.environ", environment_variables, clear=True):
            with pytest.raises(ValueError) as e:
                config_loader = EnvironmentVariablesConfigurationLoader()
                config_loader.load_config()
            assert str(e.value) == f"invalid value for '{config_name}' - value must be an integer if set"

class TestArgsConfigurationLoader:
    def test_load_config_gets_config_dict(self):
        kwargs = {
            "token_url": "sample_tokenUrl",
            "api_url": "sample_apiUrl",
            "username": "sample_username",
            "password": "sample_password",
            "client_id": "sample_clientId",
            "client_secret": "sample_clientSecret",
            "app_name": "sample_applicationName",
            "certificate_filename": "sample_clientCertificate",
            "access_token": "accessToken",
            "proxy_address": "sample_address",
            "proxy_username": "sample_username",
            "proxy_password": "sample_password",
            "total_timeout_ms": 3000,
            "connect_timeout_ms": 2000,
            "read_timeout_ms": 1000,
            "rate_limit_retries": 5,
        }
        expected_config = {
            "token_url": "sample_tokenUrl",
            "api_url": "sample_apiUrl",
            "username": "sample_username",
            "password": "sample_password",
            "client_id": "sample_clientId",
            "client_secret": "sample_clientSecret",
            "app_name": "sample_applicationName",
            "certificate_filename": "sample_clientCertificate",
            "access_token": "accessToken",
            "proxy_address": "sample_address",
            "proxy_username": "sample_username",
            "proxy_password": "sample_password",
            "total_timeout_ms": 3000,
            "connect_timeout_ms": 2000,
            "read_timeout_ms": 1000,
            "rate_limit_retries": 5,
        }
        config_loader = ArgsConfigurationLoader(**kwargs)
        result = config_loader.load_config()
        assert expected_config == result


def test_get_api_configuration_overwrites_content_in_order():
    mock_config_loader_1 = EnvironmentVariablesConfigurationLoader()
    mock_config_loader_1.load_config = mock.MagicMock(return_value={"token_url": "1"})
    mock_config_loader_2 = EnvironmentVariablesConfigurationLoader()
    mock_config_loader_2.load_config = mock.MagicMock(return_value={"token_url": "2"})
    api_config = get_api_configuration([mock_config_loader_1, mock_config_loader_2])
    assert api_config.token_url == "2"


def test_get_api_configuration_does_not_overwrite_content_when_value_None():
    mock_config_loader_1 = EnvironmentVariablesConfigurationLoader()
    mock_config_loader_1.load_config = mock.MagicMock(return_value={"token_url": "1"})
    mock_config_loader_2 = EnvironmentVariablesConfigurationLoader()
    mock_config_loader_2.load_config = mock.MagicMock(return_value={"token_url": None})
    api_config = get_api_configuration([mock_config_loader_1, mock_config_loader_2])
    assert api_config.token_url == "1"


def test_get_api_configuration_returns_api_config_with_proxy_settings_when_proxy_address_not_None():  # noqa
    proxy_address = "http://www.example.com"
    mock_config_loader = EnvironmentVariablesConfigurationLoader()
    mock_config_loader.load_config = mock.MagicMock(
        return_value={"proxy_address": proxy_address}
    )
    api_config = get_api_configuration((mock_config_loader,))
    assert api_config.proxy_config is not None
    assert api_config.proxy_config.address == proxy_address


def test_get_api_configuration_returns_api_config_with_proxy_address_and_username_password():  # noqa
    proxy_address = "http://www.example.com"
    proxy_username = "user"
    proxy_password = "pass"
    mock_config_loader = EnvironmentVariablesConfigurationLoader()
    mock_config_loader.load_config = mock.MagicMock(
        return_value={"proxy_address": proxy_address,
                      "proxy_username": proxy_username,
                      "proxy_password": proxy_password}
    )
    api_config = get_api_configuration((mock_config_loader,))
    assert api_config.proxy_config is not None
    assert api_config.proxy_config.address == proxy_address
    assert api_config.proxy_config.username == proxy_username
    assert api_config.proxy_config.password == proxy_password


class TestFileConfigurationLoader:
    def test_load_config_returns_access_token_from_file(self):
        with mock.patch("builtins.open", mock.mock_open(read_data="sample_token")):
            config_loader = FileTokenConfigurationLoader(
                access_token_location="test_file"
            )
            config = config_loader.load_config()
            assert "sample_token" == config["access_token"]

    def test_load_config_returns_no_access_token_when_location_is_empty_string(self):
        config_loader = FileTokenConfigurationLoader(access_token_location="")
        config = config_loader.load_config()
        assert config["access_token"] is None

    def test_load_config_returns_no_access_token_when_location_is_None(self):
        config_loader = FileTokenConfigurationLoader()
        config = config_loader.load_config()
        assert config["access_token"] is None
