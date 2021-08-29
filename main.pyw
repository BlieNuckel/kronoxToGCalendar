from configparser import ConfigParser
import os
import subprocess
from logic import outlook_connector
from logic import google_connector
import gui.main_gui
from logic import event_handler

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

if not os.path.isfile(CONFIG_PATH):
    subprocess.call('"batch/install_requirements.bat"')


def main():

    parser = ConfigParser(allow_no_value=True)
    if os.path.isfile(CONFIG_PATH):
        parser.read(CONFIG_PATH)
    else:
        gui.main_gui.run()

        parser.read(CONFIG_PATH)

    platform = parser["SETTINGS"]["platform"]

    if platform == "outlook":
        (calendar_id, ical_file, lang) = outlook_connector.config_loader()

        account = outlook_connector.creds()
        event_list = event_handler.parse_ics(ical_file)
        parsed_event_list = event_handler.event_edit(event_list, lang)

        outlook_connector.clear_calendar(account, calendar_id)

        outlook_connector.insert_event(parsed_event_list, account, calendar_id)

    elif platform == "google":
        (
            calendar_id,
            ical_file,
            lang,
            webhook_url,
        ) = google_connector.config_loader()

        service = google_connector.creds()
        event_list = event_handler.parse_ics(ical_file)
        parsed_event_list = event_handler.event_edit(event_list, lang)

        google_connector.clear_calendar(service, calendar_id)

        google_connector.insert_event(
            parsed_event_list, service, calendar_id, webhook_url
        )


if __name__ == "__main__":
    main()
