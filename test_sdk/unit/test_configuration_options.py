import pytest

from TO_BE_REPLACED.extensions.configuration_options import ConfigurationOptions


def test_errors_if_invalid_total_timeout_type():
    opts = ConfigurationOptions()
    with pytest.raises(TypeError) as e:
        opts.total_timeout_ms = "not-an-int"
    assert str(e.value) == "total_timeout_ms must be type int but type '<class 'str'>' used"

def test_errors_if_invalid_connect_timeout_type():
    opts = ConfigurationOptions()
    with pytest.raises(TypeError) as e:
        opts.connect_timeout_ms = "not-an-int"
    assert str(e.value) == "connect_timeout_ms must be type int but type '<class 'str'>' used"

def test_errors_if_invalid_read_timeout_type():
    opts = ConfigurationOptions()
    with pytest.raises(TypeError) as e:
        opts.read_timeout_ms = "not-an-int"
    assert str(e.value) == "read_timeout_ms must be type int but type '<class 'str'>' used"

def test_errors_if_invalid_rate_limit_retries_type():
    opts = ConfigurationOptions()
    with pytest.raises(TypeError) as e:
        opts.rate_limit_retries = "not-an-int"
    assert str(e.value) == "rate_limit_retries must be type int but type '<class 'str'>' used"

def test_errors_if_invalid_total_timeout_value():
    opts = ConfigurationOptions()
    with pytest.raises(ValueError) as e:
        opts.total_timeout_ms = -1
    assert str(e.value) == "total_timeout_ms must be an integer greater than or equal to zero"

def test_errors_if_invalid_connect_timeout_value():
    opts = ConfigurationOptions()
    with pytest.raises(ValueError) as e:
        opts.connect_timeout_ms = -1
    assert str(e.value) == "connect_timeout_ms must be an integer greater than or equal to zero"

def test_errors_if_invalid_read_timeout_value():
    opts = ConfigurationOptions()
    with pytest.raises(ValueError) as e:
        opts.read_timeout_ms = -1
    assert str(e.value) == "read_timeout_ms must be an integer greater than or equal to zero"

def test_errors_if_invalid_rate_limit_retries_value():
    opts = ConfigurationOptions()
    with pytest.raises(ValueError) as e:
        opts.rate_limit_retries = -1
    assert str(e.value) == "rate_limit_retries must be an integer greater than or equal to zero"

def test_correctly_sets_values():
    opts = ConfigurationOptions(
        total_timeout_ms=3001,
        connect_timeout_ms=2001,
        rate_limit_retries=1001,
        read_timeout_ms=4
    )
    assert opts.total_timeout_ms == 3001
    assert opts.connect_timeout_ms == 2001
    assert opts.rate_limit_retries == 1001
    assert opts.read_timeout_ms == 4