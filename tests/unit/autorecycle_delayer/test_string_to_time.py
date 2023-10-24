import datetime
import unittest

from src.autorecycle_delayer.aws_autorecycle_delayer_lambda import str_to_time


class String_to_time(unittest.TestCase):
    def test_with_valid_string(self):
        "Test a valid string can be converted to datetime object"

        valid_result = datetime.time(10, 00, 00)
        result = str_to_time("10:00:00")
        self.assertEqual(result, valid_result)

    def test_with_invalid_string(self):
        "Test an invalid time string throw an exception"
        with self.assertRaises(ValueError):
            str_to_time("10.00.00")

    def test_with_invalid_tinme_string(self):
        "Test an invalid time string with too many digits"
        with self.assertRaises(ValueError):
            str_to_time("111:000:000")
