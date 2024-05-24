from lusid.extensions.file_access_token import FileAccessToken
from unittest import mock
import time

from more_itertools import side_effect


class TestFileAccessToken:
    def test_file_access_token_loads_token_from_file(self):
        with mock.patch(
            "builtins.open", mock.mock_open(read_data="sample_token")
        ) as mock_file:
            token = FileAccessToken(access_token_location="test_file")
            assert "sample_token" == token
            mock_file.assert_called_once_with("test_file", "r")

    def test_file_access_token_refreshed_token_when_expired(self):
        mock_file_1 = mock.MagicMock()
        mock_file_1.__enter__.return_value = mock_file_1
        mock_file_1.read.return_value = "token1"
        mock_file_2 = mock.MagicMock()
        mock_file_2.__enter__.return_value = mock_file_2
        mock_file_2.read.return_value = "token2"
        with mock.patch("builtins.open", side_effect=[mock_file_1, mock_file_2]):
            token = FileAccessToken(access_token_location="test_file", expiry_time=2)
            assert "token1" == token
            time.sleep(3)
            assert "token2" == token
