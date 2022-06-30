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


class TargetDisplay(Frame):

    def __init__(self, parent, gridrow):
        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        Frame.__init__(
            self,
            parent
        )

        self.news_data = []
        self.columnconfigure(1, weight=1)
        #self.grid(row=gridrow, column=0, sticky="EW", columnspan=1)
        self.grid(row=gridrow, column=0, columnspan=2, sticky="EW")

        self.label = tk.Label(self, text="Target")
        self.label.grid(row=0, column=0, sticky="EW")

        # hidden at first
        self.label.grid_remove()
        # need a callback event to prevent threading disasters
        self.bind('<<setTarget>>', self.set_target)

    def set_target(self, event):
        self.label.pack()
        if self.target_level == 0:
            self.label["background"] = "#9b1d1e"
        if self.target_level == 1:
            self.label["background"] = "#fe7e03"
        if self.target_level == 2:
            self.label["background"] = "#B6EE56"
        if self.target_level == 3:
            self.label["background"] = "#348939"

        self.label.config(fg="black")
        self.label["text"] = self.target_text

    def safe_callback(self, text, level):
        self.target_text = text
        self.target_level = level
        self.event_generate('<<setTarget>>', when='tail')

    def journal_entry(self, cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, entry,
                      state, x, y, z, body, nearloc, client):
        if entry.get("event") == "FSDTarget":
            navroute = state.get("NavRoute")
            if navroute and navroute.get("Route"):

                for route_system in navroute.get("Route"):
                    if route_system.get("SystemAddress") == entry.get("SystemAddress"):
                        self.grid_remove()
                        return

            spanshCheck(entry.get("SystemAddress"), entry.get(
                "Name"), self.safe_callback).start()

        reset = (entry.get("event") in ("StartJump", "FSDJump"))
        reset = reset or (entry.get("event") == "Music" and entry.get(
            "MusicTrack") != "GalaxyMap")

        if reset:
            self.grid_remove()


class spanshCheck(threading.Thread):
    def __init__(self, id64, name, callback):
        threading.Thread.__init__(self)
        self.id64 = id64
        self.name = name
        self.callback = callback

    def run(self):
        url = f"https://spansh.co.uk/api/dump/{self.id64}"
        spansh = None
        # debug("request {}:  Active Threads {}".format(
        #    url, threading.activeCount()))

        r = requests.get(url, timeout=30)
        # debug("request complete")
        r.encoding = 'utf-8'
        if r.status_code == requests.codes.ok:
            # debug("got EDSM Data")
            spansh = r.json()

        totalbodies=None
        if spansh:
            totalbodies=spansh.get("system").get("bodyCount")
        bodycount=0
        if spansh and spansh.get("system").get("bodies"):
            for body in spansh.get("system").get("bodies"):
                if body.get("type") in ('Planet','Star'):
                    bodycount+=1

        
        if spansh and totalbodies and totalbodies == bodycount:
            self.callback(f"Target: {self.name} fully scanned", 3)
            return

        if spansh and bodycount > 0 and totalbodies:
            self.callback(f"Target: {self.name} scanned {bodycount}/{totalbodies}", 2)
            return

        if spansh and bodycount > 0:
            self.callback(f"Target: {self.name} scanned {bodycount}/?", 2)
            return

        if spansh and spansh.get("system").get("name"):
            self.callback(f"Target: {self.name} logged", 1)
            return

        self.callback(f"Target: {self.name} missing", 0)
