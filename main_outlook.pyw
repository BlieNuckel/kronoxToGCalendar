import os.path
import urllib
import re
from configparser import ConfigParser
import subprocess
import ssl
import webbrowser
import requests
from gui import get_token_url

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

SCOPES = [
    "https://graph.microsoft.com/offline_access",
    "https://graph.microsoft.com/Calendar.ReadWrite",
    "https://graph.microsoft.com/User.Read",
]

PATTERN1 = re.compile("\s+")
PATTERN2 = re.compile(",+")
PATTERN3 = re.compile(r"(?:(?<=\s)|^)(?:[a-z]|\d+)", re.I)

# if not os.path.isfile(CONFIG_PATH):
#     subprocess.call('"../batch/install_requirements.bat"')

from icalendar import Calendar
from discord_webhook import DiscordWebhook
from O365 import MSGraphProtocol
from O365.connection import Connection
from O365.account import Account
from O365.utils.token import FileSystemTokenBackend


def main():

    global error_set
    error_set = set()
    global error_count
    error_count = 0

    (calendar_id, ical_file, lang, webhook_url) = config_loader()

    account = creds()
    event_list = parse_ics(ical_file)
    parsed_event_list = event_edit(event_list, lang)

    clear_calendar(account, calendar_id)

    insert_event(parsed_event_list, account, calendar_id, webhook_url)


def config_loader():
    parser = ConfigParser(allow_no_value=True)

    if os.path.isfile(CONFIG_PATH):
        parser.read(CONFIG_PATH)
    else:
        import GUI

        parser.read(CONFIG_PATH)

    calendar_name = parser["SETTINGS"]["calendarId"]
    ical_url = parser["SETTINGS"]["icalURL"]
    lang = parser["SETTINGS"]["LANGUAGE"]
    global discord_integration
    discord_integration = parser["SETTINGS"]["discordIntegration"]
    webhook_url = None
    if discord_integration == "y":
        webhook_url = parser["DISCORD_SETTINGS"]["webhook"]
    myssl = ssl.create_default_context()
    myssl.check_hostname = False
    myssl.verify_mode = ssl.CERT_NONE
    ical_file = (
        urllib.request.urlopen(ical_url, context=myssl).read().decode("utf-8")
    )

    return calendar_name, ical_file, lang, webhook_url


def insert_event(events, service, calendar_id, webhook_url):  # Adds events
    batch = service.new_batch_http_request(callback=cb_insert_event)

    # Add each event to batch
    for i, event in enumerate(events):
        batch.add(service.events().insert(calendarId=calendar_id, body=event))
    batch.execute()

    if discord_integration == "y":

        if error_count > 0:
            joinedString = ", ".join([str(i) for i in error_set])
            content = (
                f"{error_count} errors, following errors found: "
                + joinedString
            )
            DiscordWebhook(url=webhook_url, content=content).execute()


def clear_calendar(account, calendar_name):  # Clears calendar
    # Get current available events
    schedule = account.schedule()
    calendar = schedule.get_calendar(calendar_name="Classes")

    # batch = service.new_batch_http_request()

    # # Add delete call for each event to batch
    # for event in events["items"]:
    #     eId = event["id"]
    #     batch.add(service.events().delete(calendarId=calendar_id, eventId=eId))

    # batch.execute()


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

            error_set.add(str(e))
            error_count += 1


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
                "timeZone": str(component.get("dtstart").dt.tzinfo),
            }
            event["end"] = {
                "dateTime": component.get("dtend").dt.isoformat(),
                "timeZone": str(component.get("dtend").dt.tzinfo),
            }
            event["sequence"] = component.get("sequence")
            try:
                event["transparency"] = component.get("transparency").lower()
                event["visibility"] = component.get("class").lower()
                event["organizer"] = {
                    "displayName": component.get("organizer").params.get("CN")
                    or "",
                    "email": re.match(
                        "mailto:(.*)", component.get("organizer")
                    ).group(1)
                    or "",
                }

                desc = component.get("description").replace("\xa0", " ")
                if "description" in event:
                    event["description"] = desc + "\r\n" + event["description"]
                else:
                    event["description"] = desc

                event["description"] = component.get("description")
            except AttributeError:
                pass

            events.append(event)

    return events


def creds():

    credentials = "8da780f3-5ea0-4d97-ab13-9e7976370624"

    protocol = MSGraphProtocol()
    scopes = protocol.get_scopes_for(["basic", "calendar_all"])

    token_backend = FileSystemTokenBackend(
        token_path=os.path.dirname(__file__), token_filename="o365_token.txt"
    )

    connection = Connection(
        credentials, auth_flow_type="public", token_backend=token_backend
    )

    account = Account(credentials, auth_flow_type="public")

    if not os.path.exists("o365_token.txt") and account.is_authenticated:
        auth_url = connection.get_authorization_url(
            requested_scopes=scopes,
        )

        webbrowser.open_new(auth_url[0])

        app = get_token_url.Application()
        app.mainloop()

        token_url = app.token_url

        connection.request_token(token_url)

    account.is_authenticated

    return account


if __name__ == "__main__":
    main()