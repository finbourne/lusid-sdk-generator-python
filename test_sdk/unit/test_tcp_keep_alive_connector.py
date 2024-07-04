from aiohttp import ClientRequest, TCPConnector
from TO_BE_REPLACED.extensions.tcp_keep_alive_connector import TcpKeepAliveConnector
from unittest import mock
from unittest.mock import patch
from yarl import URL
import pytest
from TO_BE_REPLACED.extensions.socket_keep_alive import TCP_KEEP_IDLE, TCP_KEEPALIVE_INTERVAL


class TestTCPKeepAliveConnector:
    @pytest.mark.asyncio
    async def test_create_connection_sets_sock_opts(self):
        req = ClientRequest("POST", URL("https://some_url.com"))
        mock_connection = mock.MagicMock(TCPConnector)
        mock_socket = mock.MagicMock()
        mock_connection.connect.return_value.protocol.transport.get_extra_info = mock.MagicMock(return_value=mock_socket)
        socket_options = [(0, 1, 1)]
        connector = TcpKeepAliveConnector(mock_connection, socket_options)
        await connector.connect(req, [], None)
        mock_socket.setsockopt.assert_called_once_with(0, 1, 1)

    @pytest.mark.asyncio
    async def test_create_connection_sets_windows_ioctl_sock_opts(self):
        with patch("TO_BE_REPLACED.extensions.tcp_keep_alive_connector.socket") as socket_module_mock:
            req = ClientRequest("POST", URL("https://some_url.com"))
            mock_connection = mock.MagicMock(TCPConnector)
            mock_socket = mock.MagicMock()
            mock_connection.connect.return_value.protocol.transport.get_extra_info = mock.MagicMock(return_value=mock_socket)
            socket_options = [(0, 1, 1)]
            connector = TcpKeepAliveConnector(mock_connection, socket_options)
            await connector.connect(req, [], None)
            mock_socket.ioctl.assert_called_once_with(socket_module_mock.SIO_KEEPALIVE_VALS, (1, TCP_KEEP_IDLE * 1000, TCP_KEEPALIVE_INTERVAL * 1000))

    @pytest.mark.asyncio
    async def test_create_connection_windows_ioctl_exception_is_caught(self):
        with patch("TO_BE_REPLACED.extensions.tcp_keep_alive_connector.socket") as socket_module_mock:
            del socket_module_mock.ioctl
            req = ClientRequest("POST", URL("https://some_url.com"))
            mock_connection = mock.MagicMock(TCPConnector)
            mock_socket = mock.MagicMock()
            mock_connection.connect.return_value.protocol.transport.get_extra_info = mock.MagicMock(return_value=mock_socket)
            socket_options = [(0, 1, 1)]
            connector = TcpKeepAliveConnector(mock_connection, socket_options)
            await connector.connect(req, [], None)
