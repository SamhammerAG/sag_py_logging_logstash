# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import os
import sys
import unittest
from logging import FileHandler, makeLogRecord

from sag_py_logging_logstash.formatter import LogstashFormatter


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


if __name__ == "__main__":
    unittest.main()
