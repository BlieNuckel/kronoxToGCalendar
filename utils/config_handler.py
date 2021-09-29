from configparser import ConfigParser
import os
import ssl
import urllib.request

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "config.ini",
)


parser = ConfigParser()


def check_config() -> ConfigParser:
    """Check for and read config file else run gui."""

    if os.path.isfile(CONFIG_PATH):
        parser.read(CONFIG_PATH)
        return parser

    return None


def load_config() -> tuple[str, str, str]:
    """Read and return values from config file."""

    ical_url = parser["SETTINGS"]["icalURL"]
    lang = parser["SETTINGS"]["LANGUAGE"]
    myssl = ssl.create_default_context()
    myssl.check_hostname = False
    myssl.verify_mode = ssl.CERT_NONE
    ical_file = (
        urllib.request.urlopen(ical_url, context=myssl).read().decode("utf-8")
    )

    return ical_file, lang


def set_section(val: str) -> str:
    with open(CONFIG_PATH, "w") as config:
        parser.add_section(val)
        parser.write(config)


def get_value(key: str) -> str:
    return parser.get("SETTINGS", key)


def set_value(key: str, val: str) -> None:
    with open(CONFIG_PATH, "w") as config:
        parser.set("SETTINGS", key, val)
        parser.write(config)
