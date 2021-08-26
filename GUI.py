import tkinter as tk
import os
from configparser import ConfigParser
import winshell
from win32com import client
from tkinter import messagebox

root = tk.Tk()
root.geometry("500x500")
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(12, weight=1)

lang_var = tk.StringVar(root, "1")
discord_choice_var = tk.BooleanVar(root, False, name="discord_choice_var")
add_to_startup_var = tk.BooleanVar(root, False, name="add_to_startup_var")


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        tk.Label(root, text="Google Calendar ID", ).grid(row=1, column=0)
        self.gcal_id = tk.Text(root, height=1, width=52)
        self.gcal_id.grid(row=2, column=0)
        
        tk.Label(root, text="Icalendar URL (from kronox)").grid(row=3, column=0)
        self.ical_url = tk.Text(root, height=1, width=52)
        self.ical_url.grid(row=4, column=0)
        
        tk.Label(root, text="Language of the programme you attend").grid(row=5, column=0)
        lang = {
            "English": "en",
            "Swedish": "sv"
        }
        frame = tk.Frame(root)
        for (text, value) in lang.items():
            tk.Radiobutton(frame, text = text, variable=lang_var,
                                   value = value).pack(side="left", ipady = 5)
        frame.grid(row=6, column=0)
        
        tk.Label(root, text="Discord integration").grid(row=7, column=0)
        self.discord_choice = tk.Checkbutton(root, variable="discord_choice_var", offvalue=False, onvalue=True)
        self.discord_choice.grid(row=8, column=0)
        discord_choice_var.trace_add("write", lambda var_name, var_index, operation: self.update_discord_active())
        
        self.discord_extra_frame = tk.Frame(root)
        tk.Label(self.discord_extra_frame, text="Discord Webhook").grid(row=1, column=0)
        self.discord_extra = tk.Text(self.discord_extra_frame, height=1, width=52)
        self.discord_extra.grid(row=2, column=0)
        
        self.startup_text = tk.StringVar()
        self.startup_text.set("Run script on startup\n!WARNING! without this option enabled\nthe script must be manually\nrun to update the\n schedule")
        self.add_to_startup_label = tk.Label(root, textvariable=self.startup_text)
        self.add_to_startup = tk.Checkbutton(root, variable="add_to_startup_var", offvalue=False, onvalue=True)
        self.add_to_startup_label.grid(row=10)
        self.add_to_startup.grid(row=11)
        add_to_startup_var.trace_add("write", lambda var_name, var_index, operation: self.update_add_startup_active())
        
        confirm_button_frame = tk.Frame(root)
        
        self.read_me_button = tk.Button(confirm_button_frame, text="Installation Guide", command=self.open_read_me)
        self.read_me_button.pack()
        
        self.confirm_button = tk.Button(confirm_button_frame, text="Confirm", command=self.confirm_pressed)
        self.confirm_button.pack()
        confirm_button_frame.grid(row=12, column=0)
        

    def update_discord_active(self):
        if discord_choice_var.get():
            self.discord_extra_frame.grid(row=9, column=0)
        else:
            self.discord_extra_frame.grid_forget()
            
            
    def update_add_startup_active(self):
        if add_to_startup_var.get():
            self.startup_text.set("Run script on startup")
        else:
            self.startup_text.set("Run script on startup\n!WARNING! without this option enabled\nthe script must be manually\nrun to update the\n schedule")
            
            
    def confirm_pressed(self):
        if not self.valid_check():
            return
        
        parser = ConfigParser(allow_no_value=True)
        config_path = os.path.join(os.path.dirname(__file__), "config.ini")
        
        with open(config_path, "w") as f:
            calendarId = self.gcal_id.get("1.0", tk.END)
            
            icalURL = self.ical_url.get("1.0", tk.END)
            lang = lang_var.get()
            if discord_choice_var.get():
                discordIntegration = "y"
            elif not discord_choice_var.get():
                discordIntegration = "n"

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
                    self.discord_extra.get("1.0", tk.END),
                )
            parser.write(f)
            
        if add_to_startup_var.get():
            startup_folder = winshell.startup()
            
            path = os.path.join(startup_folder, "kronoxToGCalendar_Startup.lnk")
            target = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run.vbs"))
            icon = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "run.vbs"))
            
            shell = client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(path)
            shortcut.TargetPath = target
            shortcut.IconLocation = icon
            shortcut.save()
        
        root.destroy()
            
    def valid_check(self):
        valid = True
        
        if self.gcal_id.get("1.0", tk.END)[26:].strip() != "@group.calendar.google.com":
            tk.messagebox.showinfo("Error", "Invalid google calendar ID")
            valid = False
        if self.ical_url.get("1.0", tk.END)[:46].strip() != "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics":
            tk.messagebox.showinfo("Error", "Invalid Kronox schema URL")
            valid = False
        if self.discord_extra.get("1.0", tk.END)[:33].strip() != "https://discord.com/api/webhooks/" and discord_choice_var.get():
            tk.messagebox.showinfo("Error", "Invalid discord webhook URL")
            valid = False
        
        return valid
    
    def open_read_me(self):
        os.startfile("https://github.com/BlieNuckel/kronoxToGCalendar")
        

root.lift()
app = Application(master=root)
app.mainloop()