import logging
import os


def is_debug():
    return os.getenv("DEBUG") in [1, "1", "true", "yes"]


def get_logging_level():
    return os.getenv("LOG_LEVEL", "INFO")
