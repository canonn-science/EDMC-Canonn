import plug
from config import config
import os
import threading
import requests
import json
from queue import Queue
from pathlib import Path

import tkinter as tk
from tkinter import Frame
import csv

from canonn.debug import Debug
from canonn.release import ClientVersion
from theme import theme

FULLYSCANNED = 4
PARTIALSCAN = 3
UNKNOWNSCAN = 2
LOGGED = 1
MISSING = 0


"""

When an event is triggered to fetch data, we want to check if we already have the data we need stored and if not fetch the data in a thread.
Given that many threads could be active at once, we need to store the data in a thread safe way using queues then trigger a callback that can 
retrieve the data from the queue and update the display and the cache of retrieved values. 

"""


class TargetDisplay():

    @classmethod
    def set_plugin_dir(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

    def __init__(self, parent, gridrow):
        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        self.gridrow = gridrow
        self.parent = parent

        self.systemq = Queue()
        self.system_cache = SystemCache(100)

        self.news_data = []
        self.mid_jump = False
        self.icon = tk.PhotoImage(file=os.path.join(
            TargetDisplay.plugin_dir, "icons", "floppy.gif"))
        self.note = tk.PhotoImage(file=os.path.join(
            TargetDisplay.plugin_dir, "icons", "notepad.gif"))

        # get the parent to take care of events
        self.parent.bind('<<setTarget>>', self.set_target)

        # we do not declare any widgets here as we will need to destroy them
        # to force the frame to be hidden. But we start hidden so set a value
        self.hidden = True

    """
    When this is called we will go through the queue and display anything 
    that is in there if it there is more than one then the old scan will not be 
    displayed
    """

    def set_target(self, event):

        iterations = 0
        while not self.systemq.empty():
            self.show()
            self.floppy["image"] = self.icon
            iterations += 1
            system = self.systemq.get()
            # we will add this data so save button can use it
            self.spansh = system
            # cache the system
            if system and system.get("system") and state_check(system) == FULLYSCANNED:
                self.system_cache.put(system)

            totalbodies, bodycount = body_check(system)

            # self.label.grid()

            target_level = state_check(system)
            if target_level == MISSING:
                target_text = f"Target: {system.get('name')} missing ({system.get('starclass')})"
                self.label["background"] = "#fc0303"
            if target_level == LOGGED:
                target_text = f"Target: {system.get('name')} logged ({system.get('starclass')})"
                self.label["background"] = "#FFA500"
            if target_level == UNKNOWNSCAN:
                target_text = f"Target: {system.get('name')} scanned {bodycount}/? ({system.get('starclass')})"
                self.label["background"] = "#FFA500"
            if target_level == PARTIALSCAN:
                target_text = f"Target: {system.get('name')} scanned {bodycount}/{totalbodies} ({system.get('starclass')})"
                self.label["background"] = "#FFA500"
            if target_level == FULLYSCANNED:
                target_text = f"Target: {system.get('name')} fully scanned {bodycount}/{totalbodies} ({system.get('starclass')})"
                self.label["background"] = "#00ff00"
            if iterations > 1:
                plug.show_error(f"target {system.get('name')} skipped")

            self.label.config(fg="black")
            self.label["text"] = target_text
            self.floppy.bind("<Button-1>", self.save)

    def openfile(self, event):
        csvpath = os.path.join(config.app_dir_path, 'canonn')
        csvfile = os.path.join(csvpath, "targets.csv")
        os.system(f"notepad.exe {csvfile}")

    def save(self, event):
        # this should always exist but better safe than sorry
        csvpath = os.path.join(config.app_dir_path, 'canonn')
        csvfile = os.path.join(csvpath, "targets.csv")
        try:
            os.mkdir(csvpath)
        except OSError as error:
            pass

        name = self.spansh.get("name")
        id64 = self.spansh.get("id64")
        starclass = self.spansh.get("starclass")
        x, y, z = "", "", ""
        if self.spansh.get("system"):
            x, y, z = self.spansh.get("system").get("coords").values()

        rows = []
        if not Path(csvfile).is_file():
            rows.append(["system", "id64", "starclass", "x", "y", "z"])

        rows.append([name, id64, starclass, str(x), str(y), str(z)])

        with open(csvfile, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

        # now we can provide a link to open the file
        self.floppy.bind("<Button-1>", self.openfile)
        self.floppy["image"] = self.note

    def hide(self):

        if not self.hidden:
            self.hidden = True
            self.label.destroy()
            self.frame.destroy()
            self.floppy.destroy()

    def show(self):

        # only do this if the frame does not exist
        if self.hidden:
            self.hidden = False
            self.frame = Frame(self.parent)

            self.frame.columnconfigure(2, weight=1)
            self.frame.grid(row=self.gridrow, column=0,
                            columnspan=2)
            self.label = tk.Label(self.frame)
            self.label.grid(row=0, column=0)

            self.floppy = tk.Label(self.frame, image=self.icon, cursor="hand2")
            self.floppy.grid(row=0, column=1)
            theme.update(self.frame)
            theme.update(self.floppy)

    """
    This will put the system in the queue
    """

    def safe_callback(self, spansh):
        self.systemq.put(spansh)
        self.parent.event_generate('<<setTarget>>', when='tail')

    def journal_entry(self, cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, entry,
                      state, x, y, z, body, nearloc, client):
        if entry.get("event") == "FSDTarget":

            if not self.mid_jump:

                cache = self.system_cache.get(entry.get("SystemAddress"))
                # if the system is in the cache and fully scanned don't ask spansh again
                if state_check(cache) == FULLYSCANNED:
                    self.systemq.put(cache)
                    # calling it now not generating an event
                    self.set_target(None)
                else:
                    spanshCheck(entry, self.safe_callback).start()

        if entry.get("event") in ("StartJump") and entry.get("JumpType") == "Hyperspace":
            self.mid_jump = True
        if entry.get("event") in ("FSDJump"):
            self.mid_jump = False

        reset = (entry.get("event") in ("StartJump", "FSDJump"))
        reset = reset or (entry.get("event") == "Music" and entry.get(
            "MusicTrack") != "GalaxyMap")

        if reset:
            self.hide()


"""
 Makes sure that the cached system values does not exceed 100 items
"""


class SystemCache():
    def __init__(self, maxlen=100):
        self.systems = {}
        self.maxlen = maxlen

    def get(self, value):
        return self.systems.get(value)

    def put(self, value):
        if value.get("id64"):
            self.systems[value.get("id64")] = value
        if len(self.systems) > self.maxlen:
            self.systems.pop(next(iter(self.systems)))


"""

"""


class spanshCheck(threading.Thread):
    def __init__(self, entry, callback):
        threading.Thread.__init__(self)
        self.id64 = entry.get("SystemAddress")
        self.name = entry.get("Name")
        self.starclass = entry.get("StarClass")
        self.callback = callback

    def run(self):
        headers = {
            'User-Agent': f"{ClientVersion.client()} (canonn.target.py)"
        }
        url = f"https://spansh.co.uk/api/dump/{self.id64}"
        spansh = None
        # debug("request {}:  Active Threads {}".format(
        #    url, threading.activeCount()))

        r = requests.get(url, timeout=30, headers=headers)
        # debug("request complete")
        r.encoding = 'utf-8'
        if r.status_code in (requests.codes.ok, requests.codes.not_found):
            # debug("got EDSM Data")
            if requests.codes.ok:
                spansh = r.json()
        else:
            plug.show_error(f"error: canonn -> spansh ({r.status_code})")
            Debug.logger.error(f"error: canonn -> spansh ({r.status_code})")
            Debug.logger.error(r.text)

        spansh["starclass"] = self.starclass
        spansh["name"] = self.name
        spansh["id64"] = self.id64
        self.callback(spansh)


def body_check(spansh):
    bodycount = 0
    totalbodies = None

    if spansh and spansh.get("system"):

        totalbodies = spansh.get("system").get("bodyCount")
        bodycount = 0
        if spansh.get("system").get("bodies"):
            for body in spansh.get("system").get("bodies"):
                if body.get("type") in ('Planet', 'Star'):
                    bodycount += 1
    return [totalbodies, bodycount]


def state_check(spansh):

    bodycount = 0
    totalbodies = None

    if spansh and spansh.get("system"):

        totalbodies = spansh.get("system").get("bodyCount")
        bodycount = 0
        if spansh.get("system").get("bodies"):
            for body in spansh.get("system").get("bodies"):
                if body.get("type") in ('Planet', 'Star'):
                    bodycount += 1

        if totalbodies and totalbodies == bodycount:
            return FULLYSCANNED

        if bodycount > 0 and totalbodies:
            return PARTIALSCAN

        if bodycount > 0:
            return UNKNOWNSCAN

        if spansh.get("system").get("name"):
            return LOGGED

    return MISSING
