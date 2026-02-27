import logging

from timeflip_tracker import logger


def test_create_logger_defaults_to_error(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    logger.create_logger()

    assert logger.get_logger().level == logging.ERROR


def test_create_logger_respects_debug_env(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    logger.create_logger()

    assert logger.get_logger().level == logging.DEBUG
