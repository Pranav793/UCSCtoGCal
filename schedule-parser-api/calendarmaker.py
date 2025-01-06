import re
from datetime import datetime, time, timedelta
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

ICS_DAY_ORDER = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

def parse_days_times(days_times_str):
    """
    e.g. "MoWeFr 4:00PM - 5:05PM" -> (["MO","WE","FR"], time(16,0), time(17,5))
    """
    m = re.match(r'^([A-Za-z]+)\s+(.*)$', days_times_str.strip())
    if not m:
        return [], None, None

    days_part, time_part = m.groups()

    # e.g. "MoWeFr" -> ["Mo","We","Fr"]
    day_codes = []
    i = 0
    while i < len(days_part):
        chunk = days_part[i : i+2]
        day_codes.append(chunk)
        i += 2

    # Convert to ICS day codes: e.g. "Mo" -> "MO"
    ics_days = [DAY_MAP[d] for d in day_codes if d in DAY_MAP]

    # Parse time range "4:00PM - 5:05PM"
    tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
    if not tm:
        return ics_days, None, None
    start_str, end_str = tm.groups()

    start_t = parse_time_12h(start_str)
    end_t   = parse_time_12h(end_str)
    return ics_days, start_t, end_t

def parse_time_12h(tstr):
    """
    "4:00PM" => time(16,0)
    """
    tstr = tstr.strip()
    if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
        # Insert space => "4:00PM" -> "4:00 PM"
        tstr = tstr[:-2] + " " + tstr[-2:]
        dt = datetime.strptime(tstr, "%I:%M %p")
        return dt.time()
    return None

def parse_start_end_dates(date_range_str):
    """
    "01/06/2025 - 03/14/2025" => (date(2025,1,6), date(2025,3,14))
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
    Shift start_date forward to the correct weekday (MO,WE,FR,...).
    Monday=0..Sunday=6
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
    Instead of using e.begin/e.end (which can shift times),
    we'll manually add lines for local times with TZID=America/Los_Angeles:
      DTSTART;TZID=America/Los_Angeles:YYYYmmddTHHMMSS
      DTEND;TZID=America/Los_Angeles:YYYYmmddTHHMMSS
    Also do single-event multi-day (e.g., BYDAY=MO,WE,FR).
    """
    events = []
    course_title = course.get("title", "Untitled Course")

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

        # e.g. ["MO","WE","FR"] => "MO,WE,FR"
        wday_str = ",".join(weekdays)
        earliest_wd = min(weekdays, key=lambda d: ICS_DAY_ORDER.index(d))
        first_occ   = align_first_occurrence(start_date, earliest_wd)

        # Build naive datetimes, then format them as local strings
        start_dt = datetime.combine(first_occ, start_t)
        end_dt   = datetime.combine(first_occ, end_t)
        # e.g. "20250106T160000"
        start_str = start_dt.strftime("%Y%m%dT%H%M%S")
        end_str   = end_dt.strftime("%Y%m%dT%H%M%S")

        # Create the event object
        e = Event()

        # We'll skip setting e.begin/e.end, because that might produce floating or UTC times.
        # Instead, we add custom lines:
        e.extra.append(ContentLine(
            name="DTSTART;TZID=America/Los_Angeles",
            value=start_str
        ))
        e.extra.append(ContentLine(
            name="DTEND;TZID=America/Los_Angeles",
            value=end_str
        ))

        # Single RRULE for multi-day repeating
        until_utc = end_date.strftime("%Y%m%dT235900Z")
        e.extra.append(ContentLine(
            name="RRULE",
            value=f"FREQ=WEEKLY;BYDAY={wday_str};UNTIL={until_utc}"
        ))

        e.name        = f"{course_title} ({comp} {sect})"
        e.description = f"Instructor: {instr}\nClass Number: {cnum}"
        e.location    = room

        events.append(e)

    return events

########################
# HARDCODE VTIMEZONE
########################
def add_vtimezone_block(cal: Calendar):
    """
    Insert a static VTIMEZONE block for America/Los_Angeles 
    so the ICS file has local-time definitions for PST/PDT.
    """
    tz_lines = [
        # Note: This minimal block is typically recognized by modern calendars
        "X-WR-TIMEZONE:America/Los_Angeles",
        "BEGIN:VTIMEZONE",
        "TZID:America/Los_Angeles",
        "X-LIC-LOCATION:America/Los_Angeles",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:-0800",
        "TZOFFSETTO:-0700",
        "TZNAME:PDT",
        "DTSTART:19700308T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU",
        "END:DAYLIGHT",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:-0700",
        "TZOFFSETTO:-0800",
        "TZNAME:PST",
        "DTSTART:19701101T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU",
        "END:STANDARD",
        "END:VTIMEZONE"
    ]
    for i in tz_lines:
        cal.extra.append(ContentLine(
            name=i.split(":")[0],
            value=i.split(":")[1],
        ))

    return cal

def build_calendar_with_timezone(courses):
    """
    Build a single Calendar, add the LA time zone block, 
    and add events from your parse.
    """
    cal = Calendar()
    cal = add_vtimezone_block(cal)  # Insert the LA time zone block

    for course in courses:
        events = create_events_for_course(course)
        for e in events:
            cal.events.add(e)

    return cal
