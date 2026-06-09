import logging

import structlog

from app.core.logging import setup_logging


def test_setup_logging_does_not_raise() -> None:
    setup_logging("INFO")


def test_setup_logging_configures_structlog() -> None:
    setup_logging("INFO")
    logger = structlog.get_logger("test")
    assert logger is not None


def test_setup_logging_sets_root_level_info() -> None:
    setup_logging("INFO")
    assert logging.getLogger().level == logging.INFO


def test_setup_logging_sets_root_level_warning() -> None:
    setup_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
