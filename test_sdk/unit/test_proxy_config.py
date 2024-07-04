import pytest

from TO_BE_REPLACED.extensions.proxy_config import ProxyConfig


class TestProxyConfig:

    def test_format_schemas_with_port(self):
        """
        Tests that the proxy can be formatted correctly with a port

        :return: None
        """
        proxy_config = ProxyConfig(
            address="http://localhost:8888",
            username="username",
            password="password"
        )

        formatted = proxy_config.format_proxy_schema()

        expected = {
            "http": "http://username:password@localhost:8888",
            "https": "http://username:password@localhost:8888"
        }

        assert expected == formatted

    def test_format_schemas_no_port(self):
        """
        Tests that the proxy can be formatted correctly without a port

        :return: None
        """
        proxy_config = ProxyConfig(
            address="http://localhost",
            username="username",
            password="password"
        )

        formatted = proxy_config.format_proxy_schema()

        expected = {
            "http": "http://username:password@localhost",
            "https": "http://username:password@localhost"
        }

        assert expected == formatted

    def test_create_proxy_no_protocol(self):
        """
        Tests that the proxy won't be created without a fully qualified address

        :return: None
        """

        with pytest.raises(ValueError) as ex:
            ProxyConfig(
                address="localhost",
                username="username",
                password="password"
            )

        assert ex.value.args[0] == f"The provided proxy address of localhost does not contain a protocol, please specify in the full format e.g. http://myproxy.com:8080"
