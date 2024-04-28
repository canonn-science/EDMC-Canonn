try:
    import tkinter as tk
    from tkinter import Button
    from tkinter import Frame
    from urllib.parse import quote_plus
except:
    import Tkinter as tk
    from Tkinter import Button
    from Tkinter import Frame
    from urllib import quote_plus

import canonn.emitter
import glob
import json
import math
import os
import plug
import requests
import sys
import threading
import time
import inspect

from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.emitter import Emitter
from canonn.systems import Systems
from config import config


"""

We want to record the system where the user was last hyperdicted
Ths is in the statistics event which appears every time the user
returns from the main menu.    

This is done using the postHD API

If we detect a hyperdiction we want to record it so we send the detected
hyperdictions to postHDDetected

"""


class hyperdictionDetector:
    NEUTRAL = 0
    JUMPSTARTED = 1
    MISJUMP = 2
    THARGOIDS = 3
    HOSTILE = 3

    state = NEUTRAL
    target_system = ""

    @classmethod
    def hide(cls):
        cls.frame.grid_remove()

    @classmethod
    def show(cls):
        cls.frame.grid()
        cls.frame.after(120000, cls.hide)

    @classmethod
    def setup(cls, parent, gridrow):
        cls.parent = parent
        cls.frame = tk.Frame(parent)
        cls.frame.grid(row=gridrow)
        cls.container = tk.Frame(cls.frame)
        cls.container.columnconfigure(1, weight=1)
        cls.container.grid(row=1)
        cls.banner = tk.Label(cls.container, text="HYPERDICTION", fg="green")
        cls.banner.grid(row=0, column=0, columnspan=1)
        cls.banner.config(font=("Arial Black", 22))
        cls.instructions = tk.Label(
            cls.container, text="Please exit to main menu for confirmation", fg="green"
        )
        cls.instructions.grid(row=1, column=0, columnspan=1)
        cls.instructions.config(font=("Arial Black", 8))
        cls.hide()
        return cls.frame

    @classmethod
    def startJump(cls, target_system):
        Debug.logger.debug("startJump setting state 1 {}".format(target_system))
        cls.hide()
        cls.SetState(cls.JUMPSTARTED)

        cls.target_system = target_system

    @classmethod
    def FSDJump(cls, system):
        if cls.state == cls.JUMPSTARTED and not system == cls.target_system:
            Debug.logger.debug(
                "FSDJump setting state 2 {} {}".format(system, cls.target_system)
            )

            cls.SetState(cls.MISJUMP)
            # reset the detector after 5 seconds so we dont pick up later events
            cls.parent.after(5000, cls.Reset)
        else:
            Debug.logger.debug(
                "FSDJUMP resetting state back {} {}".format(system, cls.target_system)
            )

            cls.SetState(cls.NEUTRAL)

    @classmethod
    def Music(cls, system, cmdr, timestamp, client, odyssey):
        if cls.state == cls.MISJUMP:
            ody = "n"
            if odyssey:
                ody = "y"
            x, y, z = Systems.edsmGetSystem(system)
            dx, dy, dz = Systems.edsmGetSystem(cls.target_system)
            cls.hdvalues = {
                "cmdr": cmdr,
                "system": system,
                "timestamp": timestamp,
                "x": x,
                "y": y,
                "z": z,
                "destination": cls.target_system,
                "dx": dx,
                "dy": dy,
                "dz": dz,
                "client": client,
                "odyssey": ody,
                "hostile": False,
            }

            cls.banner["fg"] = "green"
            cls.instructions["fg"] = "green"
            cls.instructions["text"] = "Thargoids not hostile"

        else:
            Debug.logger.debug("FSDJUMP resetting state back")
            cls.hide()
            cls.state == cls.NEUTRAL

    @classmethod
    def Combat(cls, system, cmdr, timestamp, client, odyssey):
        if cls.state in (cls.MISJUMP, cls.THARGOIDS):
            ody = "n"
            if odyssey:
                ody = "y"
            x, y, z = Systems.edsmGetSystem(system)
            dx, dy, dz = Systems.edsmGetSystem(cls.target_system)
            cls.hdvalues = {
                "cmdr": cmdr,
                "system": system,
                "timestamp": timestamp,
                "x": x,
                "y": y,
                "z": z,
                "destination": cls.target_system,
                "dx": dx,
                "dy": dy,
                "dz": dz,
                "client": client,
                "odyssey": ody,
                "hostile": False,
            }
            cls.banner["fg"] = "red"
            cls.instructions["fg"] = "red"
            cls.instructions["text"] = "Thargoids are hostile"
            cls.hdvalues["hostile"] = True

            cls.SetState(cls.HOSTILE)

    @classmethod
    def hyperdiction(cls):
        if cls.state in (cls.THARGOIDS, cls.HOSTILE):
            Debug.logger.debug("Hyperdiction Detected")
            cls.show()
            canonn.emitter.post(
                "https://europe-west1-canonn-api-236217.cloudfunctions.net/postHDDetected",
                cls.hdvalues,
            )
            cls.Reset()
            # plug.show_error("Hyperdiction: Exit to main menu")

    @classmethod
    def SupercruiseExit(cls):
        cls.hide()
        cls.SetState(cls.NEUTRAL)

    @classmethod
    def Reset(cls):
        cls.SetState(cls.NEUTRAL)

    @classmethod
    def SetState(cls, state):
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name
        Debug.logger.debug(f"{caller_name} setting hyper {state}")
        cls.state = state

    @classmethod
    def submit(cls, cmdr, is_beta, system, station, entry, client, state):
        odyssey = state.get("Odyssey")
        if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            cls.startJump(entry.get("StarSystem"))

        if entry.get("event") == "FSDJump":
            cls.FSDJump(entry.get("StarSystem"))

        if entry.get("event") == "Music" and entry.get("MusicTrack") in (
            "Unknown_Encounter"
        ):
            if cls.state == cls.MISJUMP:
                # move here because we can get a second UE music even after combat
                cls.Music(system, cmdr, entry.get("timestamp"), client, odyssey)
                cls.SetState(cls.THARGOIDS)
                # we will wait 3 seconds for a hostile interaction before sending a message
                cls.parent.after(3000, cls.hyperdiction)

        # we used to get "Unknown_Encounter" event first but Glaives need to be hypered immediately
        if entry.get("event") == "Music" and entry.get("MusicTrack") in (
            "Combat_Unknown",
            "Combat_Dogfight",
            "Combat_Hunters",
        ):

            if cls.state in (cls.MISJUMP, cls.THARGOIDS):
                cls.Combat(system, cmdr, entry.get("timestamp"), client, odyssey)
                # setting the state so we dont send twice
                cls.SetState(cls.HOSTILE)
                cls.hyperdiction()

        if entry.get("event") == "SupercruiseExit":
            cls.SupercruiseExit()


def get_distance(a, b):
    x, y, z = Systems.edsmGetSystem(a)
    a, b, c = Systems.edsmGetSystem(b)
    return math.sqrt(math.pow(x - a, 2) + math.pow(y - b, 2) + math.pow(z - c, 2))


def submit(cmdr, is_beta, system, station, entry, client, state):
    hyperdictionDetector.submit(cmdr, is_beta, system, station, entry, client, state)

    if entry["event"] == "Statistics" and entry.get("TG_ENCOUNTERS"):
        # there is no guarentee TG_ENCOUNTER_TOTAL_LAST_SYSTEM will have a value
        if entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM"):

            lastsystem = entry.get("TG_ENCOUNTERS").get(
                "TG_ENCOUNTER_TOTAL_LAST_SYSTEM"
            )
            gametime = entry.get("TG_ENCOUNTERS").get(
                "TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP"
            )
            year, remainder = gametime.split("-", 1)
            tgtime = "{}-{}".format(str(int(year) - 1286), remainder)

            if lastsystem == "Pleiades Sector IR-W d1-55":
                lastsystem = "Delphi"

            Debug.logger.debug(
                {"cmdr": cmdr, "system": lastsystem, "timestamp": tgtime}
            )
            x, y, z = Systems.edsmGetSystem(lastsystem)
            # we are going to submit the hyperdiction here.
            canonn.emitter.post(
                "https://europe-west1-canonn-api-236217.cloudfunctions.net/postHD",
                {
                    "cmdr": cmdr,
                    "system": lastsystem,
                    "timestamp": tgtime,
                    "x": x,
                    "y": y,
                    "z": z,
                },
            )
