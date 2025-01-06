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

# For ordering if the user typed "WeFrMo" etc.:
ICS_DAY_ORDER = ["MO","TU","WE","TH","FR","SA","SU"]

def parse_days_times(days_times_str):
    """
    e.g. "MoWeFr 4:00PM - 5:05PM"
    => (["MO","WE","FR"], time(16,0), time(17,5))
    """
    # 1) Separate "MoWeFr" from "4:00PM - 5:05PM"
    m = re.match(r'^([A-Za-z]+)\s+(.*)$', days_times_str.strip())
    if not m:
        return [], None, None
    days_part, time_part = m.groups()

    # 2) e.g. "MoWeFr" -> ["Mo","We","Fr"]
    i = 0
    day_codes = []
    while i < len(days_part):
        chunk = days_part[i : i+2]
        day_codes.append(chunk)
        i += 2

    # Convert ["Mo","We","Fr"] -> ["MO","WE","FR"]
    ics_days = [DAY_MAP.get(d,"") for d in day_codes if d in DAY_MAP]

    # 3) parse the time range "4:00PM - 5:05PM"
    tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
    if not tm:
        return ics_days, None, None
    start_str, end_str = tm.groups()

    start_t = parse_time_12h(start_str)
    end_t   = parse_time_12h(end_str)
    return ics_days, start_t, end_t

def parse_time_12h(tstr):
    """
    e.g. "4:00PM" => time(16,0)
    """
    tstr = tstr.strip()
    # Insert a space => "4:00PM" -> "4:00 PM"
    if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
        tstr = tstr[:-2] + " " + tstr[-2:]
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

def align_earliest_day(start_date, ics_days):
    """
    If we have e.g. ics_days=["MO","WE","FR"], 
    pick the earliest day by ICS_DAY_ORDER => "MO"
    shift start_date forward to that day.
    """
    # e.g. earliest_d = "MO"
    earliest_d = min(ics_days, key=lambda d: ICS_DAY_ORDER.index(d))

    # We'll map to Python's Monday=0..Sunday=6
    PY_DAY_MAP = {"MO":0,"TU":1,"WE":2,"TH":3,"FR":4,"SA":5,"SU":6}
    target_wd = PY_DAY_MAP[earliest_d]
    current_wd = start_date.weekday()
    if current_wd <= target_wd:
        diff = target_wd - current_wd
    else:
        diff = 7 - (current_wd - target_wd)
    return start_date + timedelta(days=diff)

def create_multi_day_event(course):
    """
    Creates one recurring event per "class" 
    if it meets multiple days (MoWeFr). 
    - Align earliest day 
    - Build local date/time 
    - Add BYDAY=MO,WE,FR etc.
    """
    events = []
    title = course.get("title","Untitled Course")

    # Each "classes" entry might be "MoWeFr 4:00PM - 5:05PM" + room, instructor, ...
    for cls_info in course["classes"]:
        dt_str = cls_info.get("days_times","")
        se_str = cls_info.get("start_end","")
        room   = cls_info.get("room","")
        instr  = cls_info.get("instructor","")
        comp   = cls_info.get("component","")
        sect   = cls_info.get("section","")
        cnum   = cls_info.get("class_nbr","")

        ics_days, start_t, end_t = parse_days_times(dt_str)
        start_d, end_d = parse_start_end_dates(se_str)

        # skip if missing data
        if not ics_days or not start_t or not end_t or not start_d or not end_d:
            continue

        # e.g. "MO,WE,FR"
        byday_str = ",".join(ics_days)

        # shift start_date to the earliest ICS day
        aligned_start = align_earliest_day(start_d, ics_days)

        # build naive local datetimes
        dt_begin = datetime.combine(aligned_start, start_t)
        dt_end   = datetime.combine(aligned_start, end_t)

        # Convert to ICS format e.g. "20250106T160000"
        begin_str = dt_begin.strftime("%Y%m%dT%H%M%S")
        end_str   = dt_end.strftime("%Y%m%dT%H%M%S")

        # Create single event
        e = Event()
        e.name        = f"{title} ({comp} {sect})"
        e.description = f"Instructor: {instr}\nClass Number: {cnum}"
        e.location    = room

        # Instead of e.begin/e.end, write lines with TZID=America/Los_Angeles
        e.extra.append(ContentLine(
            name="DTSTART;TZID=America/Los_Angeles",
            value=begin_str
        ))
        e.extra.append(ContentLine(
            name="DTEND;TZID=America/Los_Angeles",
            value=end_str
        ))

        # The RRULE => "FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=..."
        until_utc = end_d.strftime("%Y%m%dT235900Z")
        e.extra.append(ContentLine(
            name="RRULE",
            value=f"FREQ=WEEKLY;BYDAY={byday_str};UNTIL={until_utc}"
        ))

        events.append(e)
    return events

def add_vtimezone_block(cal: Calendar):
    """
    Insert a standard VTIMEZONE block for "America/Los_Angeles".
    """
    lines = [
        ContentLine("BEGIN","VTIMEZONE"),
        ContentLine("TZID","America/Los_Angeles"),
        ContentLine("X-LIC-LOCATION","America/Los_Angeles"),

        ContentLine("BEGIN","DAYLIGHT"),
        ContentLine("TZOFFSETFROM","-0800"),
        ContentLine("TZOFFSETTO","-0700"),
        ContentLine("TZNAME","PDT"),
        ContentLine("DTSTART","19700308T020000"),
        ContentLine("RRULE","FREQ=YEARLY;BYMONTH=3;BYDAY=2SU"),
        ContentLine("END","DAYLIGHT"),

        ContentLine("BEGIN","STANDARD"),
        ContentLine("TZOFFSETFROM","-0700"),
        ContentLine("TZOFFSETTO","-0800"),
        ContentLine("TZNAME","PST"),
        ContentLine("DTSTART","19701101T020000"),
        ContentLine("RRULE","FREQ=YEARLY;BYMONTH=11;BYDAY=1SU"),
        ContentLine("END","STANDARD"),

        ContentLine("END","VTIMEZONE")
    ]
    for i in lines:
        cal.extra.append(i)

def build_calendar(courses):
    """
    Build a single ICS calendar. 
    - For each course, create single multi-day events
    - Insert VTIMEZONE for LA
    """
    cal = Calendar()
    add_vtimezone_block(cal)

    for course in courses:
        evts = create_multi_day_event(course)
        for e in evts:
            cal.events.add(e)
    return cal
