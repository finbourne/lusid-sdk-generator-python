import pytest
from TO_BE_REPLACED.configuration import Configuration


def test_errors_if_invalid_timeouts_set():
    configuration = Configuration()
    assert configuration.timeouts != None
    with pytest.raises(TypeError) as e:
        configuration.timeouts = None
    assert str(e.value) == "timeouts must be type Timeouts but type '<class 'NoneType'>' used"

def test_errors_if_invalid_rate_limit_retries_type_set():
    configuration = Configuration()
    assert configuration.rate_limit_retries != None
    with pytest.raises(TypeError) as e:
        configuration.rate_limit_retries = None
    assert str(e.value) == "rate_limit_retries must be type int but type '<class 'NoneType'>' used"

def test_errors_if_invalid_rate_limit_retries_value_set():
    configuration = Configuration()
    assert configuration.rate_limit_retries != None
    with pytest.raises(ValueError) as e:
        configuration.rate_limit_retries = -1
    assert str(e.value) == "rate_limit_retries must be greater than or equal to zero but was '-1'"