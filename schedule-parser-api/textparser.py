import re
from pprint import pprint
t = 'CSE 111 - Adv Programming\n\t\t\nStatus\tUnits\tGrading\tGrade\tDeadlines\nEnrolled\n5.00\nGraded\n \nAcademic Calendar Deadlines\nClass Nbr\tSection\tComponent\tDays & Times\tRoom\tInstructor\tStart/End Date\n30481\n01\nLecture\nMoWeFr 4:00PM - 5:05PM\nMedia Theater M110\nEthan  Sifferman\n01/06/2025 - 03/14/2025\n33007\n01E\nDiscussion\nWe 10:40AM - 11:45AM\nEngineer 2 194\nTo be Announced\n01/06/2025 - 03/14/2025\nCSE 115B - Software Design Pro\n\t\t\nStatus\tUnits\tGrading\tGrade\tGeneral Education\tDeadlines\nEnrolled\n5.00\nGraded\n \nPR-E\nAcademic Calendar Deadlines\nClass Nbr\tSection\tComponent\tDays & Times\tRoom\tInstructor\tStart/End Date\n30476\n01\nLecture\nTuTh 11:40AM - 1:15PM\nMerrill Acad 102\nRichard K Jullig\n01/06/2025 - 03/14/2025\nCSE 123A - Engr Design Proj I\n\t\t\nStatus\tUnits\tGrading\tGrade\tGeneral Education\tDeadlines\nDropped\n5.00\nGraded\n \nPR-E\nAcademic Calendar Deadlines\nClass Nbr\tSection\tComponent\tDays & Times\tRoom\tInstructor\tStart/End Date\n32151\n01\nLecture\nTuTh 5:20PM - 6:55PM\nSoc Sci 2 075\nDavid Charles Harrison\n01/06/2025 - 03/14/2025\nCSE 185E - Tech Writ Comp Engs\n\t\t\nStatus\tUnits\tGrading\tGrade\tDeadlines\nEnrolled\n5.00\nGraded\n \nAcademic Calendar Deadlines\nClass Nbr\tSection\tComponent\tDays & Times\tRoom\tInstructor\tStart/End Date\n32153\n01E\nDiscussion\nTu 7:10PM - 8:15PM\nMerrill Acad 132\nTo be Announced\n01/06/2025 - 03/14/2025\n32158\n01\nLecture\nTuTh 1:30PM - 3:05PM\nClassroomUnit 001\nGerald Bennett Moulds\n01/06/2025 - 03/14/2025'

def parse_schedule_text(text: str, onlyenrolledcourses: bool):
    """
    Parse the entire schedule text into a list of course dictionaries.
    """
    # 1) Split the input into 'course chunks' by matching lines that look like "CSE 111 - Adv Programming"
    #    Pattern: 2-5 uppercase letters, space, digits (optionally with letters), space, dash, space...
    pattern = r'(?=^[A-Z]{2,5}\s+\d+\S*\s*-\s)'
    course_chunks = re.split(pattern, text.strip(), flags=re.MULTILINE)

    # Remove any empty strings
    course_chunks = [chunk.strip() for chunk in course_chunks if chunk.strip()]

    # Parse each chunk
    print("onlyenrolledcourses", onlyenrolledcourses)
    courses = []
    for chunk in course_chunks:
        course = parse_course_chunk(chunk)
        if course:
            courses.append(course)

    print(courses)
    return courses


def parse_course_chunk(chunk: str):
    """
    Given the text for a single course, parse out:
      - title
      - code (e.g. "CSE 111")
      - name (e.g. "Adv Programming")
      - metadata: {status, units, grading, grade, general_education}
      - classes: list of class dictionaries (class_nbr, section, component, days_times, room, instructor, start_end)
    """
    lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
    if not lines:
        return None

    # 1) First line => course title (e.g. "CSE 111 - Adv Programming")
    title_line = lines[0]
    course_title = title_line
    # Split out code vs. name if you want them separate
    if " - " in title_line:
        code_part, name_part = title_line.split(" - ", 1)
    else:
        code_part, name_part = title_line, ""  # fallback if no " - "

    # Initialize the course dict
    course = {
        "title": course_title,
        "code": code_part,
        "name": name_part,
        "metadata": {
            "status": None,
            "units": None,
            "grading": None,
            "grade": None,
            "general_education": None,
        },
        "classes": []
    }

    # 2) Read lines to fill in metadata until we see "Academic Calendar Deadlines"
    idx = 1
    while idx < len(lines):
        line = lines[idx]
        if "Academic Calendar Deadlines" in line:
            idx += 1  # move past that line
            break

        # Check if line is "Enrolled"/"Dropped"
        if line in ["Enrolled", "Dropped"]:
            course["metadata"]["status"] = line
        # If it's numeric, likely units
        elif re.match(r'^\d+(\.\d+)?$', line):
            course["metadata"]["units"] = line
        # "Graded" or "P/NP"
        elif "Graded" in line or "P/NP" in line:
            course["metadata"]["grading"] = line
        # A letter grade like A-, B+, etc.
        elif re.match(r'^[ABCDFW][+\-]?$|^P$|^NP$', line):
            course["metadata"]["grade"] = line
        # If it starts with "PR-" (e.g. "PR-E")
        elif re.match(r'^PR-', line):
            course["metadata"]["general_education"] = line

        idx += 1

    # 3) Parse the class table lines (7 lines per class)
    #    Format for each class:
    #      (1) Class Nbr
    #      (2) Section
    #      (3) Component
    #      (4) Days & Times
    #      (5) Room
    #      (6) Instructor
    #      (7) Start/End Date

    while idx < len(lines):
        # If the next line *is* the table header, skip it
        if "Class Nbr" in lines[idx]:
            idx += 1
            continue

        # If fewer than 7 lines remain, we can't parse a full class => break
        if (idx + 6) >= len(lines):
            break

        class_nbr    = lines[idx].strip()
        section      = lines[idx+1].strip()
        component    = lines[idx+2].strip()
        days_times   = lines[idx+3].strip()
        room         = lines[idx+4].strip()
        instructor   = lines[idx+5].strip()
        start_end    = lines[idx+6].strip()

        idx += 7  # move to next potential class

        class_info = {
            "class_nbr": class_nbr,
            "section": section,
            "component": component,
            "days_times": days_times,
            "room": room,
            "instructor": instructor,
            "start_end": start_end
        }

        course["classes"].append(class_info)

    return course

