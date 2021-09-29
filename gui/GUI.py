import tkinter as tk
import os
import utils.gui_open_readme as gui_open_readme
from utils.config_handler import ConfigHandler
from utils.enums import Platform
import winshell
from win32com import client

OPTIONS = {
    "Select programme to get schedule": "",
    "Datasystemutveckling 2020": "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TGDU3+2020+36+100+NML+sv",
    "Datasystemutveckling 2021": "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TGDU3+2021+35+100+NML+sv",
    "Software Development 2020": "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TBSE2+2020+36+100+NML+en",
    "Software Development 2021": "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics?startDatum=idag&intervallTyp=m&intervallAntal=6&sprak=SV&sokMedAND=true&forklaringar=true&resurser=p.TBSE2+2021+35+100+NML+en",
}

config_handler = ConfigHandler()


class Application(tk.Frame):
    def __init__(self, platform):
        self.root = tk.Tk()
        self.root.geometry("500x500")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(13, weight=1)
        super().__init__(self.root)
        self.master = self.root
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)

        self.lang_var = tk.StringVar(self.root, "1")

        self.ical_option_var = tk.StringVar(
            self.root,
            list(OPTIONS.keys())[0],
            name="self.ical_option_var",
        )

        self.start_platform(platform)

    def start_platform(self, platform) -> Platform:
        if platform == "google":
            self.create_widgets(Platform.GOOGLE)
        elif platform == "outlook":
            self.create_widgets(Platform.OUTLOOK)

    def create_widgets(self, platform: Platform):
        tk.Label(
            self.root,
            text="iCal file URL\n(read the installation guide for details on where to find this)",
        ).grid(row=3, column=0)
        self.ical_url = tk.Text(self.root, height=1, width=52)
        self.ical_url.grid(row=4, column=0)

        self.ical_options = tk.OptionMenu(
            self.root, self.ical_option_var, *OPTIONS.keys()
        )
        self.ical_options.grid(row=5, column=0)
        self.ical_option_var.trace_add(
            "write",
            lambda var_name, var_index, operation: self.update_ical_option(),
        )

        tk.Label(self.root, text="Language of the programme you attend").grid(
            row=6, column=0
        )
        lang = {"English": "en", "Swedish": "sv"}
        frame = tk.Frame(self.root)
        for (text, value) in lang.items():
            tk.Radiobutton(
                frame, text=text, variable=self.lang_var, value=value
            ).pack(side="left", ipady=5)
        frame.grid(row=7, column=0)

        confirm_button_frame = tk.Frame(self.root)

        self.read_me_button = tk.Button(
            confirm_button_frame,
            text="Installation Guide",
            command=gui_open_readme.open_read_me,
        )
        self.read_me_button.pack()

        self.confirm_button = tk.Button(
            confirm_button_frame,
            text="Confirm",
            command=self.confirm_pressed(platform),
        )
        self.confirm_button.pack()
        confirm_button_frame.grid(row=13, column=0)

    def update_ical_option(self):
        self.ical_url.delete("1.0", tk.END)
        self.ical_url.insert(tk.END, OPTIONS[self.ical_option_var.get()])

    def confirm_pressed(self, platform: Platform):
        # if not gui_valid_check.valid_check(self.ical_url, self.lang_var):
        #     return

        icalURL = self.ical_url.get("1.0", tk.END)
        lang = self.lang_var.get()

        config_handler.set_section("SETTINGS")
        config_handler.set_value("platform", platform)
        config_handler.set_value("icalURL", icalURL)
        config_handler.set_value("language", lang)

        startup_folder = winshell.startup()

        path = os.path.join(startup_folder, "kronoxToGCalendar_startup.lnk")
        target = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..\..", "run.vbs")
        )
        icon = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..\..", "run.vbs")
        )
        wrk_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..\.."))

        shell = client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        shortcut.TargetPath = target
        shortcut.IconLocation = icon
        shortcut.WorkingDirectory = wrk_dir
        shortcut.save()

        self.root.destroy()
