from unittest.mock import patch
from urllib3.connection import HTTPConnection
from TO_BE_REPLACED.extensions.socket_keep_alive import keep_alive_socket_options

def test_keep_alive_socket_options_returns_linux_socket_options():
    with patch("TO_BE_REPLACED.extensions.socket_keep_alive.socket") as socket_mock:
        socket_options = keep_alive_socket_options()
        expected_socket_options = HTTPConnection.default_socket_options + [
            (socket_mock.SOL_SOCKET, socket_mock.SO_KEEPALIVE, 1),
            (socket_mock.IPPROTO_TCP, socket_mock.TCP_KEEPIDLE, 60),
            (socket_mock.IPPROTO_TCP, socket_mock.TCP_KEEPINTVL, 60),
            (socket_mock.IPPROTO_TCP, socket_mock.TCP_KEEPCNT, 3),
        ]
        assert expected_socket_options == socket_options


def test_keep_alive_socket_options_returns_osx_socket_options_when_error_thrown():
    with patch("TO_BE_REPLACED.extensions.socket_keep_alive.socket") as socket_mock:
        del socket_mock.TCP_KEEPCNT
        socket_options = keep_alive_socket_options()
        expected_socket_options = HTTPConnection.default_socket_options + [
            (socket_mock.SOL_SOCKET, socket_mock.SO_KEEPALIVE, 1),
            (socket_mock.IPPROTO_TCP, 0x10, 60),
        ]
        assert expected_socket_options == socket_options

def test_keep_alive_socket_options_returns_windows_socket_options_when_error_thrown_in_osx():
    with patch("TO_BE_REPLACED.extensions.socket_keep_alive.socket") as socket_mock:
        del socket_mock.IPPROTO_TCP
        socket_options = keep_alive_socket_options()
        expected_socket_options = HTTPConnection.default_socket_options + [
            (socket_mock.SOL_SOCKET, socket_mock.SO_KEEPALIVE, 1)
        ]
        assert expected_socket_options == socket_options
