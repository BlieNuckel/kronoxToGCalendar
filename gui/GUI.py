import tkinter as tk
import os
from configparser import ConfigParser
import winshell
from win32com import shell
from tkinter import messagebox
import pythoncom


class Application(tk.Frame):
    def __init__(self, platform):
        self.root = tk.Tk()
        self.root.geometry("500x500")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(12, weight=1)
        super().__init__(self.root)
        self.master = self.root
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)

        self.lang_var = tk.StringVar(self.root, "1")
        self.discord_choice_var = tk.BooleanVar(
            self.root, False, name="self.discord_choice_var"
        )
        self.add_to_startup_var = tk.BooleanVar(
            self.root, False, name="self.add_to_startup_var"
        )

        func = self.get_platform(platform)
        func()

    def get_platform(self, platform):
        if platform == "google":
            return self.create_google_widgets
        elif platform == "outlook":
            return self.create_outlook_widgets

    def create_google_widgets(self):
        tk.Label(
            self.root,
            text="Google Calendar ID",
        ).grid(row=1, column=0)
        self.gcal_id = tk.Text(self.root, height=1, width=52)
        self.gcal_id.grid(row=2, column=0)

        tk.Label(self.root, text="Discord integration").grid(row=7, column=0)
        self.discord_choice = tk.Checkbutton(
            self.root,
            variable="self.discord_choice_var",
            offvalue=False,
            onvalue=True,
        )
        self.discord_choice.grid(row=8, column=0)
        self.discord_choice_var.trace_add(
            "write",
            lambda var_name, var_index, operation: self.update_discord_active(),
        )

        self.discord_extra_frame = tk.Frame(self.root)
        tk.Label(self.discord_extra_frame, text="Discord Webhook").grid(
            row=1, column=0
        )
        self.discord_extra = tk.Text(
            self.discord_extra_frame, height=1, width=52
        )
        self.discord_extra.grid(row=2, column=0)

        confirm_button_frame = tk.Frame(self.root)

        self.read_me_button = tk.Button(
            confirm_button_frame,
            text="Installation Guide",
            command=self.open_read_me,
        )
        self.read_me_button.pack()

        self.confirm_button = tk.Button(
            confirm_button_frame,
            text="Confirm",
            command=self.confirm_pressed_google,
        )
        self.confirm_button.pack()
        confirm_button_frame.grid(row=12, column=0)

        self.create_shared_widgets()

    def create_outlook_widgets(self):
        tk.Label(
            self.root,
            text="Outlook calendar name (case sensitive)",
        ).grid(row=1, column=0)
        self.gcal_id = tk.Text(self.root, height=1, width=52)
        self.gcal_id.grid(row=2, column=0)

        confirm_button_frame = tk.Frame(self.root)

        self.read_me_button = tk.Button(
            confirm_button_frame,
            text="Installation Guide",
            command=self.open_read_me,
        )
        self.read_me_button.pack()

        self.confirm_button = tk.Button(
            confirm_button_frame,
            text="Confirm",
            command=self.confirm_pressed_outlook,
        )
        self.confirm_button.pack()
        confirm_button_frame.grid(row=12, column=0)

        self.create_shared_widgets()

    def create_shared_widgets(self):
        tk.Label(self.root, text="Icalendar URL (from kronox)").grid(
            row=3, column=0
        )
        self.ical_url = tk.Text(self.root, height=1, width=52)
        self.ical_url.grid(row=4, column=0)

        tk.Label(self.root, text="Language of the programme you attend").grid(
            row=5, column=0
        )
        lang = {"English": "en", "Swedish": "sv"}
        frame = tk.Frame(self.root)
        for (text, value) in lang.items():
            tk.Radiobutton(
                frame, text=text, variable=self.lang_var, value=value
            ).pack(side="left", ipady=5)
        frame.grid(row=6, column=0)

        self.startup_text = tk.StringVar()
        self.startup_text.set(
            "Run script on startup\n!WARNING! without this option enabled\nthe script must be manually\nrun to update the\n schedule"
        )
        self.add_to_startup_label = tk.Label(
            self.root, textvariable=self.startup_text
        )
        self.add_to_startup = tk.Checkbutton(
            self.root,
            variable="self.add_to_startup_var",
            offvalue=False,
            onvalue=True,
        )
        self.add_to_startup_label.grid(row=10)
        self.add_to_startup.grid(row=11)
        self.add_to_startup_var.trace_add(
            "write",
            lambda var_name, var_index, operation: self.update_add_startup_active(),
        )

    def update_discord_active(self):
        if self.discord_choice_var.get():
            self.discord_extra_frame.grid(row=9, column=0)
        else:
            self.discord_extra_frame.grid_forget()

    def update_add_startup_active(self):
        if self.add_to_startup_var.get():
            self.startup_text.set("Run script on startup")
        else:
            self.startup_text.set(
                "Run script on startup\n!WARNING! without this option enabled\nthe script must be manually\nrun to update the\n schedule"
            )

    def confirm_pressed_google(self):
        if not self.valid_check_google():
            return

        parser = ConfigParser(allow_no_value=True)
        config_path = os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            "config.ini",
        )

        with open(config_path, "w") as f:
            calendarId = self.gcal_id.get("1.0", tk.END)

            icalURL = self.ical_url.get("1.0", tk.END)
            lang = self.lang_var.get()
            if self.discord_choice_var.get():
                discordIntegration = "y"
            elif not self.discord_choice_var.get():
                discordIntegration = "n"

            parser.add_section("SETTINGS")
            parser.set("SETTINGS", "platform", "google")
            parser.set("SETTINGS", "calendarId", calendarId)
            parser.set("SETTINGS", "icalURL", icalURL)
            parser.set("SETTINGS", "language", lang)
            parser.set("SETTINGS", "discordIntegration", discordIntegration)
            if discordIntegration == "y":
                parser.add_section("DISCORD_SETTINGS")
                parser.set(
                    "DISCORD_SETTINGS",
                    "webhook",
                    self.discord_extra.get("1.0", tk.END),
                )
            parser.write(f)

        if self.add_to_startup_var.get():
            startup_folder = winshell.startup()

            path = os.path.join(
                startup_folder, "kronoxToGCalendar_Startup.lnk"
            )
            target = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..\..", "run.vbs")
            )
            wrk_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..\..")
            )

            # This code is from this (https://stackoverflow.com/a/57243272) stack overflow answer, not my own
            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink,
                None,
                pythoncom.CLSCTX_INPROC_SERVER,
                shell.IID_IShellLink,
            )

            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            shortcut.SetPath(target)
            shortcut.SetWorkingDirectory(wrk_dir)
            persist_file.save(path, 0)

        self.root.destroy()

    def confirm_pressed_outlook(self):
        if not self.valid_check_outlook():
            return

        parser = ConfigParser(allow_no_value=True)
        config_path = os.path.join(
            os.path_abspath(os.path.join(os.path.dirname(__file__), "..")),
            "config.ini",
        )

        with open(config_path, "w") as f:
            calendarId = self.gcal_id.get("1.0", tk.END)

            icalURL = self.ical_url.get("1.0", tk.END)
            lang = self.lang_var.get()

            parser.add_section("SETTINGS")
            parser.set("SETTINGS", "platform", "outlook")
            parser.set("SETTINGS", "calendarId", calendarId)
            parser.set("SETTINGS", "icalURL", icalURL)
            parser.set("SETTINGS", "language", lang)
            parser.write(f)

        if self.add_to_startup_var.get():
            startup_folder = winshell.startup()

            path = os.path.join(
                startup_folder, "kronoxToGCalendar_Startup.lnk"
            )
            target = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..\..", "run.vbs")
            )
            wrk_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..\..")
            )

            # This code is from this (https://stackoverflow.com/a/57243272) stack overflow answer, not my own
            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink,
                None,
                pythoncom.CLSCTX_INPROC_SERVER,
                shell.IID_IShellLink,
            )

            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            shortcut.SetPath(target)
            shortcut.SetWorkingDirectory(wrk_dir)
            persist_file.save(path, 0)

        self.root.destroy()

    def valid_check_google(self):
        valid = True

        # if (
        #     self.gcal_id.get("1.0", tk.END)[26:].strip()
        #     != "@group.calendar.google.com"
        # ):
        #     tk.messagebox.showinfo("Error", "Invalid google calendar ID")
        #     valid = False
        if (
            self.ical_url.get("1.0", tk.END)[:46].strip()
            != "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics"
        ):
            tk.messagebox.showinfo("Error", "Invalid Kronox schema URL")
            valid = False
        if (
            self.discord_extra.get("1.0", tk.END)[:33].strip()
            != "https://discord.com/api/webhooks/"
            and self.discord_choice_var.get()
        ):
            tk.messagebox.showinfo("Error", "Invalid discord webhook URL")
            valid = False

        return valid

    def valid_check_outlook(self):
        valid = True

        if (
            self.ical_url.get("1.0", tk.END)[:46].strip()
            != "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics"
        ):
            tk.messagebox.showinfo("Error", "Invalid Kronox schema URL")
            valid = False

        return valid

    def open_read_me(self):
        os.startfile("https://github.com/BlieNuckel/kronoxToGCalendar")