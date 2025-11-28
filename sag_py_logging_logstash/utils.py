# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

from __future__ import print_function

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
