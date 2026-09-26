from datetime import datetime

from services.intent_router import LOCAL_TZ, normalize_due_date


def test_normalize_due_date_defaults_to_today_when_default_time_is_upcoming():
    now = datetime(2026, 7, 5, 8, 0, tzinfo=LOCAL_TZ)

    due_date = normalize_due_date("remind me to call mom", None, now)

    assert due_date == "2026-07-05T09:00:00+05:30"


def test_normalize_due_date_defaults_to_tomorrow_when_default_time_has_passed():
    now = datetime(2026, 7, 5, 10, 0, tzinfo=LOCAL_TZ)

    due_date = normalize_due_date("remind me to call mom", None, now)

    assert due_date == "2026-07-06T09:00:00+05:30"


def test_normalize_due_date_extracts_time_and_today_when_llm_due_date_is_missing():
    now = datetime(2026, 7, 5, 4, 1, tzinfo=LOCAL_TZ)

    due_date = normalize_due_date("schedule me an alarm at 4:03 am today", None, now)

    assert due_date == "2026-07-05T04:03:00+05:30"


def test_normalize_due_date_extracts_time_only_and_uses_tomorrow_when_passed():
    now = datetime(2026, 7, 5, 4, 5, tzinfo=LOCAL_TZ)

    due_date = normalize_due_date("schedule me an alarm at 4:03 am", None, now)

    assert due_date == "2026-07-06T04:03:00+05:30"


def test_normalize_due_date_keeps_future_time_when_date_is_missing():
    now = datetime(2026, 7, 5, 18, 0, tzinfo=LOCAL_TZ)

    due_date = normalize_due_date("remind me at 7:30 pm", "2026-07-05T19:30:00+05:30", now)

    assert due_date == "2026-07-05T19:30:00+05:30"


def test_normalize_due_date_moves_time_only_reminder_to_tomorrow_when_passed():
    now = datetime(2026, 7, 5, 20, 0, tzinfo=LOCAL_TZ)

    due_date = normalize_due_date("remind me at 7:30 pm", "2026-07-05T19:30:00+05:30", now)

    assert due_date == "2026-07-06T19:30:00+05:30"


def test_normalize_due_date_uses_default_time_when_date_has_no_time():
    now = datetime(2026, 7, 5, 8, 0, tzinfo=LOCAL_TZ)

    due_date = normalize_due_date("remind me tomorrow", "2026-07-06T08:00:00+05:30", now)

    assert due_date == "2026-07-06T09:00:00+05:30"
