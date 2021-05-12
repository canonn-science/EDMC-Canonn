try:
    import tkinter as tk
    from tkinter import Frame
except:
    import Tkinter as tk
    from Tkinter import Frame


import myNotebook as nb
import sys
from config import config
from ttkHyperlinkLabel import HyperlinkLabel
import requests
from datetime import datetime
import plug


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


def getSystemInfo(system):
    debug(f"Getting system infor for {system}")
    url = f"https://www.edsm.net/api-v1/system?showCoordinates=1&showInformation=1&showId=1&showPrimaryStar=1&systemName={system}"
    debug(f"url {url}")
    r = requests.get(url)
    debug(r)
    s = r.json()
    debug(s)
    return s


class fakeSystem():

    @classmethod
    def StartJump(cls, cmdr, client, message, wrapper, parent):
        cls.parent = parent
        cls.wrapper = wrapper
        cls.wrapper = wrapper
        cls.cmdr = cmdr
        cls.client = client

        # get system name
        values = message.split(" ")
        debug(values)
        debug(len(values))
        if len(values) > 2:
            cls.system = " ".join(values[2:])
        else:
            plug.show_error("fakejump no system to jump to")
            return
        try:
            cls.systemInfo = getSystemInfo(cls.system)
            # use the name so we can get the correct case
            cls.system = cls.systemInfo.get("name")
            cls.coords = cls.systemInfo.get("coords")
            cls.id64 = cls.systemInfo.get("id64")
        except:
            plug.show_error("fakejump can't locate system")
            return

        now = datetime.now()

        # we should really get the rest of the info from EDSM but this will do for now
        event = {
            "timestamp": now.strftime("%Y/%m/%dT%H:%M:%SZ"),
            "event": "StartJump",
            "JumpType": "Hyperspace",
            "StarSystem": cls.system,
            "SystemAddress": cls.id64,
            "StarClass": "X"
        }
        cls.wrapper(cls.cmdr, True, cls.system, None, None, None, None, event,
                    {"dummy": "dummy"}, cls.coords["x"], cls.coords["y"], cls.coords["z"], None,
                    None, None, cls.client)
        cls.parent.after(10000, cls.FSDJump)

    @ classmethod
    def FSDJump(cls):
        plug.show_error("FSDJump")
        now = datetime.now()
        event = {
            "timestamp": now.strftime("%Y/%m/%dT%H:%M:%SZ"),
            "event": "FSDJump",
            "StarSystem": cls.system,
            "SystemAddress": cls.id64,
            "StarPos": cls.coords,
            "SystemAllegiance": "",
            "SystemEconomy": "$economy_None;",
            "SystemEconomy_Localised": "None",
            "SystemSecondEconomy": "$economy_None;",
            "SystemSecondEconomy_Localised": "None",
            "SystemGovernment": "$government_None;",
            "SystemGovernment_Localised": "None",
            "SystemSecurity": "$GAlAXY_MAP_INFO_state_anarchy;",
            "SystemSecurity_Localised": "Anarchy",
            "Population": 0,
            "Body": f"{cls.system} A",
            "BodyID": 1,
            "BodyType": "Star",
            "JumpDist": 57.624,
            "FuelUsed": 4.402946,
            "FuelLevel": 21.086681
        }
        cls.wrapper(cls.cmdr, True, cls.system, None, None, None, None, event,
                    {"dummy": "dummy"}, cls.coords["x"], cls.coords["y"], cls.coords["z"], None,
                    None, None, cls.client)


def inject(cmdr, is_beta, system, station,
           entry, client, journal_entry_wrapper, frame):
    sendText = entry.get("event") == "SendText" and entry.get("Message")
    bFakeJump = (
        sendText and "canonn fakejump" in entry.get("Message").lower())

    if bFakeJump:
        message = entry.get("Message")
        fakeSystem.StartJump(cmdr, client, message,
                             journal_entry_wrapper, frame)
