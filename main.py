import pickle
import os.path
from urllib import request
import re
from configparser import ConfigParser

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

PATTERN1 = re.compile("\s+")
PATTERN2 = re.compile(",+")
PATTERN3 = re.compile(r"(?:(?<=\s)|^)(?:[a-z]|\d+)", re.I)

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

    global error_set
    error_set = set()
    global error_count
    error_count = 0


    (calendar_id, ical_file, lang, webhook_url, decode_fix) = config_loader()

    service = creds()
    event_list = parse_ics(ical_file, decode_fix)
    parsed_event_list = event_edit(event_list, lang)

    clear_calendar(service, calendar_id)

    insert_event(parsed_event_list, service, calendar_id, webhook_url, decode_fix)


def config_loader():
    parser = ConfigParser(allow_no_value=True)

    if os.path.isfile(CONFIG_PATH):
        parser.read(CONFIG_PATH)
    else:
        import GUI

    calendar_id = parser["SETTINGS"]["calendarId"]
    ical_url = parser["SETTINGS"]["icalURL"]
    lang = parser["SETTINGS"]["LANGUAGE"]
    global discord_integration
    discord_integration = parser["SETTINGS"]["discordIntegration"]
    decode_fix = parser["SETTINGS"]["decodeFix"]
    webhook_url = None
    if discord_integration == "y":
        webhook_url = parser["DISCORD_SETTINGS"]["webhook"]
    ical_file = request.urlopen(ical_url).read().decode("utf-8")

    return calendar_id, ical_file, lang, webhook_url, decode_fix


def insert_event(events, service, calendar_id, webhook_url):  # Adds events
    batch = service.new_batch_http_request(callback=cb_insert_event)

    # Add each event to batch
    for i, event in enumerate(events):
        batch.add(service.events().insert(calendarId=calendar_id, body=event))
    batch.execute()

    if discord_integration == "y":
        
        if error_count == 0:
            DiscordWebhook(
                url=webhook_url,
                content="Successfully updated schedule without errors",
            ).execute()
        else:
            joinedString = ", ".join([str(i) for i in error_set])
            content = (
                f"{error_count} errors, following errors found: " + joinedString
            )
            DiscordWebhook(url=webhook_url, content=content).execute()


def clear_calendar(service, calendar_id):  # Clears calendar
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


def event_edit(event_list, lang):
    del_events = []  # List for events to be deleted
    
    for i in event_list:  # Loop through each event
        i["summary"] = name_format(i["summary"])  # Format name

        # Clean up the name
        edit_name = i["summary"]
        edit_name = edit_name.replace(":  :", ":")
        edit_name = edit_name.rstrip(" : ")
        for j in PATTERN1.findall(i["summary"]):
            edit_name = edit_name.replace(j, " ")
        for j in PATTERN2.findall(i["summary"]):
            edit_name = edit_name.replace(j, ",")
        edit_name = edit_name.replace(";", "")

        # NAZILA FIX: FILTERS ENGLISH OR SWEDISH CLASSES OUT #
        if lang.lower() == "en":
            if "sv" in edit_name.lower() or "föreläsning" in edit_name.lower():
                if (
                    "tenta" not in edit_name.lower()
                    or "guest" not in edit_name.lower()
                ):
                    del_events.append(i)

        elif lang.lower() == "sv":
            if "eng" in edit_name.lower() or "lecture" in edit_name.lower():
                if (
                    "exam" not in edit_name.lower()
                    and "guest" not in edit_name.lower()
                ):
                    del_events.append(i)

        if len(edit_name) > 63:
            i["description"] = edit_name
            edit_name = edit_name[:63] + "..."
        
        i["summary"] = edit_name

    # Delete events from Calendar
    for i in del_events:
        event_list.remove(i)

    return event_list


def name_format(name):
    
    print(name)
    
    split_name = None
    # Split name and format SUMMARY in readable way
    if name[0] == "K":
        split_name = re.split("Kurs.grp: | Sign: | Moment: | Program: ", name)
        if "en" in split_name[3] and "sv" in split_name[3]:
            if len(split_name[1].split(" ")) == 1:
                return split_name[1] + " : " + split_name[2]
            else:
                return (
                    "".join(PATTERN3.findall(split_name[1])).upper()
                    + " : "
                    + split_name[2]
                )
        else:
            if len(split_name[1].split(" ")) == 1:
                return (
                    split_name[1]
                    + " : "
                    + split_name[3]
                    + " : "
                    + split_name[2]
                )
            else:
                return (
                    "".join(PATTERN3.findall(split_name[1])).upper()
                    + " : "
                    + split_name[3]
                    + " : "
                    + split_name[2]
                )

    elif name[0] == "S":
        split_name = re.split("Sign: | Moment: | Program: ", name)
        return split_name[2] + " : " + split_name[1]


def cb_insert_event(request_id, response, e):  # Callback from adding events
    global discord_integration
    if discord_integration == "y":
        if e:
            global error_set
            global error_count

            error_set.add(str(e).split("Details:")[1][2:-3])
            error_count += 1
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
    ical = Calendar.from_ical(ics)
    for i, component in enumerate(ical.walk()):
        if component.name == "VEVENT":

            event = {}
            event["summary"] = component.get("summary")
            event["location"] = component.get("location")
            event["start"] = {
                "dateTime": component.get("dtstart").dt.isoformat(),
                "timeZone": str(component.get("dtstart").dt.tzinfo)
                }
            event["end"] = {
                "dateTime": component.get("dtend").dt.isoformat(),
                "timeZone": str(component.get("dtend").dt.tzinfo)
                }
            event["sequence"] = component.get("sequence")
            try:
                event["transparency"] = component.get("transparency").lower()
                event["visibility"] = component.get("class").lower()
                event["organizer"] = {
                    "displayName": component.get("organizer").params.get("CN") or "",
                    "email": re.match("mailto:(.*)", component.get("organizer")).group(1)
                    or "",
                    }
                
                desc = component.get("description").replace("\xa0", " ")
                if "description" in event:
                    event["description"] = (
                        desc + "\r\n" + event["description"]
                    )
                else:
                    event["description"] = desc
                
                event["description"] = component.get("description")
            except AttributeError:
                pass
        
            events.append(event)
    
    return events


def creds():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(os.path.join(os.path.dirname(__file__), "token.pickle")):
        with open(
            os.path.join(os.path.dirname(__file__), "token.pickle"), "rb"
        ) as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(os.path.dirname(__file__), "credentials.json"),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(
            os.path.join(os.path.dirname(__file__), "token.pickle"), "wb"
        ) as token:
            pickle.dump(creds, token)

    return build("calendar", "v3", credentials=creds)


if __name__ == "__main__":
    main()
