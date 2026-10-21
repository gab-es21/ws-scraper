from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from scraper.scheduling import is_overdue, next_run_at, parse_time

LISBON = ZoneInfo("Europe/Lisbon")


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def test_parse_time():
    assert parse_time("04:00") == time(4, 0)
    assert parse_time(" 23:30 ") == time(23, 30)


@pytest.mark.parametrize(
    "now, expected_local",
    [
        (utc(2026, 10, 21, 2, 0), datetime(2026, 10, 21, 4, 0)),  # 03:00 Lisbon (summer time) -> today
        (utc(2026, 10, 21, 3, 0), datetime(2026, 10, 22, 4, 0)),  # exactly 04:00 Lisbon -> tomorrow
        (utc(2026, 10, 21, 12, 0), datetime(2026, 10, 22, 4, 0)),  # afternoon -> tomorrow
        (utc(2026, 12, 1, 3, 30), datetime(2026, 12, 1, 4, 0)),  # winter time: 03:30 Lisbon -> today
    ],
)
def test_next_run_is_the_next_local_occurrence(now, expected_local):
    run = next_run_at(now, time(4, 0), LISBON)
    assert run.replace(tzinfo=None) == expected_local
    assert run > now


def test_next_run_across_the_daylight_saving_change():
    # Clocks go back on 2026-10-25 in Lisbon: 04:00 local is 03:00 UTC before, 04:00 UTC after.
    assert next_run_at(utc(2026, 10, 24, 12, 0), time(4, 0), LISBON) == utc(2026, 10, 25, 4, 0)


def test_is_overdue():
    now = utc(2026, 10, 21, 12, 0)
    assert is_overdue(None, now)
    assert is_overdue(now - timedelta(hours=25), now)
    assert not is_overdue(now - timedelta(hours=3), now)
