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

    @classmethod
    def setLogger(cls, logger):
        Debug.logger = logger

    @classmethod
    def plugin_prefs(cls, parent, client, gridrow):
        "Called to get a tk Frame for the settings dialog."

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")
        HyperlinkLabel(frame, text=f"Release: {client}",
                       url="https://github.com/canonn-science/EDMC-Canonn/blob/master/README.md").grid(row=1, column=0, sticky="NW")

        return frame


def debug(value):
    Debug.logger.debug(value)


def error(value):
    Debug.logger.error(value)
