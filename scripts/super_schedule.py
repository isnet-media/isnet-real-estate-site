"""Publisher schedule, evaluated at execution time in Israel, including DST."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Jerusalem')
COLLECTION_DAYS = frozenset({6, 1, 3})  # Python: Sunday, Tuesday, Thursday.

def in_window(now, *, health=False):
    local = now.astimezone(TZ)
    # Collection jobs have a 45 minute timeout: a start before 11 finishes before noon.
    return local.weekday() in COLLECTION_DAYS and 8 <= local.hour < (12 if health else 11)

def expected_collection_day(now):
    local = now.astimezone(TZ)
    # Allow the staggered morning collectors to finish before requiring today's data.
    day = local.date()
    if (local.hour, local.minute) < (10, 30):
        day -= timedelta(days=1)
    while day.weekday() not in COLLECTION_DAYS:
        day -= timedelta(days=1)
    return day

if __name__ == '__main__':
    print('allowed=' + str(in_window(datetime.now(TZ), health=True)).lower())
