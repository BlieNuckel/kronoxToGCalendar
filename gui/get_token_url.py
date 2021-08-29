import tkinter as tk
import os
from configparser import ConfigParser
import winshell
from win32com import client
from tkinter import messagebox


class Application(tk.Frame):
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("500x100")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)

        super().__init__(self.root)

        self.master = self.root
        self.create_widgets()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)
        self._token_url = ""

    def create_widgets(self):
        tk.Label(
            self.root,
            text="After logging in with Microsoft, you will be\ndirected to a blank page. Copy the URL of that page and paste it here",
        ).grid(row=1, column=0)
        self.token_url_input = tk.Text(self.root, height=1, width=52)
        self.token_url_input.grid(row=2, column=0)

        self.confirm_button = tk.Button(
            self.root, text="Confirm", command=self.confirm_pressed
        )
        self.confirm_button.grid(row=3, column=0)

    def confirm_pressed(self):
        self.token_url = self.token_url_input.get("1.0", tk.END)
        self.root.destroy()

    @property
    def token_url(self):
        return self._token_url

    @token_url.setter
    def token_url(self, token_url):
        self._token_url = token_url
