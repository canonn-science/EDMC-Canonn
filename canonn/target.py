import plug
import threading
import requests
import json

try:
    import tkinter as tk
    from tkinter import Frame
except:
    import Tkinter as tk
    from Tkinter import Frame

from canonn.debug import Debug


class TargetDisplay():

    def __init__(self, parent, gridrow):
        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        self.frame = Frame(parent)

        self.news_data = []
        self.mid_jump = False
        self.frame.columnconfigure(1, weight=1)
        #self.grid(row=gridrow, column=0, sticky="EW", columnspan=1)
        self.frame.grid(row=gridrow, column=0, columnspan=2, sticky="EW")

        self.label = tk.Label(self.frame, text="Target")
        self.label.grid(row=0, column=0, sticky="EW")

        # hidden at first
        self.label.grid_remove()
        # self.grid_remove()
        # need a callback event to prevent threading disasters
        self.frame.bind('<<setTarget>>', self.set_target)

    def set_target(self, event):
        # self.grid()#
        self.label.grid()

        if self.target_level == 0:
            self.label["background"] = "#fc0303"
        if self.target_level == 1:
            self.label["background"] = "#FFA500"
        if self.target_level == 2:
            self.label["background"] = "#ffff00"
        if self.target_level == 3:
            self.label["background"] = "#00ff00"

        self.label.config(fg="black")
        self.label["text"] = self.target_text

    def safe_callback(self, text, level):
        self.target_text = text
        self.target_level = level
        self.frame.event_generate('<<setTarget>>', when='head')

    def journal_entry(self, cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, entry,
                      state, x, y, z, body, nearloc, client):
        if entry.get("event") == "FSDTarget":

            navroute = state.get("NavRoute")
            if navroute and navroute.get("Route"):

                for route_system in navroute.get("Route"):
                    if route_system.get("SystemAddress") == entry.get("SystemAddress"):
                        self.label["text"] = None
                        self.label.grid_remove()
                        self.frame.grid()

                        return

            if not self.mid_jump:
                spanshCheck(entry, self.safe_callback).start()

        if entry.get("event") in ("StartJump"):
            self.mid_jump = True
        if entry.get("event") in ("FSDJump"):
            self.mid_jump = False

        reset = (entry.get("event") in ("StartJump", "FSDJump"))
        reset = reset or (entry.get("event") == "Music" and entry.get(
            "MusicTrack") != "GalaxyMap")

        if reset:
            self.label["text"] = None
            self.label.grid_remove()
            self.frame.grid()


class spanshCheck(threading.Thread):
    def __init__(self, entry, callback):
        threading.Thread.__init__(self)
        self.id64 = entry.get("SystemAddress")
        self.name = entry.get("Name")
        self.starclass = entry.get("StarClass")
        self.callback = callback

    def run(self):
        url = f"https://spansh.co.uk/api/dump/{self.id64}"
        spansh = None
        # debug("request {}:  Active Threads {}".format(
        #    url, threading.activeCount()))

        r = requests.get(url, timeout=30)
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

        totalbodies = None

        if spansh and spansh.get("system"):

            totalbodies = spansh.get("system").get("bodyCount")
            bodycount = 0
            if spansh.get("system").get("bodies"):

                for body in spansh.get("system").get("bodies"):
                    if body.get("type") in ('Planet', 'Star'):
                        bodycount += 1

            if totalbodies and totalbodies == bodycount:

                self.callback(
                    f"Target: {self.name} fully scanned {bodycount}/{totalbodies} ({self.starclass})", 3)
                return

            if bodycount > 0 and totalbodies:

                self.callback(
                    f"Target: {self.name} scanned {bodycount}/{totalbodies} ({self.starclass})", 2)
                return

            if bodycount > 0:

                self.callback(
                    f"Target: {self.name} scanned {bodycount}/? ({self.starclass})", 2)
                return

            if spansh.get("system").get("name"):

                self.callback(
                    f"Target: {self.name} logged ({self.starclass})", 1)
                return

        self.callback(f"Target: {self.name} missing ({self.starclass})", 0)
