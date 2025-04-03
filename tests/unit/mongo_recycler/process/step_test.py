import unittest
from unittest.mock import patch

import boto3
import pytest
from moto import mock_dynamodb
from src.mongo_recycler.models.decision import (
    Decision,
    done,
    step_down_and_recycle_primary,
)
from src.mongo_recycler.models.instances import Instance
from src.mongo_recycler.process.pre_step_checks import MongoReplicaSetMismatch
from src.mongo_recycler.process.step import (
    increment_counter,
    is_first_run,
    lambda_handler,
    step,
)


class LaunchException(Exception):
    pass


@patch("src.mongo_recycler.connectors.mongo.Mongo")
@patch("src.mongo_recycler.connectors.aws.AWS")
@patch("src.mongo_recycler.process.replica_set_health.ReplicaSetHealth")
@patch("src.mongo_recycler.process.pre_step_checks.get_ami_and_check_all_amis_match")
@patch("src.mongo_recycler.process.execute.execute_action")
def test_step_function_exits_if_launch_config_ami_doesnt_match(mock_execute, mock_assert, *mocks):
    mock_assert.side_effect = LaunchException()

    with pytest.raises(LaunchException):
        step("protected")

    mock_execute.assert_not_called()


@patch("src.mongo_recycler.connectors.mongo.Mongo")
@patch("src.mongo_recycler.connectors.aws.AWS")
@patch("src.mongo_recycler.process.replica_set_health.ReplicaSetHealth")
@patch("src.mongo_recycler.process.instances.fetch_replica_set_status")
@patch("src.mongo_recycler.process.pre_step_checks.get_ami_and_check_all_amis_match")
@patch("src.mongo_recycler.process.pre_step_checks.assert_all_nodes_in_same_replica_set")
@patch("src.mongo_recycler.process.execute.execute_action")
def test_step_function_exits_if_replica_sets_dont_match(mock_execute, mock_assert_replica_set, *mocks):
    mock_assert_replica_set.side_effect = MongoReplicaSetMismatch

    with pytest.raises(MongoReplicaSetMismatch):
        step("protected")

    mock_execute.assert_not_called()


@patch("src.mongo_recycler.process.step.Mongo")
@patch("src.mongo_recycler.process.step.AWS")
@patch("src.mongo_recycler.process.replica_set_health.ReplicaSetHealth")
@patch("src.mongo_recycler.process.execute.execute_action")
@patch("src.mongo_recycler.process.decision.decide_on_action")
@patch("src.mongo_recycler.process.instances.fetch_replica_set_status")
@patch("src.mongo_recycler.process.pre_step_checks.assert_amis_match_and_get_ami")
@patch("src.mongo_recycler.process.pre_step_checks.assert_all_nodes_in_same_replica_set")
def test_step_function_normal_execution(
    mock_assert_node_check,
    mock_assert_ami_match,
    mock_fetch_replica,
    mock_decide,
    mock_execute,
    mock_replica_set_health,
    mock_aws,
    mock_mongo,
):
    replica_set_status = [Instance(None, None, None, None, None)]
    decision = step_down_and_recycle_primary(replica_set_status[0])

    mock_fetch_replica.return_value = replica_set_status
    mock_decide.return_value = decision
    mock_execute.return_value = None

    result = step("protected_mongo_a")

    mock_aws.assert_called_with("protected_mongo_a")
    mock_replica_set_health.assert_called_with(mock_aws(), mock_mongo())

    mock_assert_node_check.assert_called_with(replica_set_status)
    mock_fetch_replica.assert_called_with(mock_aws(), mock_mongo())
    mock_decide.assert_called_with(replica_set_status, mock_assert_ami_match.return_value)
    mock_execute.assert_called_with(decision, mock_aws(), mock_mongo(), mock_replica_set_health())

    assert result == decision


def test_increment_counter():
    test_event = {"component": "test-component"}
    test_result = increment_counter(test_event)
    expected_result = {"component": "test-component", "counter": 1}

    assert test_result == expected_result

    test_event = {"component": "test-component", "counter": 2}
    test_result = increment_counter(test_event)
    expected_result = {"component": "test-component", "counter": 3}

    assert test_result == expected_result


def test_is_first_run():
    test_event = {"component": "test-component"}
    test_result = is_first_run(test_event)

    assert test_result


def test_is_not_first_run():
    test_event = {"component": "test-component", "counter": 3}
    test_result = is_first_run(test_event)

    assert not test_result


@patch("requests.post")
def test_lambda_handler_raises_exception_without_silencing_alerts(mock_requests):
    event = {"component": "test-component"}
    mock_requests.return_value = None

    with pytest.raises(Exception):
        assert not lambda_handler(event, "_")


@patch("requests.post")
@patch("src.mongo_recycler.process.step.step")
@patch("src.mongo_recycler.process.step.json_logger_config")
@patch("boto3.resource")
def test_lambda_handler_runs(mock_boto3, mock_logger, mock_run, mock_requests_post):
    event = {
        "component": "test-component",
        "message_content": {
            "color": "good",
            "text": "Autorecycling has successfully initiated",
        },
        "status": "success",
    }
    test_lambda_handler_result = lambda_handler(event, "_")
    mock_logger.assert_called_with(event, "_")
    mock_run.assert_called_with("test-component")

    assert test_lambda_handler_result


@patch("requests.post")
@patch("src.mongo_recycler.process.step.step")
@patch("src.mongo_recycler.process.step.json_logger_config")
def test_lambda_handler_runs_successfully(mock_logger, mock_run, mock_requests_post):
    event = {
        "component": "test-component",
        "message_content": {
            "color": "good",
            "text": "Autorecycling has successfully initiated",
        },
        "counter": 3,
        "status": "success",
    }

    mock_run.return_value = done()
    test_lambda_handler_result = lambda_handler(event, "_")
    mock_logger.assert_called_with(event, "_")
    mock_run.assert_called_with("test-component")

    assert (
        event["message_content"]["text"] == "Autorecycling has successfully completed. " "Recycled 3 mongo instances."
    )

    assert test_lambda_handler_result


@patch("requests.post")
@patch("src.mongo_recycler.process.step.step")
@patch("src.mongo_recycler.process.step.json_logger_config")
@patch("boto3.resource")
def test_lambda_handler_returns_no_instance_recycled(mock_boto3, mock_logger, mock_run, mock_requests_post):
    event = {
        "component": "test-component",
        "message_content": {
            "color": "good",
            "text": "Autorecycling has successfully initiated",
        },
        "status": "success",
    }

    mock_run.return_value = done()
    test_lambda_handler_result = lambda_handler(event, "_")
    mock_logger.assert_called_with(event, "_")
    mock_run.assert_called_with("test-component")

    assert event["message_content"]["text"] == "No instances were recycled, because there was nothing to do"

    assert test_lambda_handler_result
