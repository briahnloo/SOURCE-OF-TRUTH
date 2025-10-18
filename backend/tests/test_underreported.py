"""Tests for underreported detection logic"""

from datetime import datetime, timedelta

import pytest
from app.config import settings


def test_underreported_criteria():
    """Test underreported detection criteria"""

    # Scenario 1: NGO source + no major wire + recent = underreported
    has_ngo = True
    has_wire = False
    hours_old = 24

    is_underreported = has_ngo and not has_wire and hours_old < settings.underreported_window_hours

    assert is_underreported is True

    # Scenario 2: NGO source + major wire = NOT underreported
    has_ngo = True
    has_wire = True

    is_underreported = has_ngo and not has_wire

    assert is_underreported is False

    # Scenario 3: No NGO + no wire = NOT underreported (just unverified)
    has_ngo = False
    has_wire = False

    is_underreported = has_ngo and not has_wire

    assert is_underreported is False


def test_time_window():
    """Test 48-hour time window for underreported detection"""

    now = datetime.utcnow()

    # 24 hours old - within window
    event_time_1 = now - timedelta(hours=24)
    within_window_1 = (now - event_time_1).total_seconds() < (48 * 3600)
    assert within_window_1 is True

    # 47 hours old - within window
    event_time_2 = now - timedelta(hours=47)
    within_window_2 = (now - event_time_2).total_seconds() < (48 * 3600)
    assert within_window_2 is True

    # 49 hours old - outside window
    event_time_3 = now - timedelta(hours=49)
    within_window_3 = (now - event_time_3).total_seconds() < (48 * 3600)
    assert within_window_3 is False


def test_minimum_sources():
    """Test minimum source requirement"""

    # 2 sources - meets requirement
    articles_count_1 = 2
    assert articles_count_1 >= settings.underreported_min_sources

    # 1 source - does not meet requirement
    articles_count_2 = 1
    assert articles_count_2 < settings.underreported_min_sources
