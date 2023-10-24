from unittest.mock import Mock, patch

import pytest
from requests import ConnectionError
from tenacity import RetryError, stop_after_attempt

from src.mongo_recycler.connectors.sensu import _post_to_sensu, silence_sensu_alerts


@patch("requests.post")
def test_silence_sensu_alert(mock_post):
    expected_endpoint = "http://sensu:4567/silenced"

    expected_payload = {
        "check": "infra_check_mongo_replica_set_health_protected_auth_critical_aggregates",
        "expire": 60,
    }

    expected_headers = {"Content-Type": "application/json"}

    mocked_response = Mock()
    mocked_response.status_code = 201
    mock_post.return_value = mocked_response

    silence_sensu_alerts("protected_auth_mongo", 60)
    mock_post.assert_called_with(expected_endpoint, json=expected_payload, headers=expected_headers)


@patch("requests.post")
@patch("src.mongo_recycler.connectors.sensu.logger.info")
def test_silence_return_status_success(mock_logger, mock_post):
    mocked_response = Mock()
    mocked_response.status_code = 201
    mock_post.return_value = mocked_response
    silence_sensu_alerts("protected_auth_mongo_b", 60)
    mock_logger.assert_any_call(
        "Sensu check silenced successfully: infra_check_mongo_replica_set_health_protected_auth_critical_aggregates"
    )
    mock_logger.assert_any_call(
        "Sensu check silenced successfully: infra_check_mongo_replica_set_health_protected_auth_warning_aggregates"
    )


@patch("requests.post")
@patch("src.mongo_recycler.connectors.sensu.logger.warning")
def test_silence_alert_logs_a_failure_status(mock_logger, mock_post):
    mocked_response_failure = Mock()
    mocked_response_failure.status_code = 501
    _post_to_sensu.retry.sleep = Mock()

    mock_post.return_value = mocked_response_failure
    silence_sensu_alerts("protected_auth_mongo_c", 60)
    mock_logger.assert_any_call(
        "Sensu silencing failed for: infra_check_mongo_replica_set_health_protected_auth_critical_aggregates"
    )
    mock_logger.assert_any_call(
        "Sensu silencing failed for: infra_check_mongo_replica_set_health_protected_auth_warning_aggregates"
    )

    assert mock_post.call_count == 2


@patch("src.mongo_recycler.connectors.sensu.logger.info")
@patch("requests.post")
def test_silence_alert_retries_after_connect_error_exception_is_raised(mock_post, mock_logger):
    mocked_response = Mock()
    mocked_response.status_code = 201
    mock_post.side_effect = [
        ConnectionError,
        ConnectionError,
        mocked_response,
        mocked_response,
    ]

    # Patch the retry decorator so it stops after 2 attempts
    _post_to_sensu.retry.stop = stop_after_attempt(4)

    # Patch the retry decorator wait time so don't have to wait
    _post_to_sensu.retry.sleep = Mock()

    silence_sensu_alerts("protected_auth_mongo", 60)

    mock_logger.assert_any_call(
        "Sensu check silenced successfully: infra_check_mongo_replica_set_health_protected_auth_critical_aggregates"
    )
    mock_logger.assert_any_call(
        "Sensu check silenced successfully: infra_check_mongo_replica_set_health_protected_auth_warning_aggregates"
    )

    # We call request.post twice in each attempt for both alert types.
    assert mock_post.call_count == 4


@patch("requests.post")
def test_silencing_alert_raises_exception_after_multiple_connect_errors(mock_post):
    mock_post.side_effect = [
        ConnectionError,
        ConnectionError,
        ConnectionError,
        ConnectionError,
        ConnectionError,
        ConnectionError,
        ConnectionError,
        ConnectionError,
    ]
    with pytest.raises(RetryError):
        _post_to_sensu.retry.stop = stop_after_attempt(8)
        _post_to_sensu.retry.sleep = Mock()
        silence_sensu_alerts("protected_auth_mongo", 60)

    assert mock_post.call_count == 8
