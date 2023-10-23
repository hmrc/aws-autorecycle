#!/usr/bin/env python
import logging
import os

logger = logging.getLogger(__name__)


class AccountIdNotFound(Exception):
    pass


class ChannelNotFound(Exception):
    pass


def get_account_id() -> str:
    try:
        return os.environ["ACCOUNT_ID"]
    except KeyError as err:
        logger.info("Account ID environment variable missing.")
        raise err


def get_slack_channel() -> str:
    try:
        slack_channel = os.environ["SLACK_CHANNEL"]
        logger.info("Notification channel is set to %s", slack_channel)
        return slack_channel
    except KeyError as err:
        logger.info("Slack Channel variable missing.")
        raise err
