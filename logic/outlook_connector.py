import os.path
import urllib
from configparser import ConfigParser
import webbrowser
from gui import get_token_url
import datetime
import ssl
from O365 import MSGraphProtocol
from O365.connection import Connection
from O365.account import Account
from O365.utils.token import FileSystemTokenBackend
from dateutil.relativedelta import relativedelta
import dateutil.parser

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "config.ini",
)

SCOPES = ["basic", "calendar_all"]


def config_loader():
    parser = ConfigParser(allow_no_value=True)

    platform = parser["SETTINGS"]["platform"]
    calendar_name = parser["SETTINGS"]["calendarId"]
    ical_url = parser["SETTINGS"]["icalURL"]
    lang = parser["SETTINGS"]["LANGUAGE"]
    myssl = ssl.create_default_context()
    myssl.check_hostname = False
    myssl.verify_mode = ssl.CERT_NONE
    ical_file = (
        urllib.request.urlopen(ical_url, context=myssl).read().decode("utf-8")
    )

    return calendar_name, ical_file, lang, platform


def insert_event(events, account, calendar_name):  # Adds events

    schedule = account.schedule()
    calendar = schedule.get_calendar(calendar_name=calendar_name)

    for event in events:
        new_event = calendar.new_event()
        new_event.subject = event["summary"]
        new_event.location = event["location"]
        new_event.start = dateutil.parser.isoparse(event["start"]["dateTime"])
        new_event.end = dateutil.parser.isoparse(event["end"]["dateTime"])
        try:
            new_event.body = event["description"]
        except KeyError:
            pass
        new_event.save()


def clear_calendar(account, calendar_name):  # Clears calendar
    # Get current available events
    schedule = account.schedule()
    calendar = schedule.get_calendar(calendar_name=calendar_name)

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    twelve_months = today + relativedelta(months=+13)

    q = calendar.new_query("start").greater_equal(yesterday)
    q.chain("and").on_attribute("end").less_equal(twelve_months)

    events = calendar.get_events(query=q, limit=1000)

    for event in events:
        event.delete()


def creds():

    credentials = "8da780f3-5ea0-4d97-ab13-9e7976370624"

    protocol = MSGraphProtocol(timezone="Europe/Stockholm")
    scopes = protocol.get_scopes_for(SCOPES)

    token_backend = FileSystemTokenBackend(
        token_path=os.path.dirname(__file__), token_filename="o365_token.txt"
    )

    connection = Connection(
        credentials, auth_flow_type="public", token_backend=token_backend
    )

    account = Account(credentials, auth_flow_type="public", protocol=protocol)

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
