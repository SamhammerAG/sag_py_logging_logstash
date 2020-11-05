=====================
python-logstash-async
=====================

.. image:: https://travis-ci.com/SamhammerAG/python-logstash-async.svg?branch=master
    :target: https://travis-ci.com/SamhammerAG/python-logstash-async
    :alt: Travis CI

Python Logstash Async is an asynchronous Python logging handler to submit
log events to a remote Logstash instance.
It based on  open source library, see the documentation http://python-logstash-async.readthedocs.io/en/latest/.
In this version transporter is limited to HTTPTransport, according to  Logstash intern installation requirements.

Unlike most other Python Logstash logging handlers, this package works asynchronously
by collecting log events from Python's logging subsystem and then transmitting the
collected events in a separate worker thread to Logstash.
This way, the main application (or thread) where the log event occurred, doesn't need to
wait until the submission to the remote Logstash instance succeeded.

This is especially useful for applications like websites or web services or any kind of
request serving API where response times matter.

Usage
-----
Example::

    from logstash_async.handler import AsynchronousLogstashHandler
    from logstash_async.formatter import LogstashFormatter
    import logging

    logstash_handler = AsynchronousLogstashHandler(
        host='my_host',
        port=123,
        username='my_user',
        password='my_password',
        index_name = 'my_index')
    logstash_formatter = LogstashFormatter( extra_prefix='',
    extra={'customer': "name", 'ap_environment': "local"})
    logstash_handler.setFormatter(logstash_formatter)

    logging_handlers = []
    logging_handlers.append(logstash_handler)

    logging.basicConfig(
    level="INFO",
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=logging_handlers)

    logging.getLogger().info("Logging Message", extra = {'new_field':"value"})

Local Installation
------------------

To install from master branch just use the following command::

    pip install git+https://github.com/SamhammerAG/python-logstash-async.git
Existing preprocessors


You can download python-logstash-async and install it
directly from source::

    python setup.py install


	
Get the Source
--------------

The source code is available at https://github.com/SamhammerAG/python-logstash-async.

