import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from ics import Calendar, Event
from ics.grammar.parse import ContentLine

DAY_MAP = {
    "Mo": "MO",
    "Tu": "TU",
    "We": "WE",
    "Th": "TH",
    "Fr": "FR",
    "Sa": "SA",
    "Su": "SU"
}

ICS_DAY_ORDER = ["MO","TU","WE","TH","FR","SA","SU"]

def parse_days_times(days_times_str):
    """
    e.g. "MoWeFr 4:00PM - 5:05PM"
    => (["MO","WE","FR"], time(16,0), time(17,5))
    """
    m = re.match(r'^([A-Za-z]+)\s+(.*)$', days_times_str.strip())
    if not m:
        return [], None, None

    days_part, time_part = m.groups()

    # Convert e.g. "MoWeFr" -> ["Mo","We","Fr"]
    day_codes = []
    i = 0
    while i < len(days_part):
        chunk = days_part[i:i+2]
        day_codes.append(chunk)
        i += 2

    # e.g. ["Mo","We","Fr"] => ["MO","WE","FR"]
    ics_days = [DAY_MAP.get(d, "") for d in day_codes if d in DAY_MAP]

    # Parse "4:00PM - 5:05PM"
    tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
    if not tm:
        return ics_days, None, None
    start_str, end_str = tm.groups()

    start_t = parse_time_12h(start_str)
    end_t   = parse_time_12h(end_str)
    return ics_days, start_t, end_t

def parse_time_12h(tstr):
    """
    e.g. "4:00PM" => time(16,0).
    """
    tstr = tstr.strip()
    if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
        tstr = tstr[:-2] + " " + tstr[-2:]  # "4:00 PM"
        dt = datetime.strptime(tstr, "%I:%M %p")
        return dt.time()
    return None

def parse_start_end_dates(date_range_str):
    """
    e.g. "01/06/2025 - 03/14/2025"
    => (date(2025,1,6), date(2025,3,14))
    """
    m = re.match(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', date_range_str)
    if not m:
        return None, None
    start_str, end_str = m.groups()
    start_dt = datetime.strptime(start_str, "%m/%d/%Y").date()
    end_dt   = datetime.strptime(end_str, "%m/%d/%Y").date()
    return start_dt, end_dt

def align_first_occurrence(start_date, wday_ics):
    """
    Shift start_date forward to correct weekday: e.g. "MO" => Monday=0..Sunday=6
    """
    PY_DAY_MAP = {"MO":0, "TU":1, "WE":2, "TH":3, "FR":4, "SA":5, "SU":6}
    target_wd  = PY_DAY_MAP[wday_ics]
    current_wd = start_date.weekday()
    if current_wd <= target_wd:
        diff = target_wd - current_wd
    else:
        diff = 7 - (current_wd - target_wd)
    return start_date + timedelta(days=diff)

def create_events_for_course(course):
    """
    We store local day/time, then SHIFT -8 hours (manually) 
    so ICS lines say e.g. "20250106T160000Z" 
    if local = Jan 6, 16:00 PST. 
    => Google sees it as Monday 4 PM local, no Sunday shift.
    """
    events = []
    course_title = course.get("title", "Untitled Course")

    # We'll define local zone if we want, or just treat everything naive
    la_zone = ZoneInfo("America/Los_Angeles")

    for cls_info in course["classes"]:
        dt_str = cls_info.get("days_times", "")
        se_str = cls_info.get("start_end", "")
        room   = cls_info.get("room", "")
        instr  = cls_info.get("instructor", "")
        comp   = cls_info.get("component", "")
        sect   = cls_info.get("section", "")
        cnum   = cls_info.get("class_nbr", "")

        weekdays, start_t, end_t = parse_days_times(dt_str)
        start_date, end_date = parse_start_end_dates(se_str)
        if not weekdays or not start_t or not end_t or not start_date or not end_date:
            continue

        wday_str = ",".join(weekdays)
        earliest_wd = min(weekdays, key=lambda d: ICS_DAY_ORDER.index(d))
        first_occ   = align_first_occurrence(start_date, earliest_wd)

        # 1) Construct the local naive datetime
        #    E.g. Monday 2025-01-06 16:00
        start_local = datetime.combine(first_occ, start_t)
        end_local   = datetime.combine(first_occ, end_t)

        # 2) SHIFT them by -8 hours => "fake" UTC 
        #    So 16:00 local => 16:00 minus 8 hours => 08:00Z same day
        #    That ensures ICS lines remain on the same date
        shift = timedelta(hours=8)  # or 7 if DST, but let's assume 8
        # If you prefer minus 8 hours => start_local - shift
        #    but let's do minus 8 => Monday 16:00 => Monday 08:00Z
        # This keeps the local day/time in ICS lines.

        # Actually, let's subtract 8 hours:
        start_fake_utc = start_local - shift
        end_fake_utc   = end_local   - shift

        # 3) Format them with 'Z'
        start_str = start_fake_utc.strftime("%Y%m%dT%H%M%S") + "Z"
        end_str   = end_fake_utc.strftime("%Y%m%dT%H%M%S")   + "Z"

        e = Event()
        e.name = f"{course_title} ({comp} {sect})"
        e.description = f"Instructor: {instr}\nClass Number: {cnum}"
        e.location = room

        # We skip e.begin/e.end to avoid ICS rewriting. We'll do custom lines:
        # e.extra.append(ContentLine(
        #     name="DTSTART;TZID=America/Los_Angeles",
        #     value=start_str
        # ))
        e.extra.append(ContentLine(name="DTSTART;TZID=America/Los_Angeles", value=start_str))
        e.extra.append(ContentLine(name="DTEND;TZID=America/Los_Angeles",   value=end_str))

        until_utc = end_date.strftime("%Y%m%dT235900Z")
        e.extra.append(ContentLine(
            name="RRULE",
            value=f"FREQ=WEEKLY;BYDAY={wday_str};UNTIL={until_utc}"
        ))

        events.append(e)

    return events

def build_calendar(courses):
    """
    Builds a calendar that manually offsets 
    local times by 8 hours, then appends 'Z'.
    """
    cal = Calendar()
    for course in courses:
        evts = create_events_for_course(course)
        for e in evts:
            cal.events.add(e)
    return cal
