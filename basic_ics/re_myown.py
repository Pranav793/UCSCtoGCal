import re
from pprint import pprint

text = """
CSE 111 - Adv Programming

Status  Units   Grading Grade   Deadlines
Enrolled
5.00
Graded
 
Academic Calendar Deadlines
Class Nbr    Section Component   Days & Times          Room                  Instructor               Start/End Date
30481        01      Lecture     MoWeFr 4:00PM - 5:05PM Media Theater M110   Ethan  Sifferman         01/06/2025 - 03/14/2025
33007        01E     Discussion  We 10:40AM - 11:45AM   Engineer 2 194       To be Announced          01/06/2025 - 03/14/2025

CSE 115B - Software Design Pro

Status  Units   Grading Grade   General Education  Deadlines
Enrolled
5.00
Graded
PR-E

Academic Calendar Deadlines
Class Nbr    Section Component   Days & Times        Room               Instructor            Start/End Date
30476        01      Lecture     TuTh 11:40AM - 1:15PM Merrill Acad 102  Richard K Jullig      01/06/2025 - 03/14/2025

CSE 123A - Engr Design Proj I

Status  Units   Grading Grade   General Education  Deadlines
Dropped
5.00
Graded
PR-E

Academic Calendar Deadlines
Class Nbr    Section Component   Days & Times       Room              Instructor                  Start/End Date
32151        01      Lecture     TuTh 5:20PM - 6:55PM Soc Sci 2 075    David Charles Harrison      01/06/2025 - 03/14/2025

CSE 185E - Tech Writ Comp Engs

Status  Units   Grading Grade   Deadlines
Enrolled
5.00
Graded

Academic Calendar Deadlines
Class Nbr    Section Component   Days & Times          Room               Instructor            Start/End Date
32153        01E     Discussion  Tu 7:10PM - 8:15PM    Merrill Acad 132   To be Announced       01/06/2025 - 03/14/2025
32158        01      Lecture     TuTh 1:30PM - 3:05PM  ClassroomUnit 001  Gerald Bennett Moulds 01/06/2025 - 03/14/2025
""".strip()

def parse_class_line(line: str):
    """
    Parse a line like:
      30481        01      Lecture     MoWeFr 4:00PM - 5:05PM Media Theater M110  Ethan Sifferman  01/06/2025 - 03/14/2025
    even with inconsistent whitespace, splitting out:
      - class_nbr, section, component
      - days_times, room, instructor
      - start_end (date range)
    """

    line = line.strip()
    if not line:
        return None

    # 1) Parse the first 3 columns from the left
    #    We'll assume these are short single tokens (e.g., "30481", "01E", "Lecture").
    parts = line.split(None, 3)  # split on ANY whitespace, up to 3 splits
    if len(parts) < 4:
        return None
    class_nbr, section, component, remainder = parts

    # 2) Extract the date range from the right using a regex
    #    pattern like "01/06/2025 - 03/14/2025"
    date_pattern = r'(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})\s*$'
    match_date = re.search(date_pattern, remainder)
    if match_date:
        start_end = match_date.group(1).strip()
        # Remove the date portion from remainder
        middle = remainder[: match_date.start()].strip()
    else:
        # No recognized date range
        start_end = ""
        middle = remainder

    # 3) Extract "days & times" from the start of 'middle'
    #    A pattern: e.g. "MoWeFr 4:00PM - 5:05PM" or "TuTh 1:30PM - 3:05PM"
    #    We'll guess a quick regex for day/time: 
    #      - Up to ~6 letters of day combos (MoWeFr, TuTh, etc.)
    #      - a start time, "4:00PM"
    #      - a dash
    #      - an end time, "5:05PM"
    #    Then optional building name might follow. 
    days_pattern = r'^([A-Za-z]{2,6}\s+\d{1,2}:\d{2}(?:AM|PM)\s*-\s*\d{1,2}:\d{2}(?:AM|PM))'
    # Explanation: 
    #  ^ => start of string
    #  [A-Za-z]{2,6} => e.g., "MoWeFr" or "TuTh" etc.
    #  \s+\d{1,2}:\d{2}(?:AM|PM) => e.g. " 4:00PM"
    #  \s*-\s* => dash with optional spaces
    #  \d{1,2}:\d{2}(?:AM|PM) => e.g. "5:05PM"

    match_days = re.search(days_pattern, middle)
    if match_days:
        days_times = match_days.group(1)
        after_days = middle[len(days_times):].strip()
    else:
        # If we can't find a time range at the start, maybe the entire 'middle' is just "days_times"
        days_times = middle
        after_days = ""

    # 4) Heuristic to split "after_days" (the remainder) into "room" + "instructor"
    #    Because "Media Theater M110" might appear as multiple tokens, we can't just
    #    do a single split. We'll do a few special checks:

    room = ""
    instructor = ""

    if not after_days:
        # Nothing left to parse => no room or instructor
        pass
    else:
        # Check if "To be Announced" is present:
        if "To be Announced" in after_days:
            # Then we can guess everything before that phrase is the room
            # and the instructor is "To be Announced."
            idx = after_days.index("To be Announced")
            # everything before that is room
            room = after_days[:idx].strip()
            instructor = "To be Announced"
        else:
            # Otherwise, let's try the "last 2 or 3 tokens are an instructor name" approach:
            tokens = after_days.split()
            # If there's 3+ tokens, the last 2 or 3 might be someone's name. 
            # E.g., "Ethan Sifferman" (2 tokens) or "Gerald Bennett Moulds" (3 tokens).
            # We try 2 or 3 from the end in a small loop to see which looks plausible.
            # We'll define "plausible" as not containing digits (assuming building codes have digits).
            
            # For example, if the last token has digits => more likely part of "room".
            # We'll do a small function to see if a token is "namey."
            def is_name_token(tok):
                # If it has digits or is < 2 chars, it might not be a name
                if re.search(r'\d', tok):
                    return False
                return True

            # We'll try to find the largest suffix of tokens that are "namey."
            # Start from the last token backwards:
            suffix_length = 0
            for i in range(1, min(4, len(tokens))+1):  # up to 3 tokens from the end
                tok = tokens[-i]
                if is_name_token(tok):
                    suffix_length += 1
                else:
                    # as soon as we find a non-name token, break
                    break
            
            if suffix_length == 0:
                # means last token is not namey => we guess there's no instructor?
                room = " ".join(tokens)
                instructor = ""
            else:
                # instructor is the "suffix_length" tokens from the end
                instructor_tokens = tokens[-suffix_length:]
                instructor = " ".join(instructor_tokens)
                room_tokens = tokens[:-suffix_length]
                room = " ".join(room_tokens)

    # 5) Build the final dict
    return {
        "class_nbr": class_nbr,
        "section": section,
        "component": component,
        "days_times": days_times.strip(),
        "room": room.strip(),
        "instructor": instructor.strip(),
        "start_end": start_end.strip()
    }


def parse_course_chunk(chunk):
    course = {}

    split_sections = chunk.split('\n')

    sections = []
    current_section = []
    
    for item in split_sections:
        if item == "" or item == " ":
            # We've hit a separator - end the current chunk
            if current_section:
                sections.append(current_section)
                current_section = []
        else:
            # Normal item, add it to the current chunk
            current_section.append(item)
    
    # If there's any leftover items after the loop, append them as a chunk
    if current_section:
        sections.append(current_section)

    print(sections)
    title_section = sections[0]
    metadata_section = sections[1]
    info_section = sections[2]

    # TITLE SECTION
    course['title'] = title_section[0]
    course['code'] = title_section[0].split(' - ')[0]
    course['name'] = title_section[0].split(' - ')[1]

    # META DATA
    metadata = {}
    metadata['status'] = metadata_section[1]
    metadata['units'] = metadata_section[2]
    course["metadata"] = metadata


    for i in range(2, len(info_section)):
        parsed = parse_class_line(info_section[i])
        course["info"] = parsed

    return course



def parse_schedule_text(text):

    text = text.strip()

    # We’ll split the big text block by blank lines to isolate "chunks" for each course.
    # This is a simple approach; it assumes each course is separated by one or more blank lines.
    pattern = r'(?=^[A-Z]{2,5}\s+\d+\S*\s*-\s)'

    # Use re.split with the pattern, enabling MULTILINE (^ matches start of lines in multi-line text)
    course_chunks = re.split(pattern, text, flags=re.MULTILINE)

    # Clean up empty strings or leading/trailing whitespace
    course_chunks = [chunk.strip() for chunk in course_chunks if chunk.strip()]

    parsed_chunks = [parse_course_chunk(chunk) for chunk in course_chunks]

    for i, chunk in enumerate(parsed_chunks):
        print(f"--- Course Block {i+1} ---")
        print(chunk)
        print()

    return parsed_chunks