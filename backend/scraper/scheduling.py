"""When the daily scrape should run (used by `manage.py scheduler`)."""

from datetime import datetime, time, timedelta

# A run is overdue (e.g. the machine was off at the scheduled time) after this long.
MAX_AGE = timedelta(hours=24)


def parse_time(text):
    """'04:00' -> time(4, 0)."""
    hours, minutes = text.strip().split(":")
    return time(int(hours), int(minutes))


def next_run_at(now, at, tz):
    """The next moment strictly after `now` that is `at` o'clock in timezone `tz`."""
    local_now = now.astimezone(tz)
    candidate = datetime.combine(local_now.date(), at, tzinfo=tz)
    if candidate <= local_now:
        candidate = datetime.combine(local_now.date() + timedelta(days=1), at, tzinfo=tz)
    return candidate


def is_overdue(last_success, now):
    return last_success is None or now - last_success >= MAX_AGE
