from datetime import date, timedelta
from ics import Calendar, Event
from ics.grammar.parse import ContentLine
# Create a new calendar
c = Calendar()

# Create an event
e = Event()
e.name = "My Cool Event (Today)"
e.description = "THIS IS REALL COOL"
e.location = "the location of the cool event"
# Generate start/end for today:
#  - Start at 00:00:00 (midnight)
#  - End an hour later (01:00:00)
today_str = date.today().strftime("%Y-%m-%d")
e.begin = f"{today_str} 00:00:00"
e.end = f"{today_str} 01:00:00"
end_date = (date.today() + timedelta(weeks=3)).strftime("%Y%m%dT000000Z")


e.extra.append(ContentLine(name="RRULE", value=f"FREQ=WEEKLY;UNTIL={end_date}"))

# e.extra.append(
#                 (
#                     "RRULE",
#                     f"FREQ=WEEKLY;UNTIL={end_date}"
#                 )
#             )

# Add event to calendar
c.events.add(e)
print(c.events)
# Save to an .ics file
with open('my.ics', 'w') as my_file:
    my_file.writelines(c.serialize_iter())

print("Created an event for today in my.ics!")
