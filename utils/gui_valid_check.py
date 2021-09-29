from tkinter import messagebox
import tkinter as tk

if __name__ == "__main__":
    pass


def valid_check(ical_url: tk.Text, lang_var: tk.StringVar):
    valid = True

    if (
        ical_url.get("1.0", tk.END)[:46].strip()
        != "https://kronox.hkr.se/setup/jsp/SchemaICAL.ics"
        and ical_url.get("1.0", tk.END)[:46].strip()
        != "https://schema.hkr.se/setup/jsp/SchemaICAL.ics"
    ):
        messagebox.showinfo("Error", "Invalid Kronox schema URL")
        valid = False
    elif lang_var.get() == "1":
        messagebox.showinfo("Error", "You must select a language")
        valid = False

    return valid
