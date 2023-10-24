from unittest.mock import Mock

import pytest

from src.mongo_recycler.utils.poll import poll, run_until


def test_poll_exits_after_max_failures():
    error = Exception("whoops")
    always_fails = Mock(side_effect=error)

    with pytest.raises(Exception) as e_info:
        poll(always_fails)

    assert e_info.value == error
    assert always_fails.call_count == 50


def test_poll_stops_after_success():
    never_fails = Mock()
    poll(never_fails)

    assert never_fails.call_count == 1


def test_poll_iters_depends_on_max_iters():
    error = Exception("whoops")
    always_fails = Mock(side_effect=error)

    max_iters = 10

    with pytest.raises(Exception) as e_info:
        poll(always_fails, max_iters=max_iters)

    assert e_info.value == error
    assert always_fails.call_count == 10


def test_run_until_fn_returns_sentinel():
    fn = Mock()

    fn.return_value = True
    run_until(fn, True)
    assert fn.call_count == 1


def test_run_until_fn_does_not_return_sentinel():
    fn = Mock()

    fn.return_value = False
    run_until(fn, True)
    assert fn.call_count == 50


def test_run_until_fn_does_not_return_sentinel_n_iters():
    fn = Mock()

    fn.return_value = False
    run_until(fn, True, max_iters=10)
    assert fn.call_count == 10


def test_run_until_raises():
    fn = Mock()
    fn.side_effect = Exception
    with pytest.raises(Exception):
        run_until(fn, True)
    assert fn.call_count == 1
