"""Unit tests for logging utilities."""

from __future__ import annotations

import logging

import pytest

from gps.utils.logging import configure_logging


@pytest.mark.unit
def test_configure_logging_does_not_duplicate_handlers() -> None:
    # Call configure_logging 10 times
    for _ in range(10):
        configure_logging("INFO")

    logger = logging.getLogger("gps")
    assert len(logger.handlers) == 1
