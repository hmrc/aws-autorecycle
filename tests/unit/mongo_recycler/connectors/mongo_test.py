import json
import ssl
from unittest.mock import Mock, patch

import pytest
from pymongo.errors import AutoReconnect
from tenacity.wait import wait_none

import src.mongo_recycler.connectors.mongo as mongo


def test_state_string_from_status():
    assert mongo.state_string_from_status({"myState": 0}) == "STARTUP"
    assert mongo.state_string_from_status({"myState": 1}) == "PRIMARY"
    assert mongo.state_string_from_status({"myState": 2}) == "SECONDARY"
    assert mongo.state_string_from_status({"myState": 3}) == "RECOVERING"
    assert mongo.state_string_from_status({"myState": 4}) == "STARTUP2"
    assert mongo.state_string_from_status({"myState": 5}) == "UNKNOWN"
    assert mongo.state_string_from_status({"myState": 6}) == "ARBITER"
    assert mongo.state_string_from_status({"myState": 7}) == "DOWN"
    assert mongo.state_string_from_status({"myState": 8}) == "ROLLBACK"
    assert mongo.state_string_from_status({"myState": 9}) == "REMOVED"


def test_state_string_from_status_fails_if_myState_cannot_be_found():
    with pytest.raises(mongo.InstanceStateNotFound):
        mongo.state_string_from_status({})


def test_node_details():
    instance_status = {"myState": 2, "ok": 1.0, "set": "int-protected-1"}

    expected_result = mongo.NodeDetails("SECONDARY", "int-protected-1")

    result = mongo.node_details(instance_status)
    assert result == expected_result


def test_node_details_unsuccessful():
    instance_status = {"ok": 0}

    with pytest.raises(mongo.MongoRequestFailed):
        mongo.node_details(instance_status)


@patch("pymongo.MongoClient")
def test_get_node_details(mock_mongo_client):
    instance_status = {"myState": 2, "ok": 1.0, "set": "int-protected-1"}

    mock_mongo_client().admin.command.return_value = instance_status

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    expected_result = mongo.NodeDetails("SECONDARY", "int-protected-1")
    result = mongo_instance.get_node_details("1.1.1.1")

    assert result == expected_result


@patch("pymongo.MongoClient")
def test_replica_set_status(mock_mongo_client):
    instance_status = {"myState": 2, "ok": 1.0, "set": "int-protected-1"}

    mock_mongo_client().admin.command.return_value = instance_status

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    assert mongo_instance.replica_set_status("1.1.1.1") == instance_status

    mock_mongo_client.assert_called_with(
        "1.1.1.1",
        authMechanism="MONGODB-AWS",
        serverSelectionTimeoutMS=5000,
        ssl=True,
        tlsAllowInvalidCertificates=True,
    )


@patch("src.mongo_recycler.connectors.mongo.Mongo._connect")
def test_step_down_requests_primary_step_down_then_catches_connection_error(
    mock_mongo_client,
):
    ip_address = "1.2.3.4"

    mock_mongo_client().admin.command.side_effect = AutoReconnect

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    mongo_instance.step_down(ip_address)

    mock_mongo_client().admin.command.assert_called_with("replSetStepDown", 100)


@patch("pymongo.MongoClient")
def test_step_down_throws_on_any_other_error_but_connection(mock_mongo_client):
    ip_address = "1.2.3.4"

    mock_mongo_client().admin.command.side_effect = Exception

    mongo_instance = mongo.Mongo("test_cluster_mongo_a")

    with pytest.raises(Exception):
        mongo_instance.step_down(ip_address)


@patch("pymongo.MongoClient")
def test_connect_with_auth(mock_mongo_client):
    mongo_instance = mongo.Mongo("test_cluster_mongo_a")

    mongo_instance._connect("")
    mock_mongo_client.assert_called_with(
        "",
        serverSelectionTimeoutMS=5000,
        ssl=True,
        tlsAllowInvalidCertificates=True,
        authMechanism="MONGODB-AWS",
    )


@patch("pymongo.MongoClient")
def test_connect_retries(mock_mongo_client):
    mongo_instance = mongo.Mongo("test_cluster_mongo_a")

    class TemporaryException(Exception):
        pass

    mock_mongo_client.side_effect = [
        TemporaryException,
        TemporaryException,
        TemporaryException,
        Mock(),
    ]

    try:
        mongo_instance._connect("")
    except TemporaryException:
        assert False, "_connect wasn't retried enough times"


@patch("src.mongo_recycler.connectors.mongo.Mongo._connect")
def test_if_settings_match_there_is_no_reconfig(mock_mongo_client):
    mock_mongo_client().admin.command.return_value = {"config": {"version": 1, "settings": {"chainingAllowed": True}}}
    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    config = mongo_instance.set_chaining("foo_connection_string", True)
    mock_mongo_client().admin.command.assert_called_once_with("replSetGetConfig")
    assert config["settings"]["chainingAllowed"]


@patch("src.mongo_recycler.connectors.mongo.Mongo._connect")
def test_when_settings_change_there_is_a_reconfig(mock_mongo_client):
    mock_mongo_client().admin.command.return_value = {"config": {"version": 1, "settings": {"chainingAllowed": True}}}
    mongo_instance = mongo.Mongo("test_cluster_mongo_a")
    config = mongo_instance.set_chaining("foo_connection_string", False)
    mock_mongo_client().admin.command.assert_called_with({"replSetReconfig": config})
    assert config["settings"]["chainingAllowed"] is False
    assert config["version"] == 2
