import json
import os
import unittest

from mock import patch

from src.autorecycle_invoke_stepfunctions.get_account_details import (
    AccountIdNotFound,
    ChannelNotFound,
    get_account_id,
    get_slack_channel,
)


class Get_account_id_from_env(unittest.TestCase):
    @patch.dict(os.environ, {"ACCOUNT_ID": "1234567890"})
    def test_with_environment_variable_set(self):
        """
        When the environment variable is set and the result returns the same value
        """
        result = get_account_id()
        self.assertEqual(result, "1234567890")

    def test_with_environment_variable_missing(self):
        """
        When the environment variable is not set and an exception is raised
        """
        with self.assertRaises(KeyError):
            get_account_id()


class Get_slack_channel_from_env(unittest.TestCase):
    @patch.dict(os.environ, {"SLACK_CHANNEL": "event-test-recycle"})
    def test_with_environment_variable_set(self):
        """
        When the environment variable is set and the result returns the same value
        """
        result = get_slack_channel()
        self.assertEqual(result, "event-test-recycle")

    def test_with_environment_variable_missing(self):
        """
        When the environment variable is missing and an exception is raised
        """
        with self.assertRaises(KeyError):
            get_slack_channel()
