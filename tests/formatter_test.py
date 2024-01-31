# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.
import logging
import os
import sys
import unittest
from ast import literal_eval
from logging import FileHandler, makeLogRecord

from sag_py_logging_logstash.formatter import LogstashFormatter

VERY_LONG_MESSAGE = "long message" * 100


class ExceptionCatchingFileHandler(FileHandler):
    def __init__(self, *args, **kwargs):
        FileHandler.__init__(self, *args, **kwargs)
        self.exception = None

    def handleError(self, record):
        self.exception = sys.exc_info()


class LogstashFormatterTest(unittest.TestCase):
    def test_format(self):
        file_handler = ExceptionCatchingFileHandler(os.devnull)
        file_handler.setFormatter(LogstashFormatter())
        file_handler.emit(makeLogRecord({"msg": "тест"}))
        file_handler.close()

        self.assertIsNone(file_handler.exception)

    def test_long_message(self):
        # Arrange
        formatter = LogstashFormatter()
        long_message = "a" * 1000
        record = logging.LogRecord(
            name="example_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=10,
            msg=long_message,
            args=(),
            exc_info=None,
            func="example_function",
            sinfo=None,
        )

        # Act
        formatted_message = formatter.format(record)
        # Assert
        self.assertTrue(len(literal_eval(formatted_message)["message"]) <= formatter._max_length)
        self.assertTrue(len(literal_eval(formatted_message)["message_template"]) <= formatter._max_length)


if __name__ == "__main__":
    unittest.main()
