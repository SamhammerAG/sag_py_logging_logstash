# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the MIT license.  See the LICENSE file for details.

import json
import logging
from abc import ABC, abstractmethod
from typing import Iterator, Union

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class TimeoutNotSet:
    pass


class Transport(ABC):
    """The :class:`Transport <Transport>` is the abstract base class of
    all transport protocols.

    :param host: The name of the host.
    :type host: str
    :param port: The TCP/UDP port.
    :type port: int
    :param timeout: The connection timeout.
    :type timeout: None or float
    :param ssl_enable: Activates TLS.
    :type ssl_enable: bool
    :param use_logging: Use logging for debugging.
    :type use_logging: bool
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: Union[None, float],
        ssl_enable: bool,
        use_logging: bool,
    ):
        self._host = host
        self._port = port
        self._timeout = None if timeout is TimeoutNotSet else timeout  # type: ignore
        self._ssl_enable = ssl_enable
        self._use_logging = use_logging
        super().__init__()

    @abstractmethod
    def send(self, events: list, **kwargs):
        pass

    @abstractmethod
    def close(self):
        pass


class HttpTransport(Transport):
    """The :class:`HttpTransport <HttpTransport>` implements a client for the
    logstash plugin `inputs_http`.

    For more details visit:
    https://www.elastic.co/guide/en/logstash/current/plugins-inputs-http.html

    :param host: The hostname of the logstash HTTP server.
    :type host: str
    :param port: The TCP port of the logstash HTTP server.
    :type port: int
    :param timeout: The connection timeout. (Default: None)
    :type timeout: float
    :param ssl_enable: Activates TLS. (Default: True)
    :type ssl_enable: bool
    :param use_logging: Use logging for debugging.
    :type use_logging: bool
    :param username: Username for basic authorization. (Default: "")
    :type username: str
    :param password: Password for basic authorization. (Default: "")
    :type password: str
    :param index_name: A string with the prefix of the elasticsearch index that will be created.
    :type index_name: str
    :param max_content_length: The max content of an HTTP request in bytes.
    (Default: 100MB)
    :type max_content_length: int
    """

    def __init__(
        self,
        host: str,
        port: int,
        timeout: Union[None, float] = TimeoutNotSet,  # type: ignore
        ssl_enable: bool = True,
        use_logging: bool = False,
        **kwargs,
    ):
        super().__init__(host, port, timeout, ssl_enable, use_logging)
        self._username = kwargs.get("username", None)
        self._password = kwargs.get("password", None)
        self._index_name = kwargs.get("index_name", None)
        self._max_content_length = kwargs.get("max_content_length", 100 * 1024 * 1024)
        self.__session = None

    @property
    def url(self) -> str:
        """The URL of the logstash pipeline based on the hostname, the index, the port and
        the TLS usage.

        :return: The URL of the logstash HTTP pipeline.
        :rtype: str
        """
        protocol = "http"
        if self._ssl_enable:
            protocol = "https"

        if self._index_name is not None:
            return f"{protocol}://{self._host}:{self._port}/{self._index_name}"
        return f"{protocol}://{self._host}:{self._port}"

    def __batches(self, events: list) -> Iterator[list]:
        """Generate dynamic sized batches based on the max content length.

        :param events: A list of events.
        :type events: list
        :return: A iterator which generates batches of events.
        :rtype: Iterator[list]
        """
        current_batch = []
        event_iter = iter(events)
        while True:
            try:
                current_event = next(event_iter)
            except StopIteration:
                current_event = None
                if not current_batch:
                    return
                yield current_batch
            if current_event is None:
                return
            if len(current_event) > self._max_content_length:
                msg = "The event size <%s> is greater than the max content length <%s>. Skipping event."
                if self._use_logging:
                    logger.warning(msg, len(current_event), self._max_content_length)
                continue
            obj = json.loads(current_event)
            content_length = len(json.dumps(current_batch + [obj]).encode("utf8"))
            if content_length > self._max_content_length:
                batch = current_batch
                current_batch = [obj]
                yield batch
            else:
                current_batch += [obj]

    def __auth(self) -> HTTPBasicAuth:
        """The authentication method for the logstash pipeline. If the username
        or the password is not set correctly it will return None.

        :return: A HTTP basic auth object or None.
        :rtype: HTTPBasicAuth
        """
        if self._username is None or self._password is None:
            return None
        return HTTPBasicAuth(self._username, self._password)

    def close(self) -> None:
        """Close the HTTP session."""
        if self.__session is not None:
            self.__session.close()

    def send(self, events: list, **kwargs):
        """Send events to the logstash pipeline.

        Max Events: `logstash_async.Constants.QUEUED_EVENTS_BATCH_SIZE`
        Max Content Length: `HttpTransport._max_content_length`

        The method receives a list of events from the worker. It tries to send
        as much of the events as possible in one request. If the total size of
        the received events is greater than the maximal content length the
        events will be divide into batches.

        :param events: A list of events
        :type events: list
        """
        self.__session = requests.Session()
        for batch in self.__batches(events):
            if self._use_logging:
                logger.debug("Batch length: %s, Batch size: %s", len(batch), len(json.dumps(batch).encode("utf8")))
            response = self.__session.post(
                self.url,
                headers={"Content-Type": "application/json"},
                json=batch,
                timeout=self._timeout,
                auth=self.__auth(),
            )
            if response.status_code != 200:
                self.close()
                response.raise_for_status()
        self.close()
