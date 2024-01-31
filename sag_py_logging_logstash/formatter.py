# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import logging
import socket
import sys
import time
import traceback
import uuid
from datetime import date, datetime

from sag_py_logging_logstash.constants import constants

try:
    import json
except ImportError:
    import simplejson as json  # type: ignore


class LogstashFormatter(logging.Formatter):
    # ----------------------------------------------------------------------
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        message_type="python-logstash",
        tags=None,
        fqdn=False,
        extra_prefix="",
        extra=None,
        ensure_ascii=True,
        metadata=None,
        max_length=500,
    ):
        super().__init__()
        self._message_type = message_type
        self._tags = tags if tags is not None else []
        self._extra_prefix = extra_prefix
        self._extra = extra
        self._format_extra_fields()

        self._ensure_ascii = ensure_ascii
        self._metadata = metadata
        self._max_length = max_length

        self._host = None
        self._logsource = None
        self._program_name = None

        # fetch static information and process related information already
        # as they won't change during lifetime
        self._prefetch_host(fqdn)
        self._prefetch_logsource()
        self._prefetch_program_name()

    # ----------------------------------------------------------------------
    def _prefetch_host(self, fqdn):
        """Override when needed"""
        if fqdn:
            self._host = socket.getfqdn()
        else:
            self._host = socket.gethostname()

    # ----------------------------------------------------------------------
    def _prefetch_logsource(self):
        """Override when needed"""
        self._logsource = self._host

    # ----------------------------------------------------------------------
    def _prefetch_program_name(self):
        """Override when needed"""
        self._program_name = sys.argv[0]

    # ----------------------------------------------------------------------
    def format(self, record):
        message = {
            "@timestamp": self._format_timestamp(record.created),
            "@version": "1",
            "host": self._host,
            "level": record.levelname,
            "logsource": self._logsource,
            "message": self._shorten(record.getMessage()),
            "message_template": self._shorten(record.msg),
            "path": record.pathname,
            "process_id": record.process,
            "program": self._program_name,
            "type": self._message_type,
            "func_name": record.funcName,
            "line": record.lineno,
            "logger_name": record.name,
            "thread_name": record.threadName,
        }
        if self._metadata:
            message["@metadata"] = self._metadata
        if self._tags:
            message["tags"] = self._tags

        if record.exc_info:
            message.update({"stack_trace": self._format_exception(record.exc_info)})

        # record fields
        dynamic_extra_fields = self._get_record_fields(record)
        message.update(dynamic_extra_fields)
        if self._extra:
            message.update(self._extra)

        return self._serialize(message)

    # ----------------------------------------------------------------------
    def _format_timestamp(self, time_):
        tstamp = datetime.utcfromtimestamp(time_)
        return tstamp.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (tstamp.microsecond / 1000) + "Z"

    # ----------------------------------------------------------------------
    def _get_record_fields(self, record):
        def value_repr(value):
            easy_types = (type(None), bool, str, int, float)

            if isinstance(value, dict):
                return {k: value_repr(v) for k, v in value.items()}
            elif isinstance(value, (tuple, list)):
                return [value_repr(v) for v in value]
            elif isinstance(value, (datetime, date)):
                return self._format_timestamp(time.mktime(value.timetuple()))
            elif isinstance(value, uuid.UUID):
                return value.hex
            elif isinstance(value, easy_types):
                return value
            else:
                return repr(value)

        fields = {}

        for key, value in record.__dict__.items():
            if key not in constants.FORMATTER_RECORD_FIELD_SKIP_LIST:
                if self._extra_prefix and key not in constants.FORMATTER_LOGSTASH_MESSAGE_FIELD_LIST:
                    key = self._extra_prefix + "." + key
                fields[key] = value_repr(value)
        return fields

    # ----------------------------------------------------------------------
    def _format_extra_fields(self):
        # static extra fields
        if self._extra:
            if self._extra_prefix:
                extra_fields_with_prefix = {}
                for key in self._extra:
                    extra_fields_with_prefix[self._extra_prefix + "." + key] = self._extra[key]
                self._extra = extra_fields_with_prefix

    # ----------------------------------------------------------------------
    def _format_exception(self, exc_info):
        if isinstance(exc_info, tuple):
            stack_trace = "".join(traceback.format_exception(*exc_info))
        elif exc_info:
            stack_trace = "".join(traceback.format_stack())
        else:
            stack_trace = ""
        return stack_trace

    # ----------------------------------------------------------------------
    def _serialize(self, message):
        return json.dumps(message, ensure_ascii=self._ensure_ascii)

    # ----------------------------------------------------------------------
    def _shorten(self, message):
        notice = "\n[MESSAGE SHORTENED]\n"
        offset = len(notice) % 2  # needed when 'notice' has an odd number of characters
        index = (self._max_length // 2) - len(notice) // 2 - offset
        if len(message) > self._max_length:
            return message[:index] + notice + message[-index:]
        return message
