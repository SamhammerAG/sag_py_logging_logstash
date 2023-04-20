# sag_py_logging_logstash

[![Maintainability][codeclimate-image]][codeclimate-url]
[![Coverage Status][coveralls-image]][coveralls-url]
[![Known Vulnerabilities](https://snyk.io/test/github/SamhammerAG/sag_py_logging_logstash/badge.svg)](https://snyk.io/test/github/SamhammerAG/sag_py_logging_logstash)

[coveralls-image]:https://coveralls.io/repos/github/SamhammerAG/sag_py_logging_logstash/badge.svg?branch=master
[coveralls-url]:https://coveralls.io/github/SamhammerAG/sag_py_logging_logstash?branch=master
[codeclimate-image]:https://api.codeclimate.com/v1/badges/5e8f1c5bef6aeecd543d/maintainability
[codeclimate-url]:https://codeclimate.com/github/SamhammerAG/sag_py_logging_logstash/maintainability


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

## Usage

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


### Installation
pip install sag-py-logging-logstash

## How to start developing

### With vscode

Just install vscode with dev containers extension. All required extensions and configurations are prepared automatically.

### With pycharm

* Install latest pycharm
* Install pycharm plugin BlackConnect
* Configure the python interpreter/venv
* pip install requirements-dev.txt
* pip install black[d]
* Ctl+Alt+S => Check Tools => BlackConnect => Trigger when saving changed files
* Ctl+Alt+S => Check Tools => BlackConnect => Trigger on code reformat
* Ctl+Alt+S => Click Tools => BlackConnect => "Load from pyproject.yaml" (ensure line length is 120)
* Ctl+Alt+S => Click Tools => BlackConnect => Configure path to the blackd.exe at the "local instance" config (e.g. C:\Python310\Scripts\blackd.exe)
* Ctl+Alt+S => Click Tools => Actions on save => Reformat code
* Restart pycharm

## How to publish
* Update the version in setup.py and commit your change
* Create a tag with the same version number
* Let github do the rest
