from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List, Optional
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from textparser import parse_schedule_text
from localeventmaker import create_events_for_course
from datetime import date, timedelta
from ics import Calendar, Event
from pprint import pprint


app = FastAPI()

origins = [
    "http://localhost:3000"
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

    cal = Calendar()

    for course in parsed_courses:
        events = create_events_for_course(course)
        for e in events:
            cal.events.add(e)
    
    filename = "my.ics"
    with open(filename, 'w') as my_file:
        my_file.writelines(cal.serialize_iter())

    # 3. Return the file as an attachment
    # "media_type" tells the browser it's a text/calendar (ICS) file
    return FileResponse(
        path=filename,
        media_type="text/calendar",
        filename="my_schedule.ics"
    )

