import datetime as dt

import pytz

from weatherbot.storage import Storage, User


def test_storage_roundtrip(tmp_path):
    s = Storage(str(tmp_path / "t.db"))
    s.save(User(1, "Ali", 41.3, 69.2, "Asia/Tashkent"))
    u = s.get(1)
    assert (u.hour, u.minute, u.timezone) == (7, 0, "Asia/Tashkent")
    u.hour = 6
    s.save(u)
    assert s.get(1).hour == 6
    s.delete(1)
    assert s.get(1) is None


def test_job_runs_at_7_local_time():
    from apscheduler.triggers.cron import CronTrigger

    tz = pytz.timezone("Asia/Tashkent")
    trigger = CronTrigger(hour=7, minute=0, timezone=tz)
    now = tz.localize(dt.datetime(2026, 10, 10, 8, 0))
    nxt = trigger.get_next_fire_time(None, now)
    assert nxt.astimezone(pytz.utc).hour == 2  # 07:00 Toshkent = 02:00 UTC
    assert nxt.day == 11
