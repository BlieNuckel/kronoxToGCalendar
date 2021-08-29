import tkinter as tk
from gui import GUI

root = tk.Tk()
root.geometry("500x500")
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(3, weight=1)

platform_var = tk.StringVar(root, "1")


class MainApplication(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        tk.Label(
            root, text="Which platform do you wish to integrate with"
        ).grid(row=1, column=0)
        platforms = {"Google": "google", "Outlook": "outlook"}
        frame = tk.Frame(root)
        for (text, value) in platforms.items():
            tk.Radiobutton(
                frame, text=text, variable=platform_var, value=value
            ).pack(side="left", ipady=5)
        frame.grid(row=2, column=0)

        self.confirm_button = tk.Button(
            root, text="Confirm", command=self.confirm_pressed
        )
        self.confirm_button.grid(row=3, column=0)

    def confirm_pressed(self):
        self.platform = platform_var.get()
        root.destroy()

        app = GUI.Application(platform=self.platform)
        app.mainloop()


def run():
    app = MainApplication(master=root)
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", False)
    app.mainloop()
