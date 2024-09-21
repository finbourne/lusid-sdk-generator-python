from TO_BE_REPLACED.configuration import Timeouts
import pytest


def test_timeouts_does_not_allow_incorrect_type_for_total():
    with pytest.raises(TypeError) as e:
        Timeouts("not-an-int", 0, 0)
    assert str(e.value) == "total_timeout_ms must be type int but type '<class 'str'>' used"

def test_timeouts_does_not_allow_incorrect_type_for_connect():
    with pytest.raises(TypeError) as e:
        Timeouts(0, "not-an-int", 0)
    assert str(e.value) == "connect_timeout_ms must be type int but type '<class 'str'>' used"

def test_timeouts_does_not_allow_incorrect_type_for_read():
    with pytest.raises(TypeError) as e:
        Timeouts(0, 0, "not-an-int")
    assert str(e.value) == "read_timeout_ms must be type int but type '<class 'str'>' used"

def test_timeouts_does_not_allow_incorrect_value_for_total():
    with pytest.raises(ValueError) as e:
        Timeouts(-1, 0, 0)
    assert str(e.value) == "total_timeout_ms must be an integer greater than or equal to zero"

def test_timeouts_does_not_allow_incorrect_value_for_connect():
    with pytest.raises(ValueError) as e:
        Timeouts(0, -1, 0)
    assert str(e.value) == "connect_timeout_ms must be an integer greater than or equal to zero"

def test_timeouts_does_not_allow_incorrect_value_for_read():
    with pytest.raises(ValueError) as e:
        Timeouts(0, 0, -1)
    assert str(e.value) == "read_timeout_ms must be an integer greater than or equal to zero"

def test_timeouts_set_correctly():
    timeouts = Timeouts(3000, 2000, 1000)
    assert timeouts.total_timeout_ms == 3000
    assert timeouts.connect_timeout_ms == 2000
    assert timeouts.read_timeout_ms == 1000