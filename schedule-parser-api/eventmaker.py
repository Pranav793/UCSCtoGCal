# t = {'classes': [{'class_nbr': '30481',
#               'component': 'Lecture',
#               'days_times': 'MoWeFr 4:00PM - 5:05PM',
#               'instructor': 'Ethan  Sifferman',
#               'room': 'Media Theater M110',
#               'section': '01',
#               'start_end': '01/06/2025 - 03/14/2025'},
#              {'class_nbr': '33007',
#               'component': 'Discussion',
#               'days_times': 'We 10:40AM - 11:45AM',
#               'instructor': 'To be Announced',
#               'room': 'Engineer 2 194',
#               'section': '01E',
#               'start_end': '01/06/2025 - 03/14/2025'}],
#  'code': 'CSE 111',
#  'metadata': {'general_education': None,
#               'grade': None,
#               'grading': 'Graded',
#               'status': 'Enrolled',
#               'units': '5.00'},
#  'name': 'Adv Programming',
#  'title': 'CSE 111 - Adv Programming'}

# import re
# from datetime import datetime, time, timedelta
# from ics import Calendar, Event
# from ics.grammar.parse import ContentLine


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
#       - start_time as datetime.time
#       - end_time as datetime.time
    
#     Example inputs:
#       "MoWeFr 4:00PM - 5:05PM"
#       "TuTh 1:30PM - 3:05PM"
#       "We 10:40AM - 11:45AM"
#     """
#     # 1) Split the string into two parts: e.g. "MoWeFr" and "4:00PM - 5:05PM"
#     m = re.match(r'^([A-Za-z]+)\s+(.*)$', days_times_str.strip())
#     if not m:
#         # If it doesn't match, fallback or raise an error
#         return [], None, None
    
#     days_part, time_part = m.groups()  # e.g. "MoWeFr", "4:00PM - 5:05PM"
    
#     # 2) Extract each 2-letter day code from days_part: "MoWeFr" => ["Mo", "We", "Fr"]
#     #    We'll chunk every 2 chars. If your data uses "TuTh" as 4 chars, you'll need a more robust approach.
#     #    For this demo, let's assume 2 chars each.
#     day_codes = []
#     i = 0
#     while i < len(days_part):
#         day_2 = days_part[i : i+2]
#         day_codes.append(day_2)
#         i += 2
    
#     # Convert to ICS format (MO, TU, WE, etc.)
#     ics_days = []
#     for d in day_codes:
#         if d in DAY_MAP:
#             ics_days.append(DAY_MAP[d])  # e.g. "Mo" -> "MO", "We" -> "WE"
    
#     # 3) Parse time range: "4:00PM - 5:05PM"
#     tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
#     if not tm:
#         return ics_days, None, None
#     start_str, end_str = tm.groups()

#     start_t = parse_time_12h(start_str)  # convert "4:00PM" to datetime.time(16, 0)
#     end_t = parse_time_12h(end_str)      # e.g. "5:05PM" -> datetime.time(17, 5)

#     return ics_days, start_t, end_t

# def parse_time_12h(tstr):
#     """
#     Convert a 12-hour time string like "4:00PM" or "11:45AM" into a datetime.time object.
#     """
#     # We can parse with datetime.strptime if we insert a space: "4:00PM" -> "4:00 PM"
#     tstr = tstr.strip()
#     if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
#         # Insert space before AM/PM
#         tstr = tstr[:-2] + " " + tstr[-2:]  # e.g. "4:00 PM"
#         dt = datetime.strptime(tstr, "%I:%M %p")
#         return dt.time()
#     return None

# def parse_start_end_dates(date_range_str):
#     """
#     Given something like "01/06/2025 - 03/14/2025", return (start_date, end_date) as datetime.date objects.
#     """
#     m = re.match(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})', date_range_str)
#     if not m:
#         return None, None
#     start_str, end_str = m.groups()
#     start_dt = datetime.strptime(start_str, "%m/%d/%Y").date()
#     end_dt = datetime.strptime(end_str, "%m/%d/%Y").date()
#     return start_dt, end_dt



# def create_events_for_course(course):
#     """
#     Given a course dict like:
#     {
#       'classes': [
#          {'days_times': 'MoWeFr 4:00PM - 5:05PM', 'start_end': '01/06/2025 - 03/14/2025', ...},
#          ...
#       ],
#       'title': 'CSE 111 - Adv Programming',
#       ...
#     }
    
#     Return a list of ics.Event objects corresponding to each "class" meeting pattern.
#     """
#     events = []
#     course_title = course.get("title", "Untitled Course")

#     for cls_info in course["classes"]:
#         dt_str = cls_info.get("days_times")       # e.g. "MoWeFr 4:00PM - 5:05PM"
#         se_str = cls_info.get("start_end")        # e.g. "01/06/2025 - 03/14/2025"
#         room   = cls_info.get("room", "")
#         instr  = cls_info.get("instructor", "")
#         comp   = cls_info.get("component", "")
#         section= cls_info.get("section", "")
        
#         # 1) Parse the days_times => which weekdays, start time, end time
#         weekdays, start_t, end_t = parse_days_times(dt_str)
#         if not weekdays or not start_t or not end_t:
#             # If missing or invalid, skip
#             continue
        
#         # 2) Parse the date range => start_date, end_date
#         start_date, end_date = parse_start_end_dates(se_str)
#         if not start_date or not end_date:
#             continue
        
#         # Let's take the "start_date" as the first class day (we'll adjust day offset below).
#         # ICS can handle an RRULE that repeats weekly. 
#         # We can handle multiple days in one RRULE using BYDAY=MO,WE,FR, 
#         # but ics.py doesn't have super direct support for that via Python objects yet.
#         # We'll do a SINGLE BYDAY for each "Mo", "We", "Fr" for clarity.
#         # Alternatively, you can create a single event with multiple BYDAY entries, 
#         # but it's simpler to create one event per day-of-week.

#         for wday in weekdays:  # e.g. "MO", "WE", "FR"
#             e = Event()
#             # Name the event: "CSE 111 (Lecture 01)" or something
#             e.name = f"{course_title} ({comp} {section})"
#             e.description = f"Instructor: {instr}\nClass Number: {cls_info.get('class_nbr','')}"
#             e.location = room
            
#             # We'll compute the first occurrence day. 
#             # If the start_date is a Monday, but our wday is Wednesday, we shift to that Wednesday in the same week.
#             # We'll do a small function:
#             first_occ = align_first_occurrence(start_date, wday)  # returns a datetime.date
            
#             # Combine that date with the start_t and end_t for the event
#             start_dt = datetime.combine(first_occ, start_t)
#             end_dt   = datetime.combine(first_occ, end_t)
            
#             e.begin = start_dt
#             e.end   = end_dt
            
#             # Set a weekly recurrence (RRULE) until end_date
#             # ics.py can do something like: e.rrule = {"freq": "weekly", "until": <datetime>, "byday": [wday]}
#             # But it's not always documented. We'll do:
#             # e.make_all_day(False)  # ensure it's not an all-day event
#             # ics 0.7+ you can do:
#             e.extra.append(ContentLine(name="RRULE", value=f"FREQ=WEEKLY;BYDAY={wday};UNTIL={end_date.strftime('%Y%m%dT235900Z')}"))
            
#             events.append(e)
    
#     return events

# def align_first_occurrence(start_date, wday_ics):
#     """
#     Shift start_date forward until it's the correct weekday (MO/TU/WE/TH/FR/SA/SU).
#     If start_date is already that weekday, return it as is.
#     Otherwise, move to the next instance of that weekday within the same or next week.
#     """
#     # Convert ICS day to Python weekday: 
#     # Python's date.weekday() => Monday=0, Tuesday=1, ... Sunday=6
#     # We'll define a helper map:
#     PY_DAY_MAP = {"MO":0, "TU":1, "WE":2, "TH":3, "FR":4, "SA":5, "SU":6}
    
#     target_wd = PY_DAY_MAP[wday_ics]
#     current_wd = start_date.weekday()  # 0=Monday ... 6=Sunday
    
#     # If current_wd <= target_wd, shift forward target_wd - current_wd days
#     # else shift forward (7 - (current_wd - target_wd)) days
#     if current_wd <= target_wd:
#         diff = target_wd - current_wd
#     else:
#         diff = 7 - (current_wd - target_wd)
    
#     return start_date + timedelta(days=diff)


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

def parse_days_times(days_times_str):
    """
    Given something like "MoWeFr 4:00PM - 5:05PM",
    return:
      - a list of ICS weekday codes, e.g. ["MO", "WE", "FR"]
      - start_time (datetime.time)
      - end_time (datetime.time)
    """
    # 1) Separate the day combo ("MoWeFr") from the time range ("4:00PM - 5:05PM")
    m = re.match(r'^([A-Za-z]+)\s+(.*)$', days_times_str.strip())
    if not m:
        return [], None, None
    
    days_part, time_part = m.groups()
    
    # 2) Extract 2-letter day codes from days_part => e.g. "MoWeFr" -> ["Mo", "We", "Fr"]
    day_codes = []
    i = 0
    while i < len(days_part):
        day_2 = days_part[i:i+2]
        day_codes.append(day_2)
        i += 2
    
    # Convert them to ICS day codes (MO, TU, WE, etc.)
    ics_days = [DAY_MAP[d] for d in day_codes if d in DAY_MAP]
    
    # 3) Parse the time range ("4:00PM - 5:05PM")
    tm = re.match(r'(.*)\s*-\s*(.*)', time_part)
    if not tm:
        return ics_days, None, None
    
    start_str, end_str = tm.groups()
    start_t = parse_time_12h(start_str)
    end_t   = parse_time_12h(end_str)
    
    return ics_days, start_t, end_t

def parse_time_12h(tstr):
    """
    Convert "4:00PM" -> datetime.time(16, 0), etc.
    """
    tstr = tstr.strip()
    if re.match(r'^\d{1,2}:\d{2}(AM|PM)$', tstr):
        # Insert a space before AM/PM => "4:00PM" => "4:00 PM"
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

def create_events_for_course(course):
    """
    Now we produce ONE event per class entry, 
    with a multi-day BYDAY if we have multiple day codes.
    Example: "MoWeFr" => BYDAY=MO,WE,FR
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

        # 1) Parse day codes + times
        weekdays, start_t, end_t = parse_days_times(dt_str)
        if not weekdays or not start_t or not end_t:
            continue
        
        # 2) Parse date range
        start_date, end_date = parse_start_end_dates(se_str)
        if not start_date or not end_date:
            continue
        
        # 3) Build a single event with multiple BYDAY codes
        #    e.g. BYDAY=MO,WE,FR
        wday_str = ",".join(weekdays)  # "MO,WE,FR"

        # We'll pick the earliest day in weekdays to align the "first_occ" date.
        # Because if we have MO, WE, FR, we want the first occurrence to be Monday 
        # (assuming start_date <= that Monday).
        earliest_wd = min(weekdays, key=lambda d: ICS_DAY_ORDER.index(d))
        
        # Align the start_date to that earliest weekday
        first_occ = align_first_occurrence(start_date, earliest_wd)

        # Create an Event
        e = Event()
        e.name = f"{course_title} ({comp} {sect})"
        e.description = f"Instructor: {instr}\nClass Number: {cnum}"
        e.location    = room

        start_dt = datetime.combine(first_occ, start_t)
        end_dt   = datetime.combine(first_occ, end_t)
        e.begin  = start_dt
        e.end    = end_dt

        # Add an RRULE with multiple BYDAY entries
        # e.g. FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20250314T235900Z
        until_utc = end_date.strftime("%Y%m%dT235900Z")
        e.extra.append(
            ContentLine(
                name="RRULE", 
                value=f"FREQ=WEEKLY;BYDAY={wday_str};UNTIL={until_utc}"
            )
        )
        
        events.append(e)

    return events

# We define a consistent order for ICS day codes so we can find the earliest weekday easily.
ICS_DAY_ORDER = ["MO","TU","WE","TH","FR","SA","SU"]

def align_first_occurrence(start_date, wday_ics):
    """
    Shift start_date forward until it matches wday_ics (e.g. "MO", "WE", etc.).
    """
    PY_DAY_MAP = {"MO":0, "TU":1, "WE":2, "TH":3, "FR":4, "SA":5, "SU":6}
    
    target_wd  = PY_DAY_MAP[wday_ics]
    current_wd = start_date.weekday()  # Monday=0..Sunday=6

    if current_wd <= target_wd:
        diff = target_wd - current_wd
    else:
        diff = 7 - (current_wd - target_wd)
    
    return start_date + timedelta(days=diff)
