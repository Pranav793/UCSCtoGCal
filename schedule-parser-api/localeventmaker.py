# import re
# from datetime import datetime, time, timedelta
# from ics import Calendar, Event
# from ics.grammar.parse import ContentLine

# # For Python 3.9+, you can use zoneinfo
# from zoneinfo import ZoneInfo

# DAY_MAP = {
#     "Mo": "MO",
#     "Tu": "TU",
#     "We": "WE",
#     "Th": "TH",
#     "Fr": "FR",
#     "Sa": "SA",
#     "Su": "SU"
# }

# def parse_days_times(days_times_str):
#     """
#     Given a string like "MoWeFr 4:00PM - 5:05PM",
#     return:
#       - a list of ICS weekday codes (e.g. ["MO", "WE", "FR"])
#       - start_time as datetime.time (local)
#       - end_time as datetime.time (local)
#     """
#     m = re.match(r'^([A-Za-z]+)\s+(.*)$', days_times_str.strip())
#     if not m:
#         return [], None, None
    
#     days_part, time_part = m.groups()  # e.g. "MoWeFr", "4:00PM - 5:05PM"
    
#     # Extract each 2-letter day code: "MoWeFr" => ["Mo", "We", "Fr"]
#     day_codes = []
#     i = 0
#     while i < len(days_part):
#         day_2 = days_part[i : i+2]
#         day_codes.append(day_2)
#         i += 2
    
#     ics_days = []
#     for d in day_codes:
#         if d in DAY_MAP:
#             ics_days.append(DAY_MAP[d])  # e.g. "Mo" -> "MO", etc.
    
#     # Parse time range: "4:00PM - 5:05PM"
#     tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
#     if not tm:
#         return ics_days, None, None
#     start_str, end_str = tm.groups()

#     start_t = parse_time_12h(start_str)
#     end_t   = parse_time_12h(end_str)

#     return ics_days, start_t, end_t

# def parse_time_12h(tstr):
#     """
#     Convert "4:00PM" => datetime.time(16, 0) (local).
#     """
#     tstr = tstr.strip()
#     if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
#         # Insert space: "4:00PM" => "4:00 PM"
#         tstr = tstr[:-2] + " " + tstr[-2:]
#         dt = datetime.strptime(tstr, "%I:%M %p")
#         return dt.time()
#     return None

# def parse_start_end_dates(date_range_str):
#     """
#     Convert "01/06/2025 - 03/14/2025" => (date(2025,1,6), date(2025,3,14))
#     """
#     m = re.match(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', date_range_str)
#     if not m:
#         return None, None
#     start_str, end_str = m.groups()
#     start_dt = datetime.strptime(start_str, "%m/%d/%Y").date()
#     end_dt   = datetime.strptime(end_str, "%m/%d/%Y").date()
#     return start_dt, end_dt

# def align_first_occurrence(start_date, wday_ics):
#     """
#     Shift start_date forward until it's the correct weekday (MO, TU, WE, TH, etc.)
#     """
#     PY_DAY_MAP = {"MO":0, "TU":1, "WE":2, "TH":3, "FR":4, "SA":5, "SU":6}
    
#     target_wd  = PY_DAY_MAP[wday_ics]
#     current_wd = start_date.weekday()  # Monday=0, Sunday=6
#     if current_wd <= target_wd:
#         diff = target_wd - current_wd
#     else:
#         diff = 7 - (current_wd - target_wd)
    
#     return start_date + timedelta(days=diff)

# def create_events_for_course(course):
#     """
#     Convert each class in 'course' into one or more weekly recurring events
#     in local (America/Los_Angeles) time.
#     """
#     events = []
#     course_title = course.get("title", "Untitled Course")

#     for cls_info in course["classes"]:
#         dt_str = cls_info.get("days_times", "")  # e.g. "MoWeFr 4:00PM - 5:05PM"
#         se_str = cls_info.get("start_end", "")   # e.g. "01/06/2025 - 03/14/2025"
#         room   = cls_info.get("room", "")
#         instr  = cls_info.get("instructor", "")
#         comp   = cls_info.get("component", "")
#         section= cls_info.get("section", "")
#         cnum   = cls_info.get("class_nbr", "")

#         weekdays, start_t, end_t = parse_days_times(dt_str)
#         start_date, end_date = parse_start_end_dates(se_str)
#         if not weekdays or not start_t or not end_t or not start_date or not end_date:
#             # skip if any essential piece is missing
#             continue

#         # For each day in weekdays, create a weekly recurring event
#         for wday in weekdays:
#             e = Event()
#             e.name = f"{course_title} ({comp} {section})"
#             e.description = f"Instructor: {instr}\nClass Number: {cnum}"
#             e.location    = room
            
#             # Compute first occurrence on the correct weekday
#             first_occ = align_first_occurrence(start_date, wday)
            
#             # Combine date + time, assign local time zone
#             tz = ZoneInfo("America/Los_Angeles")
            
#             start_dt = datetime.combine(first_occ, start_t, tz)
#             end_dt   = datetime.combine(first_occ, end_t,   tz)
            
#             e.begin = start_dt
#             e.end   = end_dt
            
#             # Add an RRULE for weekly recurrence until the end_date
#             # We'll store everything in local time
#             # ics < 0.9 doesn't have a direct property for RRULE except using e.extra
#             e.extra.append(
#                 ContentLine(
#                     name="RRULE", 
#                     value=f"FREQ=WEEKLY;BYDAY={wday};UNTIL={end_date.strftime('%Y%m%dT235900Z')}"
#                 )
#             )
            
#             events.append(e)
    
#     return events


import re
from datetime import datetime, time, timedelta
from ics import Calendar, Event
from ics.grammar.parse import ContentLine
from zoneinfo import ZoneInfo  # For local time in Python 3.9+

DAY_MAP = {
    "Mo": "MO",
    "Tu": "TU",
    "We": "WE",
    "Th": "TH",
    "Fr": "FR",
    "Sa": "SA",
    "Su": "SU"
}

# We'll define an ordering so we can align the first occurrence on the earliest day (e.g. Monday before Wed).
ICS_DAY_ORDER = ["MO","TU","WE","TH","FR","SA","SU"]

def parse_days_times(days_times_str):
    """
    e.g. "MoWeFr 4:00PM - 5:05PM" => (["MO","WE","FR"], time(16,0), time(17,5))
    """
    m = re.match(r'^([A-Za-z]+)\s+(.*)$', days_times_str.strip())
    if not m:
        return [], None, None
    
    days_part, time_part = m.groups()  # "MoWeFr", "4:00PM - 5:05PM"
    
    # Extract 2-letter segments => e.g. "MoWeFr" => ["Mo","We","Fr"]
    day_codes = []
    i = 0
    while i < len(days_part):
        chunk = days_part[i : i+2]
        day_codes.append(chunk)
        i += 2
    
    ics_days = [DAY_MAP[d] for d in day_codes if d in DAY_MAP]
    
    tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
    if not tm:
        return ics_days, None, None
    
    start_str, end_str = tm.groups()
    start_t = parse_time_12h(start_str)
    end_t   = parse_time_12h(end_str)
    
    return ics_days, start_t, end_t

def parse_time_12h(tstr):
    """
    Convert "4:00PM" => time(16,0)
    """
    tstr = tstr.strip()
    if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
        # Insert space: "4:00PM" => "4:00 PM"
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
    Shift start_date forward to the given weekday (e.g. "MO", "WE", "FR").
    """
    PY_DAY_MAP = {"MO":0, "TU":1, "WE":2, "TH":3, "FR":4, "SA":5, "SU":6}
    target_wd  = PY_DAY_MAP[wday_ics]
    current_wd = start_date.weekday()  # Monday=0..Sunday=6
    if current_wd <= target_wd:
        diff = target_wd - current_wd
    else:
        diff = 7 - (current_wd - target_wd)
    return start_date + timedelta(days=diff)

def create_events_for_course(course):
    """
    Creates ICS events in local "America/Los_Angeles" time.
    If a class meets multiple days (e.g. MoWeFr), we create *one* event with BYDAY=MO,WE,FR.
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

        # e.g. weekdays = ["MO","WE","FR"] => we want a single event with "BYDAY=MO,WE,FR"
        wday_str = ",".join(weekdays)

        # Align first occurrence to the *earliest* weekday (e.g. MO if we have MO,WE,FR)
        earliest_wd = min(weekdays, key=lambda w: ICS_DAY_ORDER.index(w))
        first_occ   = align_first_occurrence(start_date, earliest_wd)

        # Build the event
        e = Event()
        e.name = f"{course_title} ({comp} {sect})"
        e.description = f"Instructor: {instr}\nClass Number: {cnum}"
        e.location = room

        # Local Time
        tz = ZoneInfo("America/Los_Angeles")
        start_dt = datetime.combine(first_occ, start_t, tz)
        end_dt   = datetime.combine(first_occ, end_t,   tz)
        e.begin  = start_dt
        e.end    = end_dt

        # RRULE with multiple BYDAY codes
        until_utc = end_date.strftime("%Y%m%dT235900Z")
        e.extra.append(
            ContentLine(
                name="RRULE",
                value=f"FREQ=WEEKLY;BYDAY={wday_str};UNTIL={until_utc}"
            )
        )

        events.append(e)

    return events

# The day order for referencing earliest day
ICS_DAY_ORDER = ["MO","TU","WE","TH","FR","SA","SU"]
