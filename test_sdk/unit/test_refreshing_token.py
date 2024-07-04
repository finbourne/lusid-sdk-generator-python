from threading import Thread
from unittest.mock import MagicMock, patch, ANY
from TO_BE_REPLACED.extensions.configuration_loaders import (
    get_api_configuration,
    EnvironmentVariablesConfigurationLoader,
)
from TO_BE_REPLACED.extensions.refreshing_token import RefreshingToken
from time import sleep, time
from TO_BE_REPLACED.extensions.proxy_config import ProxyConfig
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def config():
    return get_api_configuration([EnvironmentVariablesConfigurationLoader()])


@pytest.fixture
def valid_response_mock():
    valid_response_mock = MagicMock()
    valid_response_mock.status_code = 200
    valid_response_mock.json.return_value = {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "expires_in": 3600,
    }
    return valid_response_mock


@pytest.fixture
def rate_limit_response_mock():
    rate_limit_response_mock = MagicMock()
    rate_limit_response_mock.status_code = 429
    rate_limit_response_mock.json.return_value = {
        "error": "rate_limit",
        "error_description": "API rate limit exceeded.",
    }
    return rate_limit_response_mock


@pytest.fixture
def invalid_grant_response_mock():
    invalid_grant_response_mock = MagicMock()
    invalid_grant_response_mock.status_code = 400
    invalid_grant_response_mock.json.return_value = {
        "error": "invalid_grant",
        "error_description": "The refresh token is invalid or expired.",
    }
    return invalid_grant_response_mock


class TestRefreshingToken:
    def test_get_token(self, config):
        refreshed_token = RefreshingToken(api_configuration=config)
        assert refreshed_token is not None

    @staticmethod
    def force_refresh(refresh_token):
        return f"{refresh_token}"

    @staticmethod
    def convert_to_http_date(datetime_value):
        return datetime_value.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def test_get_token_with_proxy(self, config):
        config.proxy_config = ProxyConfig(
            address="https://sample_address",
            username="sample_username",
            password="sample_password",
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "sample_access_token",
            "refresh_token": "sample_refresh_token",
        }
        refreshed_token = RefreshingToken(api_configuration=config, expiry_offset=3599)
        with patch("requests.post") as mock_post_request:
            mock_post_request.return_value = mock_response
            refreshed_token.get_access_token()
            mock_post_request.assert_called_once_with(
                config.token_url,
                data=ANY,
                proxies=config.proxy_config.format_proxy_schema(),
                headers=ANY,
            )

    def test_refreshed_token_when_expired(self, config):
        refreshed_token = RefreshingToken(
            api_configuration=config, expiry_offset=3599
        )  # set to 1s expiry

        assert refreshed_token is not None

        # force de-referencing the token value
        first_value = f"{refreshed_token}"

        sleep(1)

        assert first_value != refreshed_token

    def test_token_when_refresh_token_expired_still_refreshes(
        self, config, valid_response_mock, invalid_grant_response_mock
    ):
        refreshed_token = RefreshingToken(api_configuration=config, expiry_offset=3599)

        assert refreshed_token is not None

        # force de-referencing the token value
        first_value = f"{refreshed_token}"

        sleep(1)

        with patch(
            "requests.post",
            side_effect=[
                invalid_grant_response_mock,
                valid_response_mock,
            ],
        ):
            assert first_value != refreshed_token

    def test_token_when_not_expired_does_not_refresh(self, config):
        refreshed_token = RefreshingToken(api_configuration=config)

        assert refreshed_token is not None

        # force de-referencing the token value
        first_value = f"{refreshed_token}"

        sleep(1)

        assert first_value == refreshed_token

    def test_can_make_header(self, config):
        refreshed_token = RefreshingToken(api_configuration=config)

        header = "Bearer " + refreshed_token

        assert header is not None

    def test_use_refresh_token_multiple_threads(self, config, valid_response_mock):
        refreshed_token = RefreshingToken(api_configuration=config)

        thread1 = Thread(target=self.force_refresh, args=[refreshed_token])
        thread2 = Thread(target=self.force_refresh, args=[refreshed_token])
        thread3 = Thread(target=self.force_refresh, args=[refreshed_token])

        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = lambda *args, **kwargs: valid_response_mock

            thread1.start()
            thread2.start()
            thread3.start()

            thread1.join()
            thread2.join()
            thread3.join()

            # Ensure that we only got an access token once
            assert 1 == identity_mock.call_count

    def test_retries_on_429_status_code_initial_access_token(
        self, config, valid_response_mock, rate_limit_response_mock
    ):
        """
        Ensures that in the event of a 429 HTTP Status Code being
        returned when communicating with an identity
        provider, the request is retried.
        """

        refreshing_token = RefreshingToken(api_configuration=config)

        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = [
                # Return a 429 on the first attempt
                rate_limit_response_mock,
                # Return a 200 on the second attempt
                valid_response_mock,
            ]

            # Ensure that we were able to get the token,
            # if not retrying this would be impossible
            assert f"{refreshing_token}" == "mock_access_token"
            assert identity_mock.call_count == 2

    def test_retries_on_429_status_code_using_refresh_token(
        self, config, valid_response_mock, rate_limit_response_mock
    ):
        """
        Ensures that in the event of a 429 HTTP Status Code being
        returned when communicating with an identity
        provider, the request is retried.
        """
        refreshing_token = RefreshingToken(api_configuration=config)
        valid_response_mock_with_short_timeout = MagicMock()
        valid_response_mock_with_short_timeout.status_code = 200
        valid_response_mock_with_short_timeout.json.return_value = {
            "access_token": "mock_access_token_short",
            "refresh_token": "mock_access_token_short",
            "expires_in": 1,
        }

        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = [
                # Get initial access token
                valid_response_mock_with_short_timeout,
                # Return a 429 on the second attempt
                rate_limit_response_mock,
                # Return a 200 on the third attempt
                valid_response_mock,
            ]

            # Ensure that we were able to get the first access token
            assert f"{refreshing_token}" == "mock_access_token_short"

            sleep(1)  # Wait for initial token to expire

            # Try and get access token again forcing refresh,
            # if we can get it then retry was called
            assert f"{refreshing_token}" == "mock_access_token"
            assert identity_mock.call_count == 3

    def test_does_not_retry_on_4xx_status_code_other_than_429(
        self, config, invalid_grant_response_mock
    ):
        """
        Ensures that we do not retry on other common 4xx status codes
        such as 400 - Bad Request
        """
        refreshing_token = RefreshingToken(api_configuration=config)

        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = [
                # Return a 400
                invalid_grant_response_mock,
            ]

            # Ensure that a 400 is raised as an error and not retried
            with pytest.raises(ValueError) as bad_request_exception:
                self.force_refresh(refreshing_token)

            assert identity_mock.call_count == 1  # No retrying
            assert "invalid_grant" in str(bad_request_exception.value)

    def test_retries_on_429s_up_till_retry_limit(
        self, config, rate_limit_response_mock
    ):
        """
        Ensures that the refreshing token only retries up until
        the retry limit to prevent an infinite retry loop
        """
        refreshing_token = RefreshingToken(api_configuration=config)

        refreshing_token.retry_limit = (
            2  # Override default to ensure test runs in reasonable amount of time
        )
        expected_requests = (
            1 + refreshing_token.retry_limit
        )  # Initial request plus expected number retries

        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = [
                rate_limit_response_mock
            ] * expected_requests  # Return a 429 every time up until expected numberof attempts

            # Ensure that a an error is raised once reaching the retry limit
            with pytest.raises(ValueError) as retry_limit_error:
                self.force_refresh(refreshing_token)

            assert "Max retry limit" in str(retry_limit_error.value)

            # Ensure that we only tried as many times as expected
            assert expected_requests == identity_mock.call_count

    @pytest.mark.parametrize(
        "_, number_attempts_till_success, expected_delay",
        [
            ["One Attempt", 1, 2],
            ["Two Attempts", 2, 2 + 4],
            ["Three Attempts", 3, 2 + 4 + 8],
            ["Four Attempts", 4, 2 + 4 + 8 + 16],
        ],
    )
    def test_retries_on_429s_uses_exponential_back_off_if_no_retry_after_header(
        self,
        _,
        number_attempts_till_success,
        expected_delay,
        config,
        rate_limit_response_mock,
        valid_response_mock,
    ):
        """
        Ensures that if no "Retry-After" header is provided then a
        simple exponential back-off strategy is used.
        This is confirmed by checking that the time taken to successfully
        retrieve a token scales exponentially as the number
        of retries increases.
        """
        refreshing_token = RefreshingToken(api_configuration=config)
        refreshing_token.backoff_base = (
            2  # Use a 2 second base for calculating back-off
        )

        with patch(
            "requests.post",
            side_effect=[
                # Return a 429 on the first attempts
                rate_limit_response_mock
            ]
            * number_attempts_till_success
            +
            # Return a 200 on the last attempt
            [valid_response_mock],
        ):
            start = time()
            # Ensure that we were able to get the token,
            # if not retrying this would be impossible
            assert f"{refreshing_token}" == "mock_access_token"
            elapsed = time() - start
            # Ensure that the elapsed time is as expected
            assert round(elapsed) == expected_delay

    @pytest.mark.parametrize(
        "_, seconds_delay",
        [
            ["Zero", 0],
            ["Positive Int", 5],
            ["Positive Int2", 8]
            # Not possible to have a negative integer returned in this header
        ],
    )
    def test_retries_on_429s_uses_retry_after_header_with_seconds_delay_if_exists(
        self, _, seconds_delay, config, rate_limit_response_mock, valid_response_mock
    ):
        """
        Ensures that if a seconds delay is contained in the "Retry-After" header
        then a retry is attempted after
        the appropriate amount of time.

        :param _: The name of the tests
        :param seconds_delay: The number of seconds to wait before retrying
        """
        refreshing_token = RefreshingToken(api_configuration=config)
        rate_limit_response_mock.headers = {"Retry-After": str(seconds_delay)}

        with patch(
            "requests.post",
            side_effect=[
                # Return a 429 on the first attempt
                rate_limit_response_mock,
                # Return a 200 on the second attempt
                valid_response_mock,
            ],
        ):
            start = time()
            # Ensure that we were able to get the token,
            # if not retrying this would be impossible
            assert f"{refreshing_token}" == "mock_access_token"
            elapsed = time() - start
            # Ensure that the wait was for an appropriate amount of time
            assert int(elapsed) == seconds_delay

    def test_retries_on_429s_uses_retry_after_header_with_http_date_in_future_if_exists(
        self, config, rate_limit_response_mock, valid_response_mock
    ):
        """
        Ensures that if the HTTP Date returned on the "Retry-After" header is x seconds in the future
        it takes approximately x seconds to retry and get the token.
        """
        time_to_wait = 5

        refreshing_token = RefreshingToken(api_configuration=config)
        rate_limit_response_mock.headers = {
            "Retry-After": self.convert_to_http_date(
                datetime.utcnow() + timedelta(seconds=time_to_wait)
            )
        }

        with patch(
            "requests.post",
            side_effect=[
                # Return a 429 on the first attempt
                rate_limit_response_mock,
                # Return a 200 on the second attempt
                valid_response_mock,
            ],
        ):
            start = time()
            # Ensure that we were able to get the token,
            # if not retrying this would be impossible
            assert f"{refreshing_token}" == "mock_access_token"
            elapsed = time() - start
            # Ensure that the wait was for an appropriate amount of time,
            # because the seconds to wait are calculated
            # here instead of being provided directly the delay could be a second less
            assert int(elapsed) >= time_to_wait - 1
            assert int(elapsed) <= time_to_wait

    def test_retries_on_429s_uses_retry_after_header_with_http_date_in_past_if_exists(
        self, config, rate_limit_response_mock, valid_response_mock
    ):
        """
        Ensures that if the HTTP Date returned on the "Retry-After" header is x seconds in the past
        an retry attempt to get the token is made immediately
        """
        refreshing_token = RefreshingToken(api_configuration=config)
        rate_limit_response_mock.headers = {
            "Retry-After": self.convert_to_http_date(
                datetime.utcnow() - timedelta(seconds=5)
            )
        }

        with patch(
            "requests.post",
            side_effect=[
                # Return a 429 on the first attempt
                rate_limit_response_mock,
                # Return a 200 on the second attempt
                valid_response_mock,
            ],
        ):
            start = time()
            # Ensure that we were able to get the token,
            # if not retrying this would be impossible
            assert f"{refreshing_token}" == "mock_access_token"
            elapsed = time() - start
            # Ensure that the wait was essentially no wait before retrying
            assert elapsed < 1

    def test_can_use_id_provider_handler_to_provide_retry_after_header_from_custom_header(
        self, config, rate_limit_response_mock, valid_response_mock
    ):
        """
        Ensures that the "Retry-After" header can be used after
        being created from a custom header using the
        id_provider_response_handler.
        """

        time_to_wait = 5

        def header_creator(id_provider_response):
            rate_limit_reset = id_provider_response.headers.get(
                "X-Rate-Limit-Reset", None
            )

            if rate_limit_reset is not None:
                id_provider_response.headers["Retry-After"] = max(
                    int(rate_limit_reset - datetime.utcnow().timestamp()), 0
                )

        refreshing_token = RefreshingToken(
            api_configuration=config, id_provider_response_handler=header_creator
        )
        rate_limit_response_mock.headers = {
            "X-Rate-Limit-Reset": datetime.utcnow().timestamp() + time_to_wait
        }

        with patch(
            "requests.post",
            side_effect=[
                # Return a 429 on the first attempt
                rate_limit_response_mock,
                # Return a 200 on the second attempt
                valid_response_mock,
            ],
        ):
            start = time()
            # Ensure that we were able to get the token, 
            # if not retrying this would be impossible
            assert f"{refreshing_token}" == "mock_access_token"
            elapsed = time() - start
            # Ensure that the wait was for an appropriate amount of time,
            #  because the seconds to wait are calculated
            # here instead of being provided directly the delay could be a second less
            assert int(elapsed) >= time_to_wait - 1
            assert int(elapsed) <= time_to_wait

    def test_get_access_token_with_special_chars_in_credentials(
        self, config, valid_response_mock
    ):
        # create the problematic credentials
        config.password = "abcd:efg"
        refreshing_token = RefreshingToken(api_configuration=config)

        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = [valid_response_mock]
            # Ensure that we were able to get the token
            assert f"{refreshing_token}" == "mock_access_token"

    def test_get_access_token_with_path_chars_in_credentials(
        self, config, valid_response_mock
    ):
        # create the problematic credentials
        config.password = "some/random/url?key=value"
        config.username = "test"
        config.client_id = "test"
        config.client_secret = "test"
        refreshing_token = RefreshingToken(api_configuration=config)
        with patch("requests.post") as identity_mock:
            identity_mock.side_effect = [valid_response_mock]
            assert f"{refreshing_token}" == "mock_access_token"
            expected_password_encoding = "some%2Frandom%2Furl%3Fkey%3Dvalue"
            expected_request_body = (
                f"grant_type=password&username=test"
                f"&password={expected_password_encoding}&scope=openid client groups \
offline_access"
                f"&client_id=test&client_secret=test"
            )
            assert identity_mock.call_args[1]["data"] == expected_request_body
