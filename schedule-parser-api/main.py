from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List, Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from textparser import parse_schedule_text
from localeventmaker import create_events_for_course
from calendarmaker import build_calendar
from datetime import date, timedelta
from ics import Calendar, Event
from pprint import pprint
import fileinput


app = FastAPI()

origins = [
    "https://ucscschedtocalendar.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Define your request payload structure
class ScheduleRequest(BaseModel):
    scheduleText: str

# Define what the parsed result might look like
# For example, a list of Course objects...
class ClassInfo(BaseModel):
    class_nbr: str
    section: str
    component: str
    days_times: str
    room: str
    instructor: str
    start_end: str

class Course(BaseModel):
    course_title: str
    status: Optional[str] = None
    units: Optional[str] = None
    grading: Optional[str] = None
    general_education: Optional[str] = None
    classes: List[ClassInfo] = []



@app.get('/')
async def check():
    return 'hello'

@app.get('/info')
async def info():
    return """Hi! My name is Pranav, and I built this because I am tired of always trying to put my UCSC schedule into my Google Calendar Manually.
    It turns out I could make this 30 minute problem into a 2 day problem! This is also my first time deploying anything and have it run live, so contact me at ppurathe@ucsc.edu if there are any issues!"""

# @app.post("/parseSchedule", response_model=List[Course])
@app.post("/parseSchedule")
def parse_schedule(payload: ScheduleRequest):
    """
    Endpoint to parse the UCSC schedule text.
    Expects JSON: { "scheduleText": "CSE 111 - Adv Programming\n..." }
    Returns a list of Course objects in JSON.
    """
    # 1. Extract the schedule text from the request
    schedule_text = payload.scheduleText

    # 2. Call your actual parser function
    parsed_courses = parse_schedule_text(schedule_text)

    # cal = Calendar()

    # for course in parsed_courses:
    #     events = create_events_for_course(course)
    #     for e in events:
    #         cal.events.add(e)

    cal = build_calendar(parsed_courses)
    
    filename = "my.ics"
    with open(filename, 'w') as my_file:
        my_file.writelines(cal.serialize_iter())
        # my_file.replace("DTSTART;TZID=AMERICA/LOS_ANGELES", "DTSTART;TZID=America/Los_Angeles")
        # my_file.replace("DTEND;TZID=AMERICA/LOS_ANGELES", "DTEND;TZID=America/Los_Angeles")

    with fileinput.FileInput(filename, inplace=True, backup='.bak') as file:
        for line in file:
            print(line.replace("DTSTART;TZID=AMERICA/LOS_ANGELES", "DTSTART;TZID=America/Los_Angeles"), end='')
        for line in file:
            print(line.replace("DTEND;TZID=AMERICA/LOS_ANGELES", "DTEND;TZID=America/Los_Angeles"), end='')

    

    # 3. Return the file as an attachment
    # "media_type" tells the browser it's a text/calendar (ICS) file
    return FileResponse(
        path=filename,
        media_type="text/calendar",
        filename="my_schedule.ics"
    )

