import json
from lusid.extensions import (
    SecretsFileConfigurationLoader,
    EnvironmentVariablesConfigurationLoader,
    ArgsConfigurationLoader,
)
from lusid.extensions.api_client_factory import get_api_configuration
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
        }

        secrets_file_contents = {
            "api": {
                "tokenUrl": "sample_tokenUrl",
                "lusidUrl": "sample_apiUrl",
                "username": "sample_username",
                "password": "sample_password",
                "clientId": "sample_clientId",
                "clientSecret": "sample_clientSecret",
                "applicationName": "sample_applicationName",
                "clientCertificate": "sample_clientCertificate",
                "accessToken": "accessToken",
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
        environment_variables = {
            "FBN_TOKEN_URL": "sample_tokenUrl",
            "FBN_LUSID_API_URL": "sample_apiUrl",
            "FBN_USERNAME": "sample_username",
            "FBN_PASSWORD": "sample_password",
            "FBN_CLIENT_ID": "sample_clientId",
            "FBN_CLIENT_SECRET": "sample_clientSecret",
            "FBN_APP_NAME": "sample_applicationName",
            "FBN_CLIENT_CERTIFICATE": "sample_clientCertificate",
            "FBN_ACCESS_TOKEN": "accessToken",
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
        }
        with mock.patch.dict("os.environ", environment_variables, clear=True):
            config_loader = EnvironmentVariablesConfigurationLoader()
            result = config_loader.load_config()
            assert expected_config == result

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
        }
        with mock.patch.dict("os.environ", environment_variables, clear=True):
            config_loader = EnvironmentVariablesConfigurationLoader()
            result = config_loader.load_config()
            assert expected_config == result


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
