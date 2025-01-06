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
        chunk = days_part[i:i+2]
        day_codes.append(chunk)
        i += 2
    
    # Convert e.g. ["Mo","We","Fr"] -> ["MO","WE","FR"]
    ics_days = [DAY_MAP[d] for d in day_codes if d in DAY_MAP]
    
    # parse "4:00PM - 5:05PM"
    tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
    if not tm:
        return ics_days, None, None
    start_str, end_str = tm.groups()

    start_t = parse_time_12h(start_str)
    end_t   = parse_time_12h(end_str)
    return ics_days, start_t, end_t

def parse_time_12h(tstr):
    """
    "4:00PM" => datetime.time(16, 0)
    """
    tstr = tstr.strip()
    if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
        tstr = tstr[:-2] + " " + tstr[-2:]
        dt = datetime.strptime(tstr, "%I:%M %p")
        return dt.time()
    return None

def parse_start_end_dates(date_range_str):
    """
    e.g. "01/06/2025 - 03/14/2025" => (date(2025,1,6), date(2025,3,14))
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
    Shift start_date forward to e.g. "MO","WE","FR", etc.
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
    Creates ICS events where we keep local day/time in the ICS lines 
    but forcibly add a "Z" suffix => 'fake' UTC. This avoids Sunday shift
    but is not strictly correct in time-zone math.
    """
    events = []
    course_title = course.get("title", "Untitled Course")

    # We'll assume local = America/Los_Angeles
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

        # 1) Build local aware datetimes (just to confirm day/time)
        start_local = datetime.combine(first_occ, start_t, la_zone)
        end_local   = datetime.combine(first_occ, end_t,   la_zone)

        # 2) But we do NOT convert to real UTC. We keep the same date/time as local:
        #    i.e. if Monday 16:00 PST, we store "20250106T160000Z" 
        #    even though real UTC would be 20250107T000000Z.
        start_str = start_local.strftime("%Y%m%dT%H%M%S") + "Z"
        end_str   = end_local.strftime("%Y%m%dT%H%M%S")   + "Z"

        # 3) Make the event with e.begin/e.end or custom lines
        e = Event()
        e.name = f"{course_title} ({comp} {sect})"
        e.description = f"Instructor: {instr}\nClass Number: {cnum}"
        e.location = room

        # We'll override e.begin/e.end with these lines:
        # This forcibly sets "DTSTART:20250106T160000Z" in the ICS 
        # (the same local day/time, plus 'Z')
        e.extra.append(ContentLine(name="DTSTART", value=start_str))
        e.extra.append(ContentLine(name="DTEND",   value=end_str))

        # Single RRULE for multi-day
        until_utc = end_date.strftime("%Y%m%dT235900Z")
        e.extra.append(ContentLine(
            name="RRULE",
            value=f"FREQ=WEEKLY;BYDAY={wday_str};UNTIL={until_utc}"
        ))

        events.append(e)

    return events

def build_utc_calendar(courses):
    """
    Build a Calendar that 'fakes' UTC by storing local day/time + 'Z'
    to avoid Sunday shift in Google, albeit not strictly correct math.
    """
    cal = Calendar()
    for course in courses:
        evts = create_events_for_course(course)
        for e in evts:
            cal.events.add(e)
    return cal
