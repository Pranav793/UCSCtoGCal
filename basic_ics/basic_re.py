import re


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

# We’ll split the big text block by blank lines to isolate "chunks" for each course.
# This is a simple approach; it assumes each course is separated by one or more blank lines.
chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]

courses = []
current_course = {}

for chunk in chunks:
    lines = chunk.splitlines()
    
    # Check if the chunk looks like a "Course Header"
    # e.g., "CSE 111 - Adv Programming"
    # We'll do a quick regex: starts with "CSE " or "CSE" plus some digits + " - "
    if re.match(r'^[A-Z]{2,5}\s+\d+\S*\s*-\s', lines[0]):
        # If we have a current course with partial data, push it before starting a new one
        if current_course:
            courses.append(current_course)
        current_course = {
            "course_title": lines[0],
            "status": None,
            "units": None,
            "grading": None,
            "general_education": None,
            "classes": []
        }
        continue

    # If we see a line containing "Status" or "Enrolled"/"Dropped"
    # we can detect the status, units, grading, etc.
    if "Status" in lines[0]:
        # Next lines might have status, units, grading.
        # We'll guess from the snippet that the next few lines are:
        #   <Status> e.g. Enrolled / Dropped
        #   <Units> e.g. 5.00
        #   <Grading> e.g. Graded
        # Possibly a line with "PR-E" if there's a GE requirement
        # This is *very* dependent on the snippet structure.
        idx = 1
        while idx < len(lines):
            line = lines[idx].strip()
            if line in ["Enrolled", "Dropped"]:
                current_course["status"] = line
            elif re.match(r'^\d+(\.\d+)?$', line):  # e.g. 5.00
                current_course["units"] = line
            elif "Graded" in line or "P/NP" in line:
                current_course["grading"] = line
            elif "PR-" in line:
                current_course["general_education"] = line
            idx += 1
        continue
    
    # If the chunk has "Class Nbr" in it, the following lines should be
    # the actual classes (lectures/discussions).
    if "Class Nbr" in lines[0]:
        # lines after line[0] are the actual classes
        for c_line in lines[1:]:
            c_line = c_line.strip()
            if not c_line:
                continue
            # We'll parse each line by splitting on multiple spaces
            # The snippet has columns for:
            # Class Nbr / Section / Component / Days & Times / Room / Instructor / Start/End Date
            # We'll try a rough approach to parse them. Because the "Days & Times" can have spaces
            # (like "MoWeFr 4:00PM - 5:05PM"), we’ll do a more manual approach or a broad regex.
            
            # A simplistic approach: we know 'Class Nbr', 'Section', and 'Component' are short,
            # so let's split on multiple spaces, then rejoin the "Days & Times" chunk, etc.
            parts = re.split(r'\s{2,}', c_line)  # split on 2 or more spaces
            
            # We expect something like:
            # parts[0] -> Class Nbr
            # parts[1] -> Section
            # parts[2] -> Component
            # parts[3] -> Days & Times
            # parts[4] -> Room
            # parts[5] -> Instructor
            # parts[6] -> Start/End Date
            # (But watch out for short lines with "To be Announced")
            
            if len(parts) < 7:
                # We might have a line with missing columns. We can skip or handle gracefully.
                continue
            
            class_info = {
                "class_nbr": parts[0],
                "section": parts[1],
                "component": parts[2],
                "days_times": parts[3],
                "room": parts[4],
                "instructor": parts[5],
                "start_end": parts[6],
            }
            current_course["classes"].append(class_info)

# After the loop, push the last course if present
if current_course:
    courses.append(current_course)

# Print out the final data structure
import json
print(json.dumps(courses, indent=2))
