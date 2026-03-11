import logging
import sys

from app.core.request_context import request_id_context


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get()
        return True


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIDFilter())

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | request_id=%(request_id)s | %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.handlers:
        root_logger.handlers.clear()

    root_logger.addHandler(handler)