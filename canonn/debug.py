try:
    import tkinter as tk
    from tkinter import Frame
except:
    import Tkinter as tk
    from Tkinter import Frame

import datetime
import myNotebook as nb
import sys
from config import config
from ttkHyperlinkLabel import HyperlinkLabel


class Debug:
    debugvar = tk.IntVar(value=config.getint("CanonnDebug"))
    debugswitch = debugvar.get()
    print("EDMC-Canonn: Starting the debug sub-system")
    sys.stdout.flush()

    client = "Canonn"

    @classmethod
    def setClient(cls, client):
        Debug.client = client

    @classmethod
    def p(cls, value):
        print("{} [{}] {}".format(
            datetime.datetime.now(), Debug.client, str(value)))
        sys.stdout.flush()

    @classmethod
    def debug(cls, value):
        if cls.debugswitch == 1:
            cls.p(value)

    @classmethod
    def plugin_prefs(cls, parent, client, gridrow):
        "Called to get a tk Frame for the settings dialog."

        cls.debugvar = tk.IntVar(value=config.getint("CanonnDebug"))
        cls.debugswitch = cls.debugvar.get()
        Debug.client = client

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Checkbutton(frame, text="Turn on Debugging", variable=cls.debugvar).grid(
            row=0, column=0, sticky="NW")

        HyperlinkLabel(frame, text=f"Release: {client}",
                       url="https://github.com/canonn-science/EDMC-Canonn/blob/master/README.md").grid(row=1, column=0, sticky="NW")

        return frame

    @classmethod
    def prefs_changed(cls):
        "Called when the user clicks OK on the settings dialog."
        config.set('CanonnDebug', cls.debugvar.get())
        cls.debugswitch = cls.debugvar.get()


def debug(value):
    Debug.debug(value)


def error(value):
    Debug.p(value)
