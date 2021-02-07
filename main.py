import pickle
import os.path
from urllib import request
import re
from configparser import ConfigParser

CONFIG_PATH = "config.ini"

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

PATTERN1 = re.compile("\s+")
PATTERN2 = re.compile(",+")

if not os.path.isfile(CONFIG_PATH):
    os.system(
        "pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib"
    )
    os.system("pip install icalendar")
    os.system("pip install beautifulsoup4")
    os.system("pip install discord-webhook")

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from icalendar import Calendar
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook


def main():

    (
        calendar_id,
        ical_file,
        lang,
        webhook_url,
    ) = configLoader()

    service = creds()
    cal = event_edit(ical_file, lang)

    clearCalendar(service, calendar_id)

    open("calendar.ics", "wb").write(cal.to_ical())

    addEvents(service, calendar_id, webhook_url)


def configLoader():
    parser = ConfigParser(allow_no_value=True)

    if os.path.isfile(CONFIG_PATH):
        parser.read(CONFIG_PATH)
    else:
        with open(CONFIG_PATH, "w") as f:
            calendarId = input("Enter Google Calendar ID: ")
            icalURL = input("Enter Kronox iCal file URL: ")
            lang = input(
                "Enter language of the classes you attend. Simply press enter if you wish to see all classes (en/sv): "
            )
            discordIntegration = input(
                "Do you wish to setup a Discord Webhook for status updates? (y/n): "
            ).lower()

            parser.add_section("SETTINGS")
            parser.set("SETTINGS", "calendarId", calendarId)
            parser.set("SETTINGS", "icalURL", icalURL)
            parser.set("SETTINGS", "language", lang)
            parser.set("SETTINGS", "discordIntegration", discordIntegration)
            if discordIntegration == "y":
                parser.add_section("DISCORD_SETTINGS")
                parser.set(
                    "DISCORD_SETTINGS",
                    "webhook",
                    input("Please enter Discord webhook URL: "),
                )
            parser.write(f)

    calendar_id = parser["SETTINGS"]["calendarId"]
    ical_url = parser["SETTINGS"]["icalURL"]
    lang = parser["SETTINGS"]["LANGUAGE"]
    global discord_integration
    discord_integration = parser["SETTINGS"]["discordIntegration"]
    webhook_url = None
    if discord_integration == "y":
        webhook_url = parser["DISCORD_SETTINGS"]["webhook"]
    ical_file = request.urlopen(ical_url).read().decode("utf-8")

    return calendar_id, ical_file, lang, webhook_url


def addEvents(service, calendar_id, webhook_url):  # Adds each event
    events = parse_ics("calendar.ics")  # Parses file

    batch = service.new_batch_http_request(callback=cb_insert_event)

    # Add each event to batch
    for i, event in enumerate(events):
        batch.add(service.events().insert(calendarId=calendar_id, body=event))
    batch.execute()

    global discord_integration

    if discord_integration == "y":
        global errorSet
        errorSet = set()

        global errorCount
        errorCount = 0

        if errorCount == 0:
            DiscordWebhook(
                url=webhook_url,
                content="Successfully updated schedule without errors",
            ).execute()
        else:
            joinedString = ", ".join([str(i) for i in errorSet])
            content = (
                f"{errorCount} errors, following errors found: " + joinedString
            )
            DiscordWebhook(url=webhook_url, content=content).execute()


def clearCalendar(service, calendar_id):  # Clears calendar
    # Get current available events
    events = (
        service.events()
        .list(calendarId=calendar_id, singleEvents=True)
        .execute()
    )

    batch = service.new_batch_http_request()

    # Add delete call for each event to batch
    for event in events["items"]:
        eId = event["id"]
        batch.add(service.events().delete(calendarId=calendar_id, eventId=eId))

    batch.execute()


def event_edit(ical_file, lang):
    # ics to Calendar object
    cal = Calendar.from_ical(ical_file)

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

        # NAZILA FIX: FILTERS ENGLISH OR SWEDISH CLASSES OUT #
        if lang.lower() == "en":
            if (
                "sv" in editName.lower()
                or "föreläsning" in editName.lower()
                and (
                    "tenta" not in editName.lower()
                    and "guest" not in editName.lower()
                )
            ):
                del_events.append(i)

        elif lang.lower() == "sv":
            if "eng" in editName.lower() and (
                "exam" not in editName.lower()
                and "guest" not in editName.lower()
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
    global discord_integration
    if discord_integration == "y":
        if e:
            global errorSet
            global errorCount

            errorSet.add(str(e).split("Details:")[1][2:-3])
            errorCount += 1
    else:
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
                        desc = desc.replace("\xa0", " ")
                        if name.lower() in event:
                            event[name.lower()] = (
                                desc + "\r\n" + event[name.lower()]
                            )
                        else:
                            event[name.lower()] = desc

                    elif name == "X-ALT-DESC" and "description" not in event:
                        soup = BeautifulSoup(prop, "lxml")
                        desc = soup.body.text.replace("\xa0", " ")
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