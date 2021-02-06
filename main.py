import datetime
import json
import pickle
import os.path
from googleapiclient import http
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from urllib import parse, request
import re
from icalendar import Calendar
from google.auth.transport.requests import Request
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

CALENDAR_ID = "ep55du49memdv685dupovlp6kk@group.calendar.google.com"

ICAL_URL = "https://schema.hkr.se/setup/jsp/SchemaICAL.ics?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TBSE2+2020+36+100+NML+en"
ICAL_FILE = request.urlopen(ICAL_URL).read().decode("utf-8")

PATTERN1 = re.compile("\s+")
PATTERN2 = re.compile(",+")


def main():
    service = creds()
    cal = event_edit()

    clearCalendar(service)

    open("calendar.ics", "wb").write(cal.to_ical())

    addEvents(service)


def addEvents(service):  # Adds each event from the ics file
    events = parse_ics("calendar.ics")  # Parses file

    batch = service.new_batch_http_request(callback=cb_insert_event)

    # Add each event to batch
    for i, event in enumerate(events):
        batch.add(service.events().insert(calendarId=CALENDAR_ID, body=event))
    batch.execute()


def clearCalendar(service):  # Clears calendar
    # Get current available events
    events = (
        service.events()
        .list(calendarId=CALENDAR_ID, singleEvents=True)
        .execute()
    )

    batch = service.new_batch_http_request()

    # Add delete call for each event to batch
    for event in events["items"]:
        eId = event["id"]
        batch.add(service.events().delete(calendarId=CALENDAR_ID, eventId=eId))

    batch.execute()


def event_edit():
    # ics to Calendar object
    cal = Calendar.from_ical(ICAL_FILE)

    del_events = []  # List for events to be deleted
    for i in cal.subcomponents:  # Loop through each event
        i["summary"] = name_format(i["summary"])  # Format name

        # Clean up the name
        editName = i["summary"]
        editName = editName.replace(":  :", ":")
        editName = editName.rstrip(" : ")
        for j in PATTERN1.findall(i["summary"]):
            editName = editName.replace(j, " ")
        for j in PATTERN2.findall(i["summary"]):
            editName = editName.replace(j, ",")

        # Add events that are Swedish classes to delete list
        if (
            "sv" in editName.lower()
            or "föreläsning" in editName.lower()
            and (
                "tenta" not in editName.lower()
                and "guest" not in editName.lower()
            )
        ):
            del_events.append(i)
        i["summary"] = editName

    # Delete events from Calendar
    for i in del_events:
        cal.subcomponents.remove(i)

    return cal


def name_format(name):
    split_name = None
    # Split name and format SUMMARY in readable way
    if name[0] == "K":
        split_name = re.split("Kurs.grp: | Sign: | Moment: | Program: ", name)
        return split_name[1] + " : " + split_name[3] + " : " + split_name[2]

    elif name[0] == "S":
        split_name = re.split("Sign: | Moment: | Program: ", name)
        return split_name[2] + " : " + split_name[1]


def cb_insert_event(request_id, response, e):  # Callback from adding events
    summary = (
        response["summary"] if response and "summary" in response else "?"
    )
    if not e:
        print("({}) - Insert event {}".format(request_id, summary))
    else:
        print("({}) - Exception {}".format(request_id, e))


def parse_ics(ics):  # Parses ics file into list of event dicts
    events = []
    with open(ics, "r") as rf:
        ical = Calendar().from_ical(rf.read())
        ical_config = dict(ical.sorted_items())
        for i, comp in enumerate(ical.walk()):
            if comp.name == "VEVENT":
                event = {}
                for name, prop in comp.property_items():

                    if name in ["SUMMARY", "LOCATION"]:
                        event[name.lower()] = (
                            prop.to_ical()
                            .decode("utf-8")
                            .encode("latin-1")
                            .decode("utf-8")
                        )

                    elif name == "DTSTART":
                        event["start"] = {
                            "dateTime": prop.dt.isoformat(),
                            "timeZone": str(prop.dt.tzinfo),
                        }

                    elif name == "DTEND":
                        event["end"] = {
                            "dateTime": prop.dt.isoformat(),
                            "timeZone": str(prop.dt.tzinfo),
                        }

                    elif name == "SEQUENCE":
                        event[name.lower()] = prop

                    elif name == "TRANSP":
                        event["transparency"] = prop.lower()

                    elif name == "CLASS":
                        event["visibility"] = prop.lower()

                    elif name == "ORGANIZER":
                        event["organizer"] = {
                            "displayName": prop.params.get("CN") or "",
                            "email": re.match("mailto:(.*)", prop).group(1)
                            or "",
                        }

                    elif name == "DESCRIPTION":
                        desc = (
                            prop.to_ical()
                            .decode("utf-8")
                            .encode("latin-1")
                            .decode("utf-8")
                        )
                        desc = desc.replace(u"\xa0", u" ")
                        if name.lower() in event:
                            event[name.lower()] = (
                                desc + "\r\n" + event[name.lower()]
                            )
                        else:
                            event[name.lower()] = desc

                    elif name == "X-ALT-DESC" and "description" not in event:
                        soup = BeautifulSoup(prop, "lxml")
                        desc = soup.body.text.replace(u"\xa0", u" ")
                        if "description" in event:
                            event["description"] += "\r\n" + desc
                        else:
                            event["description"] = desc

                    elif name == "ATTENDEE":
                        if "attendees" not in event:
                            event["attendees"] = []
                        RSVP = prop.params.get("RSVP") or ""
                        RSVP = "RSVP={}".format(
                            "TRUE:{}".format(prop) if RSVP == "TRUE" else RSVP
                        )
                        ROLE = prop.params.get("ROLE") or ""
                        event["attendees"].append(
                            {
                                "displayName": prop.params.get("CN") or "",
                                "email": re.match("mailto:(.*)", prop).group(1)
                                or "",
                                "comment": ROLE
                                # 'comment': '{};{}'.format(RSVP, ROLE)
                            }
                        )

                    # VALARM: only remind by UI popup
                    elif name == "ACTION":
                        event["reminders"] = {"useDefault": True}

                    else:
                        # print(name)
                        pass

                events.append(event)

    return events


def creds():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)


if __name__ == "__main__":
    main()