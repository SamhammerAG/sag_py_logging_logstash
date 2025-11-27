import logging
import sys
import traceback
from datetime import datetime

from limits import parse as parse_rate_limit
from limits.storage import MemoryStorage
from limits.strategies import FixedWindowRateLimiter

from sag_py_logging_logstash.constants import constants


class SafeLogger:
    def __init__(
        self,
    ):
        self._shutdown_in_pgrogress = False
        self._logger = None
        self._rate_limit_storage = None
        self._rate_limit_strategy = None
        self._rate_limit_item = None

    def set_shutdown_in_progress(self):
        self._shutdown_in_pgrogress = True

    def log(self, log_level: str, message, *args, **kwargs):
        # we cannot log via the logging subsystem any longer once it has been set to shutdown
        if self._shutdown_in_pgrogress:
            self.print_log(log_level, message, *args, **kwargs)
        else:
            rate_limit_allowed = self._rate_limit_check(kwargs)
            if rate_limit_allowed <= 0:
                return  # skip further logging due to rate limiting
            if rate_limit_allowed == 1:
                # extend the message to indicate future rate limiting
                message = (
                    "{} (rate limiting effective, "
                    "further equal messages will be limited)".format(message)
                )

            self._safe_log_impl(log_level, message, *args, **kwargs)

    def _safe_log_impl(self, log_level: str, message, *args, **kwargs):
        if self._logger is None:
            self._setup_logger()

        log_func = getattr(self._logger, log_level.lower())
        log_func(message, *args, **kwargs)

    def _setup_logger(self):
        self._logger = logging.getLogger(__name__)
        # rate limit our own messages to not spam around in case of temporary network errors, etc
        rate_limit_setting = constants.ERROR_LOG_RATE_LIMIT
        if rate_limit_setting:
            self._rate_limit_storage = MemoryStorage()
            self._rate_limit_strategy = FixedWindowRateLimiter(self._rate_limit_storage)
            self._rate_limit_item = parse_rate_limit(rate_limit_setting)

    # ----------------------------------------------------------------------
    def _rate_limit_check(self, kwargs):
        exc = kwargs.pop("exc", None)
        if self._rate_limit_strategy is not None and exc is not None:
            key = self._factor_rate_limit_key(exc)
            # query curent counter for the caller
            _, remaining = self._rate_limit_strategy.get_window_stats(
                self._rate_limit_item, key
            )
            # increase the rate limit counter for the key
            self._rate_limit_strategy.hit(self._rate_limit_item, key)
            return remaining

        return 2  # any value greater than 1 means allowed

    def _factor_rate_limit_key(self, exc):  # pylint: disable=no-self-use
        module_name = getattr(exc, "__module__", "__no_module__")
        class_name = exc.__class__.__name__
        key_items = [module_name, class_name]
        if hasattr(exc, "errno") and isinstance(exc.errno, int):
            # in case of socket.error, include the errno as rate limiting key
            key_items.append(str(exc.errno))
        return ".".join(key_items)

    def print_log(self, log_level, message, *args, **kwargs):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            # Only apply formatting if args are passed
            if args:
                message = message % args
        except Exception as e:
            # Fallback: don't format message if it fails
            message = f"{message} (Log formatting failed: {e})"

        log_message = f"{timestamp}: {log_level}: {message}"
        print(log_message, file=sys.stderr)

        # print stack trace if available
        exc_info = kwargs.get("exc_info", None)
        if exc_info or log_level == "exception":
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
            stack_trace = "".join(traceback.format_exception(*exc_info))
            print(stack_trace, file=sys.stderr)
