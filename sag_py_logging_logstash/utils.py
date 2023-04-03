# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from __future__ import print_function

import sys
import traceback
from datetime import datetime
from itertools import chain, islice


# ----------------------------------------------------------------------
def ichunked(seq, chunksize):
    """Yields items from an iterator in iterable chunks.
    https://stackoverflow.com/a/8998040
    """
    iterable = iter(seq)
    while True:
        chunk_iterable = islice(iterable, chunksize)
        try:
            element = next(chunk_iterable)
        except StopIteration:
            return
        yield list(chain((element,), chunk_iterable))


# ----------------------------------------------------------------------
def safe_log_via_print(log_level, message, *args, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = "{}: {}: {}".format(timestamp, log_level, message)
    print(log_message % args, file=sys.stderr)
    # print stack trace if available
    exc_info = kwargs.get("exc_info", None)
    if exc_info or log_level == "exception":
        if not isinstance(exc_info, tuple):
            exc_info = sys.exc_info()
            stack_trace = "".join(traceback.format_exception(*exc_info))
            print(stack_trace, file=sys.stderr)
