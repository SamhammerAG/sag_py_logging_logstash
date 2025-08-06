# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import datetime
import unittest

from sag_py_logging_logstash.constants import constants
from sag_py_logging_logstash.memory_cache import MemoryCache
from sag_py_logging_logstash.safe_logger import SafeLogger

# pylint: disable=protected-access


class MemoryCacheTest(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_add_event(self):
        safe_logger = SafeLogger()
        cache = MemoryCache(safe_logger, {})
        cache.add_event("message")
        self.assertEqual(len(cache._cache), 1)
        event = list(cache._cache.values())[0]
        self.assertEqual(event["event_text"], "message")
        self.assertEqual(event["pending_delete"], False)

    # ----------------------------------------------------------------------
    def test_get_queued_events(self):
        safe_logger = SafeLogger()
        cache = MemoryCache(safe_logger, {"id1": {"pending_delete": True}, "id2": {"pending_delete": False}})
        self.assertEqual(len(cache.get_queued_events()), 1)

    # ----------------------------------------------------------------------
    def test_get_queued_events_batch_size(self):
        constants.QUEUED_EVENTS_BATCH_SIZE = 3
        safe_logger = SafeLogger()

        cache = MemoryCache(
            safe_logger,
            {
                "id1": {"pending_delete": True},
                "id2": {"pending_delete": False},
                "id3": {"pending_delete": False},
                "id4": {"pending_delete": False},
                "id5": {"pending_delete": False},
                "id6": {"pending_delete": False},
            },
        )
        events = cache.get_queued_events()
        # expect only 3 events according to QUEUED_EVENTS_BATCH_SIZE
        self.assertEqual(len(events), constants.QUEUED_EVENTS_BATCH_SIZE)

    # ----------------------------------------------------------------------
    def test_get_queued_events_batch_size_underrun(self):
        constants.QUEUED_EVENTS_BATCH_SIZE = 3
        safe_logger = SafeLogger()

        cache = MemoryCache(safe_logger, {"id1": {"pending_delete": True}, "id2": {"pending_delete": False}})
        events = cache.get_queued_events()
        # expect only 1 event as there are no more available
        self.assertEqual(len(events), 1)

    # ----------------------------------------------------------------------
    def test_get_queued_events_pending_delete_check(self):
        safe_logger = SafeLogger()
        cache = MemoryCache(safe_logger, {"id1": {"pending_delete": False}})
        queued_events = cache.get_queued_events()
        self.assertEqual(len(queued_events), 1)
        self.assertTrue(queued_events[0])

    # ----------------------------------------------------------------------
    def test_requeue_queued_events(self):
        safe_logger = SafeLogger()
        cache = MemoryCache(safe_logger, {"id1": {"pending_delete": True}})
        self.assertEqual(len(cache.get_queued_events()), 0)
        cache.requeue_queued_events([{"id": "id1"}])
        self.assertEqual(len(cache.get_queued_events()), 1)

    # ----------------------------------------------------------------------
    def test_delete_queued_events(self):
        safe_logger = SafeLogger()
        cache = MemoryCache(
            safe_logger, {"id1": {"pending_delete": True, "id": "id1"}, "id2": {"pending_delete": False, "id": "id2"}}
        )
        cache.delete_queued_events()
        self.assertEqual(len(cache._cache), 1)

    # ----------------------------------------------------------------------
    def test_expire_events(self):
        safe_logger = SafeLogger()
        cache = MemoryCache(
            safe_logger,
            {
                "id1": {"pending_delete": False, "id": "id1", "entry_date": datetime.datetime.fromtimestamp(0)},
                "id2": {"pending_delete": False, "id": "id2", "entry_date": datetime.datetime.now()},
            },
            event_ttl=100,
        )
        cache.expire_events()
        self.assertEqual(len(cache._cache), 1)
