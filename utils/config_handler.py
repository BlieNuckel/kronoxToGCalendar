from configparser import ConfigParser
import os
import ssl
import urllib.request

CONFIG_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "config.ini",
)


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ConfigHandler(metaclass=Singleton):

    parser = ConfigParser()

    def check_config(self) -> ConfigParser:
        """Check for and read config file else run gui."""

        if os.path.isfile(CONFIG_PATH):
            self.parser.read(CONFIG_PATH)
            return self.parser

        return None

    def load_config(self) -> tuple[str, str, str]:
        """Read and return values from config file."""

        ical_url = self.parser["SETTINGS"]["icalURL"]
        lang = self.parser["SETTINGS"]["LANGUAGE"]
        myssl = ssl.create_default_context()
        myssl.check_hostname = False
        myssl.verify_mode = ssl.CERT_NONE
        ical_file = (
            urllib.request.urlopen(ical_url, context=myssl).read().decode("utf-8")
        )

        return ical_file, lang

    def set_section(self, val: str) -> str:
        self.parser.add_section(val)

    def get_value(self, key: str) -> str:
        return self.parser["SETTINGS"][key]

    def set_value(self, key: str, val: str) -> None:
        with open(CONFIG_PATH, "w") as config:
            self.parser.set("SETTINGS", key, val)
            self.parser.write(config)
