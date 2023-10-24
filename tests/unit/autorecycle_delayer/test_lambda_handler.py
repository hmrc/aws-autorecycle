import unittest

from aws_lambda_context import LambdaContext
from freezegun import freeze_time

from src.autorecycle_delayer.aws_autorecycle_delayer_lambda import lambda_handler


class test_lambda_handler(unittest.TestCase):
    def setUp(self):
        self.context = LambdaContext()
        self.context.aws_request_id = "aws_id"
        self.context.function_name = "function_name"

    @freeze_time("2018-03-22 6:20:00")
    def test_when_time_now_is_greater_than_the_recycle_window(self):
        event = {"component": "payments-sftp", "recycle_window": "04:00:00, 05:30:00"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"time_wait": "2018-03-23T04:00:00+00:00", "wait": True})

    @freeze_time("2018-03-22 11:00:00")
    def test_when_time_now_is_inside_the_recycle_window_with_overnight_window(self):
        event = {"component": "payments-sftp", "recycle_window": "10:45:00, 09:45:00"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"wait": False})

    @freeze_time("2018-03-22 10:00:00")
    def test_when_time_now_is_outside_the_recycle_window_with_large_overnight_window(self):
        event = {"component": "payments-sftp", "recycle_window": "10:45:00, 09:45:00"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"time_wait": "2018-03-22T10:45:00+00:00", "wait": True})

    @freeze_time("2018-03-22 10:00:00")
    def test_when_time_now_is_outside_the_recycle_window_with_small_overnight_window(self):
        event = {"component": "payments-sftp", "recycle_window": "23:00:00, 03:00:00"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"time_wait": "2018-03-22T23:00:00+00:00", "wait": True})

    @freeze_time("2018-03-22 11:00:00")
    def test_when_no_recycle_window_in_event(self):
        event = {"component": "payments-sftp"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"wait": False})

    @freeze_time("2018-03-22 06:00:00")
    def test_when_time_before_recycle_window(self):
        event = {"component": "payments-sftp", "recycle_window": "09:00:00, 10:00:00"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"time_wait": "2018-03-22T09:00:00+00:00", "wait": True})

    @freeze_time("2018-03-22 13:00:00")
    def test_when_time_after_recycle_window(self):
        event = {"component": "payments-sftp", "recycle_window": "09:00:00, 10:00:00"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"time_wait": "2018-03-23T09:00:00+00:00", "wait": True})

    @freeze_time("2018-03-22 9:30:00")
    def test_when_time_within_recycle_window(self):
        event = {"component": "payments-sftp", "recycle_window": "09:00:00, 10:00:00"}
        result = lambda_handler(event, self.context)
        self.assertEqual(result, {"wait": False})
