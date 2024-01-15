import logging
import os
import re
import ssl
from collections import namedtuple
from typing import Any

import pymongo
from aws_get_vault_object import get_credentials
from pymongo.errors import AutoReconnect, ConnectionFailure, OperationFailure
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.before import before_log

logger = logging.getLogger(__name__)


class InstanceStateNotFound(Exception):
    pass


class MongoRequestFailed(Exception):
    pass


NodeDetails = namedtuple("NodeDetails", ["node_state", "replica_set_name"])


def state_string_from_status(instance_status: Any) -> Any:
    states = [
        "STARTUP",
        "PRIMARY",
        "SECONDARY",
        "RECOVERING",
        "STARTUP2",
        "UNKNOWN",
        "ARBITER",
        "DOWN",
        "ROLLBACK",
        "REMOVED",
    ]
    try:
        return states[instance_status["myState"]]
    except KeyError:
        raise InstanceStateNotFound


def node_details(instance_status: Any) -> NodeDetails:
    if instance_status["ok"] != 1:
        raise MongoRequestFailed

    return NodeDetails(state_string_from_status(instance_status), instance_status["set"])


class Mongo:
    def __init__(self, component: str) -> None:
        self.cluster_name = re.sub(r"_mongo(?:_[abc])?$", "", component)

    @retry(wait=wait_exponential(min=0.1, max=1), stop=stop_after_attempt(10), reraise=True)
    def _connect(self, connection_string: str) -> pymongo.MongoClient:
        creds = self.get_credentials_from_vault()

        logger.info(f"Connecting to Mongo with connection string [{connection_string}]")

        connection_object: pymongo.MongoClient = pymongo.MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            username=creds["username"],
            password=creds["password"],
            authMechanism="SCRAM-SHA-1",
        )

        connection_object.admin.command("replSetGetStatus")

        return connection_object

    def get_credentials_from_vault(self) -> Any:
        VAULT_URL = os.getenv("VAULT_URL")
        VAULT_ROLE_PATH = f"database/creds/autorecycle_{self.cluster_name}"
        CREDS_FILE = "/tmp/.creds_file"  # nosec exclude from bandit security checks
        CA_CERT = os.getenv("CA_CERT")
        creds = get_credentials(VAULT_URL, VAULT_ROLE_PATH, CREDS_FILE, refresh=True, ca_cert=CA_CERT)["data"]
        return creds

    def replica_set_status(self, connection_string: str) -> Any:
        client = self._connect(connection_string)
        return client.admin.command("replSetGetStatus")

    def replication_status(self, connection_string: str) -> Any:
        client = self._connect(connection_string)
        return client.admin.command("printSecondaryReplicationInfo")

    def get_node_details(self, ip_address: str) -> Any:
        client = self._connect(ip_address)
        instance_status = client.admin.command("replSetGetStatus")
        details = node_details(instance_status)

        return details

    def step_down(self, ip_address: str) -> None:
        client = self._connect(ip_address)
        try:
            client.admin.command("replSetStepDown", 100)
        except AutoReconnect:
            pass
