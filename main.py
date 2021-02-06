from __future__ import print_function
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

# EXAMPLE OF EVENT STRUCTURE #
# BEGIN:VEVENT
# CREATED:20201111T070918Z
# SEQUENCE:5
# X-GWSHOW-AS:BUSY
# DTSTAMP:20210205T014240Z
# DTEND:20210205T143000Z
# LAST-MODIFIED:20210108T150756Z
# LOCATION:ZOOM
# DTSTART:20210205T114500Z
# STATUS:CONFIRMED
# SUMMARY:Kurs.grp: Metoder för hållbar programmering Sign: NNA Moment: Workshop 1 (Grupp C) Program: TBSE2 2020 36 100 NML en
# TRANSP:OPAQUE
# UID:BokningsId_20201111_000000019
# END:VEVENT
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

CALENDAR_ID = "ep55du49memdv685dupovlp6kk@group.calendar.google.com"

ICAL_URL = "https://schema.hkr.se/setup/jsp/SchemaICAL.ics?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TBSE2+2020+36+100+NML+en"
ICAL_FILE = request.urlopen(ICAL_URL).read().decode("utf-8")

PATTERN1 = re.compile("\s+")
PATTERN2 = re.compile(",+")


def main():
    service = creds()
    cal = event_edit()

    open("calendar.ics", "wb").write(cal.to_ical())

    events = parse_ics("calendar.ics")

    batch = service.new_batch_http_request(callback=cb_insert_event)

    for i, event in enumerate(events):
        batch.add(service.events().insert(calendarId=CALENDAR_ID, body=event))
    batch.execute()


def event_edit():
    cal = Calendar.from_ical(ICAL_FILE)

    del_events = []
    for i in cal.subcomponents:
        i["summary"] = name_format(i["summary"])
        editName = i["summary"]
        editName = editName.replace(":  :", ":")
        editName = editName.rstrip(" : ")
        for j in PATTERN1.findall(i["summary"]):
            editName = editName.replace(j, " ")
        for j in PATTERN2.findall(i["summary"]):
            editName = editName.replace(j, ",")
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

    for i in del_events:
        cal.subcomponents.remove(i)

    return cal


def name_format(name):
    split_name = None
    if name[0] == "K":
        split_name = re.split("Kurs.grp: | Sign: | Moment: | Program: ", name)
        return split_name[1] + " : " + split_name[3] + " : " + split_name[2]

    elif name[0] == "S":
        split_name = re.split("Sign: | Moment: | Program: ", name)
        return split_name[2] + " : " + split_name[1]


def cb_insert_event(request_id, response, e):
    summary = (
        response["summary"] if response and "summary" in response else "?"
    )
    if not e:
        print("({}) - Insert event {}".format(request_id, summary))
    else:
        print("({}) - Exception {}".format(request_id, e))


def parse_ics(ics):
    events = []
    with open(ics, "r") as rf:
        ical = Calendar().from_ical(rf.read())
        ical_config = dict(ical.sorted_items())
        for i, comp in enumerate(ical.walk()):
            if comp.name == "VEVENT":
                event = {}
                for name, prop in comp.property_items():

                    if name in ["SUMMARY", "LOCATION"]:
                        event[name.lower()] = prop.to_ical().decode("utf-8")

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
                        desc = prop.to_ical().decode("utf-8")
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