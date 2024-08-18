"""
Patrols
"""

try:
    import tkinter as tk
    from tkinter import Frame
    from urllib.parse import quote_plus
except:
    import Tkinter as tk
    from Tkinter import Frame
    from urllib import quote_plus
import shutil
import codecs
import csv
import datetime
from datetime import date
import json
import math
from tkinter import N
import myNotebook as nb
import os
import re
import requests
import threading
import time
import uuid
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.release import Release
from canonn.systems import Systems
from config import config
from contextlib import closing
from l10n import Locale
from ttkHyperlinkLabel import HyperlinkLabel
import html
import plug
import canonn.overlayserver as overlayService

CYCLE = 60 * 1000 * 60  # 60 minutes
DEFAULT_URL = ""
WRAP_LENGTH = 200

THARGOIDSITES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFRhsa3g0tpYFkqyBR2HrfUjXfjW6gSRnnDhFtVtPlWtpuNAHKujI5fH6Lnh3ctt0SAyNywnesv8H_/pub?gid=1675294629&single=true&output=tsv"
GUARDIANSITES = "https://drive.google.com/uc?id=1m8q9lE4_cAI8CotM-oaEm5RWHeeJjoil"
# FLEETCARRIERS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSozf4Ii8TbuDCmk8Qk5ld1W0fUF_5EyHP-OvvnjRQmC9v8NF2_ZZLFy7XOe8pQWTXudaVgdAfxlCFo/pub?gid=470243264&single=true&output=tsv"

ship_types = {}
overlay_settings = {}


def gnosis(ds=None):

    def weeks_between(d1, d2):
        result = (d1 - d2).days // 7
        return result

    if ds:
        target = datetime.datetime.strptime(ds + " 07", "%Y-%m-%d %H")
    else:
        target = datetime.datetime.utcnow()

    ref_date = datetime.datetime.strptime("2020-09-17 07", "%Y-%m-%d %H")

    systems = [
        {
            "system": "Varati",
            "desc": "Visit the home of Canonn Interstellar Research on the Gnosis",
            "coords": [-178.65625, 77.125, -87.125],
        },
        {
            "system": "HIP 17862",
            "desc": "Join the Gnosis to investigate the thargoid wreckage",
            "coords": [-81.4375, -151.90625, -359.59375],
        },
        {
            "system": "Pleiades Sector PN-T b3-0",
            "desc": "All aboard the Gnosis to investigate the Barnacle Forest",
            "coords": [-79.53125, -199.9375, -361.593750],
        },
        {
            "system": "Synuefe PR-L b40-1",
            "desc": "Visit the protolagrange clouds on the Gnosis (Subject to availability)",
            "coords": [365.78125, -291.75, -188.65625],
        },
        {
            "system": "HIP 18120",
            "desc": "Space pumpkin carving on board the Gnosis",
            "coords": [345.75, -435.71875, -125.5],
        },
        {
            "system": "IC 2391 Sector CQ-Y c16",
            "desc": "Light up the guardian beacons on the Gnosis",
            "coords": [559.875, -87.15625, -33.15625],
        },
        {
            "system": "Kappa-1 Volantis",
            "desc": "Join the Gnosis for a relaxing meditation session to the sound of the brain trees",
            "coords": [396.90625, -142.5625, 106.09375],
        },
        {
            "system": "Epsilon Indi",
            "desc": "Take a thrilling trip around Mitterand Hollow on the Gnosis",
            "coords": [3.125, -8.875, 7.125],
        },
    ]

    wb = weeks_between(target, ref_date)
    wp = wb % 8

    return systems[wp]


def getShipType(id):
    global ship_types
    if ship_types.get(id):
        return ship_types.get(id).get("name")
    return "None"


def getShipSize(id):
    global ship_types
    print(f"ship id {id}")
    if ship_types.get(id):
        print(ship_types.get(id))
        return ship_types.get(id).get("size")
    return "L"


def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id


class UpdateThread(threading.Thread):
    def __init__(self, widget):
        threading.Thread.__init__(self)
        self.widget = widget

    def run(self):
        Debug.logger.debug("Patrol: UpdateThread")
        # download cannot contain any tkinter changes
        self.widget.download()


def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)


def get(list, index):
    try:
        return list[index]
    except:
        return None


class PatrolLink(HyperlinkLabel):

    def __init__(self, parent):
        HyperlinkLabel.__init__(
            self,
            parent,
            text="Waiting for location..",
            url=DEFAULT_URL,
            popup_copy=True,
            # wraplength=50,  # updated in __configure_event below
            anchor=tk.NW,
        )
        # self.bind('<Configure>', self.__configure_event)

    def __configure_event(self, event):
        """Handle resizing."""
        # Debug.logger.debug("Patrol: Link widget resize")
        self.configure(wraplength=event.width)


class InfoLink(HyperlinkLabel):

    def __init__(self, parent):
        HyperlinkLabel.__init__(
            self,
            parent,
            text="Waiting for location",
            url=DEFAULT_URL,
            popup_copy=True,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW,
        )
        self.resized = False
        self.lasttime = datetime.datetime.now()
        self.bind("<Configure>", self.__configure_event)

    def __configure_event(self, event):
        """Handle resizing."""

        difference = datetime.datetime.now() - self.lasttime
        # Debug.logger.debug("diff {}".format(difference.total_seconds()))
        if difference.total_seconds() > 0.5:
            self.resized = False

        if not self.resized:
            # Debug.logger.debug("Patrol widget resize")
            self.resized = True
            self.configure(wraplength=event.width - 2)
            self.lasttime = datetime.datetime.now()


class CanonnPatrol(Frame):

    def __init__(self, parent, container, gridrow):
        """Initialise the ``Patrol``."""

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        Frame.__init__(self, container)
        self.parent = parent
        self.ships = []
        self.bind("<<PatrolDone>>", self.update_ui)
        self.IMG_PREV = tk.PhotoImage(
            file=os.path.join(CanonnPatrol.plugin_dir, "icons", "left_arrow.gif")
        )
        self.IMG_NEXT = tk.PhotoImage(
            file=os.path.join(CanonnPatrol.plugin_dir, "icons", "right_arrow.gif")
        )

        self.patrol_config = os.path.join(
            config.app_dir_path, "canonn", "EDMC-Canonn.patrol"
        )

        self.canonnbtn = tk.IntVar(value=config.get_int("HideCanonn"))
        self.factionbtn = tk.IntVar(value=config.get_int("HideFaction"))
        # self.hideshipsbtn = tk.IntVar(value=config.get_int("HideShips"))
        self.edsmbtn = tk.IntVar(value=config.get_int("HideEDSM"))
        self.copypatrolbtn = tk.IntVar(value=config.get_int("CopyPatrol"))
        self.thargoidbtn = tk.IntVar(value=config.get_int("HideThargoids"))
        self.guardianbtn = tk.IntVar(value=config.get_int("HideGuardians"))

        # Overlay
        self.overlay_enabled_btn = tk.IntVar(value=config.get_int("EnableOverlay"))
        self.overlay_patrol_enabled_btn = tk.IntVar(
            value=config.get_int("EnableOverlayPatrol")
        )
        self.overlay_addinfo_enabled_btn = tk.IntVar(
            value=config.get_int("EnableOverlayAddinfo")
        )
        self.overlay_nearest_enabled_btn = tk.IntVar(
            value=config.get_int("EnableOverlayNearest")
        )
        self.overlay_enabled = self.overlay_enabled_btn.get()
        self.overlay_patrol_enabled = self.overlay_enabled_btn.get()
        self.overlay_addinfo_enabled = self.overlay_enabled_btn.get()
        self.overlay_nearest_enabled = self.overlay_nearest_enabled_btn.get()
        # self.fleetbtn = tk.IntVar(value=config.get_int("HideFleet"))

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        # self.hideships = self.hideshipsbtn.get()
        self.copypatrol = self.copypatrolbtn.get()
        self.edsm = self.edsmbtn.get()
        self.thargoids = self.thargoidbtn.get()
        self.guardians = self.guardianbtn.get()
        # self.fleet = self.fleetbtn.get()

        self.columnconfigure(1, weight=1)
        self.columnconfigure(4, weight=4)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        # Text Instructions for the patrol
        self.label = tk.Label(self, text="POI:")
        self.label.grid(row=0, column=0, sticky=sticky)

        self.hyperlink = PatrolLink(self)
        self.hyperlink.grid(row=0, column=2)
        self.distance = tk.Label(self, text="...")
        self.distance.grid(row=0, column=3, sticky="NSEW")
        self.distance.grid_remove()

        # Text Instructions for the patrol
        self.infolink = InfoLink(self)
        self.infolink.grid(row=1, column=0, sticky="NSEW", columnspan=5)
        self.infolink.grid_remove()

        # buttons for the patrol
        self.prev = tk.Button(
            self, text="Prev", image=self.IMG_PREV, width=14, height=14, borderwidth=0
        )
        # self.submit=tk.Button(self, text="Open")
        self.next = tk.Button(
            self, text="Next", image=self.IMG_NEXT, width=14, height=14, borderwidth=0
        )

        # self.submit.grid(row = 2, column = 1,sticky="NSW")
        self.prev.grid(row=0, column=1, sticky="W")
        self.next.grid(row=0, column=4, sticky="E")
        self.prev.bind("<Button-1>", self.patrol_prev)
        self.next.bind("<Button-1>", self.patrol_next)

        self.prev.grid_remove()
        self.next.grid_remove()

        self.excluded = {}

        self.patrol_list = []
        self.capi_update = False
        self.patrol_count = 0
        self.patrol_pos = 0
        self.minutes = 0

        self.isvisible = False
        self.visible()
        self.cmdr = ""
        self.nearest = {}

        self.system = ""

        self.body = ""
        self.lat = ""
        self.lon = ""

        self.started = False
        self.downloaded = False
        # self.patrol_update()
        self.bind("<<PatrolDisplay>>", self.update_desc)

    def update_desc(self, event):
        self.hyperlink["text"] = "Fetching {}".format(self.patrol_name)
        self.hyperlink["url"] = None

    def copyclip(self, value):
        # Debug.logger.debug("copyclip")

        self.parent.clipboard_clear()  # clear clipboard contents
        self.parent.clipboard_append(value)
        self.parent.update()

        # Debug.logger.debug("copyclip done")

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

        # load ship_types ref data
        global ship_types
        global overlay_settings
        file = os.path.join(cls.plugin_dir, "data", "ships.json")
        with open(file) as json_file:
            ship_types = json.load(json_file)

        # make the config directory pass if it fails
        try:
            os.mkdir(os.path.join(config.app_dir_path, "canonn"))
        except OSError as error:
            pass

        overlay_json = os.path.join(config.app_dir_path, "canonn", "overlay.json")
        if not os.path.exists(overlay_json):
            defaults = os.path.join(cls.plugin_dir, "data", "overlay.json")
            shutil.copyfile(defaults, overlay_json)

        patrol_json = os.path.join(config.app_dir_path, "canonn", "EDMC-Canonn.patrol")
        if not os.path.exists(patrol_json):
            defaults = os.path.join(cls.plugin_dir, "data", "EDMC-Canonn.patrol")
            if os.path.exists(defaults):
                shutil.copyfile(defaults, patrol_json)

        with open(overlay_json) as json_file:
            overlay_settings = json.load(json_file)

    """
    Every hour we will download the latest data
    """

    def patrol_update(self):
        UpdateThread(self).start()
        # removing the timer to see if it makes things more stable
        # Debug.logger.debug('self.after(CYCLE, self.patrol_update)')
        # self.after(CYCLE, self.patrol_update)

    def patrol_next(self, event):
        """
        When the user clicks next it will hide the current patrol for the duration of the session
        It does this by setting an excluded flag on the patrl list
        """
        # if it the last patrol lets not go any further.
        index = self.nearest.get("index")
        if index + 1 < len(self.patrol_list):
            # Debug.logger.debug("len {} ind {}".format(
            #    len(self.patrol_list), index))
            self.nearest["excluded"] = True
            self.patrol_list[index]["excluded"] = True
            self.update()
            if self.copypatrol == 1:
                self.copyclip(self.nearest.get("system"))
            # if there are excluded closer then we might need to deal with it
            # self.prev.grid()

    def patrol_prev(self, event):
        """
        When the user clicks next it will unhide the previous patrol
        It does this by unsetting the excluded flag on the previous patrol
        """
        index = self.nearest.get("index")
        # Debug.logger.debug("prev {}".format(index))

        if index > 0:
            self.patrol_list[index - 1]["excluded"] = False
            self.update()
            if self.copypatrol == 1:
                self.copyclip(self.nearest.get("system"))

    def update_ui(self, event):
        # rerun every 5 seconds
        # Debug.logger.debug('in update_ui')
        # self.after(5000, self.update_ui)
        self.update()

    def update(self):

        if self.visible():

            # Debug.logger.debug("Patrol update: Visible")
            capi_update = self.patrol_list and self.system and self.capi_update
            journal_update = self.patrol_list and self.system

            if journal_update or capi_update:
                # Debug.logger.debug("journal_update or capi_update")
                self.sort_patrol()
                p = Systems.edsmGetSystem(self.system)
                self.nearest = self.getNearest(p)
                self.hyperlink["text"] = self.nearest.get("system")
                self.hyperlink["url"] = (
                    "https://www.edsm.net/en/system?systemName={}".format(
                        quote_plus(self.nearest.get("system"))
                    )
                )
                self.distance["text"] = "{}ly".format(
                    Locale.stringFromNumber(
                        getDistance(p, self.nearest.get("coords")), 1
                    )
                )
                if self.system == self.nearest.get("system"):
                    self.distance["text"] = "0ly"
                self.infolink["text"] = self.nearest.get("instructions")
                self.infolink["url"] = self.parseurl(self.nearest.get("url"))

                self.infolink.grid()
                self.distance.grid()
                self.prev.grid()
                self.next.grid()
                self.capi_update = False

                # Overlay
                cfg = {
                    "EnableOverlay": self.overlay_enabled,
                    "EnableOverlayPatrol": self.overlay_patrol_enabled,
                    "EnableOverlayAddinfo": self.overlay_addinfo_enabled,
                    "EnableOverlayNearest": self.overlay_nearest_enabled,
                }
                # rating scrap
                if len(self.infolink["text"].split("(Rating ")) > 1:
                    rating = self.infolink["text"].split("(Rating ")[1].split("/")[0]
                else:
                    rating = "N/A"
                data = {
                    "system": self.nearest.get("system"),
                    "distance": self.distance["text"].replace("ly", ""),
                    "text": self.infolink["text"],
                    "rating": rating,
                }
                global overlay_settings
                overlayService.overlayDisplayMessage(
                    data, cfg, "patrol", overlay_settings
                )

                # Debug.logger.debug("finished refresh")
            else:
                if self.system:
                    self.hyperlink["text"] = "Fetching patrols..."
                else:
                    self.hyperlink["text"] = "Waiting for location"
                self.infolink.grid_remove()
                self.distance.grid_remove()
                self.prev.grid_remove()
                self.next.grid_remove()

    def getStates(self, state_name, bgs):
        sa = []
        active_states = bgs.get(state_name)
        if active_states:
            sa = active_states[0].values()

        if sa:
            states = ","
            states = states.join(sa)
            return states
        else:
            return None

    def getBGSInstructions(self, bgs):
        target = 0.50 <= float(bgs.get("influence")) <= 0.65
        over = float(bgs.get("influence")) > 0.65
        under = float(bgs.get("influence")) < 0.50

        if self.getStates("active_states", bgs):
            states = " States: {}".format(self.getStates("active_states", bgs))
        else:
            states = ""

        # 2019-03-24T11:14:38.000Z
        d1 = datetime.datetime.strptime(bgs.get("updated_at"), "%Y-%m-%dT%H:%M:%S.%fZ")
        d2 = datetime.datetime.now()

        last_updated = (d2 - d1).days
        if last_updated == 0:
            update_text = ""
        elif last_updated == 1:
            update_text = ". Last updated 1 day ago"
        elif last_updated < 7:
            update_text = ". Last updated {} days ago".format(last_updated)
        elif last_updated > 6:
            update_text = ". Last updated {} days ago. Please jump into the system to update the stats".format(
                last_updated
            )

        # if  self.getStates("pending_states",bgs):
        # pstates=" Pending: {}".format(self.getStates("pending_states",bgs))
        # else:
        # pstates=""

        # Debug.logger.debug(bgs)
        if target:
            retval = "Canonn Influence {}%{}{}".format(
                Locale.stringFromNumber(float(bgs.get("influence") * 100), 2),
                states,
                update_text,
            )
        if over:
            retval = "Canonn Influence {}%{} Check #mission_minor_faction on discord for instructions.{}".format(
                Locale.stringFromNumber(float(bgs.get("influence") * 100), 2),
                states,
                update_text,
            )
        if under:
            retval = "Canonn Influence {}%{} Please complete missions for Canonn to increase our influence{}".format(
                Locale.stringFromNumber(float(bgs.get("influence") * 100), 2),
                states,
                update_text,
            )

        # Debug.logger.debug("{}: {}".format(bgs.get("system_name"), retval))
        return retval

    def getGnosis(self):
        patrol = []
        gpos = gnosis()
        patrol.append(
            newPatrol(
                "GNOSIS",
                gpos.get("system"),
                gpos.get("coords"),
                gpos.get("desc"),
                None,
                None,
            )
        )
        return patrol

    def getBGSOveride(self):
        BGSOveride = []
        SystemsOvireden = []
        # Set your BGS override link(tsv)
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTqwb4MYDrfSuBzRRGpA3R1u0kzKzSPuPBudVukWm4_Ti9G9KPaW2hWdwxwOJ2vHybywVOb-O2-tTBH/pub?gid=0&single=true&output=tsv"
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.reader(r.content.decode("utf-8").splitlines(), delimiter="\t")
            next(reader)
            for row in reader:

                system, x, y, z, TINF, TFAC, Description = row
                instructions = Description.format(TFAC, TINF)
                # SystemsOvireden = []

                if system != "":
                    try:
                        BGSOveride.append(
                            newPatrol(
                                "BGSO",
                                system,
                                (float(x), float(y), float(z)),
                                instructions,
                                None,
                                None,
                            )
                        )
                        SystemsOvireden.append(system)
                    except:
                        Debug.logger.error(
                            "patrol {},{},{},{},{},{},{},{}".format(
                                "BGSO", system, x, y, z, instructions, None, None
                            )
                        )
                else:
                    Debug.logger.error("Patrol contains blank lines")
                # Debug.logger.debug(BGSOveride)
        return BGSOveride, SystemsOvireden

    def getBGSPatrol(self, bgs, BGSOSys):
        x, y, z = Systems.edsmGetSystem(bgs.get("system_name"))
        if bgs.get("system_name") in BGSOSys:
            return
        else:
            return newPatrol(
                "BGS",
                bgs.get("system_name"),
                (x, y, z),
                self.getBGSInstructions(bgs),
                "https://elitebgs.app/system/{}".format(bgs.get("system_id")),
            )

    def getFactionData(self, faction, BGSOSys):
        """
        We will get Canonn faction data using an undocumented elitebgs api
        NB: It is possible this could get broken so need to contact CMDR Garud
        """

        patrol = []

        url = "https://elitebgs.app/frontend/factions?name={}".format(faction)
        j = requests.get(url).json()
        if j:
            for bgs in j.get("docs")[0].get("faction_presence"):
                patrol.append(self.getBGSPatrol(bgs, BGSOSys))

        return patrol

    def parseurl(self, url):
        """
        We will provided some sunstitute variables for the urls
        """
        if url:
            r = url.replace("{CMDR}", self.cmdr)

            # We will need to initialise to "" if not

            if not self.lat:
                self.lat = ""
            if not self.lon:
                self.lon = ""
            if not self.body:
                self.body = ""

            r = r.replace("{LAT}", str(self.lat))
            r = r.replace("{LON}", str(self.lon))
            r = r.replace("{BODY}", self.body)

            return r
        else:
            return url

    def getJsonPatrol(self, url):
        canonnpatrol = []

        try:
            a, b, c = Systems.edsmGetSystem(self.system)
        except:
            a, b, c = (0, 0, 0)
        if "?" in url:
            newurl = "{}&x={}&y={}&z={}".format(url, a, b, c)
        else:
            newurl = "{}?x={}&y={}&z={}".format(url, a, b, c)

        Debug.logger.debug("getting patrol {}".format(newurl))

        with closing(requests.get(newurl)) as r:
            if not r.status_code == requests.codes.ok:
                Debug.logger.error(json.dumps(newurl))
                headers = r.headers
                contentType = str(headers["content-type"])
                if "json" in contentType:
                    Debug.logger.error(json.dumps(r.content))
                else:
                    Debug.logger.error(r.content)
                Debug.logger.error(r.status_code)
            else:
                reader = r.json()
                for row in reader:

                    type = row.get("type")
                    system = row.get("system")
                    x = row.get("x")
                    y = row.get("y")
                    z = row.get("z")
                    instructions = row.get("instructions")
                    url = row.get("url")
                    event = row.get("event")
                    if system != "":
                        try:
                            canonnpatrol.append(
                                newPatrol(
                                    type,
                                    system,
                                    (float(x), float(y), float(z)),
                                    instructions,
                                    url,
                                    event,
                                )
                            )
                        except:
                            Debug.logger.error(
                                "patrol {},{},{},{},{},{},{},{}".format(
                                    type, system, x, y, z, instructions, url, event
                                )
                            )
                    else:
                        Debug.logger.error(
                            "Patrol {} contains blank lines".format(type)
                        )

        return canonnpatrol

    def getTsvPatrol(self, url):
        canonnpatrol = []

        with closing(requests.get(url, stream=True)) as r:
            reader = csv.reader(r.content.decode("utf-8").splitlines(), delimiter="\t")
            next(reader)
            for row in reader:

                type = get(row, 0)
                system = get(row, 1)
                x = get(row, 2)
                y = get(row, 3)
                z = get(row, 4)
                instructions = get(row, 5)
                url = get(row, 6)
                event = get(row, 7)
                if system != "":
                    try:
                        canonnpatrol.append(
                            newPatrol(
                                type,
                                system,
                                (float(x), float(y), float(z)),
                                instructions,
                                url,
                                event,
                            )
                        )
                    except:
                        Debug.logger.error(
                            "patrol {},{},{},{},{},{},{},{}".format(
                                type, system, x, y, z, instructions, url, event
                            )
                        )
                else:
                    Debug.logger.error("Patrol contains blank lines")

        return canonnpatrol

    def getCanonnPatrol(self):
        canonnpatrol = []
        c = 0

        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQsi1Vbfx4Sk2msNYiqo0PVnW3VHSrvvtIRkjT-JvH_oG9fP67TARWX2jIjehFHKLwh4VXdSh0atk3J/pub?gid=0&single=true&output=tsv"
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.reader(r.content.decode("utf-8").splitlines(), delimiter="\t")
            next(reader)
            for row in reader:
                c = c + 1
                id, enabled, description, type, link = row
                self.patrol_name = "{} ({})".format(description, c)

                if enabled == "Y":
                    if type == "json":
                        Debug.logger.debug("{} Patrol enabled".format(description))
                        if not self.started:
                            self.event_generate("<<PatrolDisplay>>", when="tail")
                        canonnpatrol = canonnpatrol + self.getJsonPatrol(link)

                    elif type == "tsv":
                        Debug.logger.debug("{} Patrol enabled".format(description))
                        if not self.started and not config.shutting_down:
                            self.event_generate("<<PatrolDisplay>>", when="tail")
                        canonnpatrol = canonnpatrol + self.getTsvPatrol(link)

                    else:
                        Debug.logger.debug("no patrol {}".format(row))
                else:
                    Debug.logger.debug("{} Patrol disabled".format(description))

        Debug.logger.debug("Finished loading Canonn Patrols")
        return canonnpatrol

    def keyval(self, k):
        # code smell!
        # getting a blank or null system so we will push it to the end
        if self.system and k:
            x, y, z = Systems.edsmGetSystem(self.system)
            return getDistance((x, y, z), k.get("coords"))
        else:
            return 999999

    def sort_patrol(self):

        patrol_list = sorted(self.patrol_list, key=self.keyval)

        for num, val in enumerate(patrol_list):
            if val:
                system = val.get("system")
                type = val.get("type")

                patrol_list[num]["index"] = num
        self.patrol_list = patrol_list

    def download(self):

        if self.system:
            Debug.logger.debug("Download Patrol Data")

            # Debug.logger.debug(
            #    "Patrol Download for system {}".format(self.system))

            # if patrol list is populated then was can save
            if self.patrol_list:
                self.save_excluded()
            else:
                self.load_excluded()

            patrol_list = []
            if self.faction != 1:
                # Debug.logger.debug("Getting Faction Data")
                self.patrol_name = "Cannon Factions"
                if not self.started and not config.shutting_down:
                    self.event_generate("<<PatrolDisplay>>", when="tail")

                # first variable- for patrol_list, second-for ignore existant systems
                BGSO, BGSOSys = self.getBGSOveride()

                if BGSO:
                    patrol_list.extend(BGSO)

                # p = self.getFactionData("Canonn", BGSOSys)
                # if p:
                #     patrol_list.extend(p)
                # p = self.getFactionData("Canonn Deep Space Research", BGSOSys)
                # patrol_list.extend(p)
                try:
                    patrol_list.remove(None)
                except:
                    Debug.logger.debug("Nothing to delete")

            Debug.logger.debug("Getting Gnosis")
            self.patrol_name = "The Gnosis"
            if not self.started and not config.shutting_down:
                self.event_generate("<<PatrolDisplay>>", when="tail")
            gnosisPatrol = self.getGnosis()
            if gnosisPatrol:
                patrol_list.extend(gnosisPatrol)

            if self.thargoids != 1:
                Debug.logger.debug("Getting Thargoid Tour")
                self.patrol_name = "Thargoid Tour"
                if not self.started and not config.shutting_down:
                    self.event_generate("<<PatrolDisplay>>", when="tail")
                patrol_list.extend(self.getTsvPatrol(THARGOIDSITES))

            if self.guardians != 1:
                Debug.logger.debug("Getting Guardian Tour")
                self.patrol_name = "Guardian Tour"
                if not self.started and not config.shutting_down:
                    self.event_generate("<<PatrolDisplay>>", when="tail")
                patrol_list.extend(self.getJsonPatrol(GUARDIANSITES))

            # if self.fleet != 1:
            #    Debug.logger.debug("Getting DSSA Locations")
            #    self.patrol_name = "DSSA Locations"
            #    if not self.started:
            #        self.event_generate('<<PatrolDisplay>>', when='tail')
            # patrol_list.extend(self.getPatrol(GUARDIANSITES))
            # requires a new function

            if self.canonn != 1:
                self.canonnpatrol = self.getCanonnPatrol()
                patrol_list.extend(self.canonnpatrol)

            if self.edsm != 1:
                patrol_list.extend(self.getEDSMPatrol())

            # add exclusions from configuration
            Debug.logger.debug("adding exclusions")
            for num, val in enumerate(patrol_list):
                if val:

                    system = val.get("system")
                    type = val.get("type")

                    if self.excluded.get(type):
                        if self.excluded.get(type).get(system):
                            patrol_list[num]["excluded"] = self.excluded.get(type).get(
                                system
                            )

            # we will sort the patrol list
            self.patrol_list = patrol_list
            self.sort_patrol()

            Debug.logger.debug("download done")
            self.started = True
            # poke an evennt safely
            if not config.shutting_down:
                self.event_generate("<<PatrolDone>>", when="tail")

    def getEDSMPatrol(self):
        url = "https://www.edsm.net/en/galactic-mapping/json"

        types = {
            "minorPOI": "Minor Point of Interest",
            "planetaryNebula": "Planetary Nebula",
            "nebula": "Nebula",
            "blackHole": "Black Hole",
            "historicalLocation": "Historical Location",
            "stellarRemnant": "Stellar Remnant",
            "planetFeatures": "Planet Features",
            "regional": "Regional",
            "pulsar": "Pulsar",
            "starCluster": "Star Cluster",
            "jumponiumRichSystem": "Jumponium Rich System",
            "surfacePOI": "Surface Point of Interest",
            "deepSpaceOutpost": "Deep Space Outpost",
            "mysteryPOI": "Mystery Point of Interest",
            "organicPOI": "Organic Point of Interest",
            "restrictedSectors": "Restricted Sector",
            "geyserPOI": "Geyser Point of Interest",
            "region": "Region",
            "travelRoute": "Travel Route",
            "historicalRoute": "Historical Route",
            "minorRoute": "Minor Route",
            "neutronRoute": "Neutron Route",
        }

        validtypes = [
            "minorPOI",
            "planetaryNebula",
            "nebula",
            "blackHole",
            "historicalLocation",
            "stellarRemnant",
            "planetFeatures",
            "regional",
            "pulsar",
            "starCluster",
            "jumponiumRichSystem",
            "surfacePOI",
            "deepSpaceOutpost",
            "mysteryPOI",
            "organicPOI",
            "restrictedSectors",
            "geyserPOI",
        ]

        try:
            r = requests.get(url)
            r.encoding = "utf-8"
            Debug.logger.debug(r.encoding)
            gmpentries = r.json()
        except Exception as e:
            Debug.logger.error("Failed to fetch GMP POIs")
            Debug.logger.error(e)
            plug.show_error("Canonn: Failed to fetch GMP POIs")

        try:
            gr = requests.get("https://edastro.com/gec/json/all")
            gr.encoding = "utf-8"
            gecentries = gr.json()

        except Exception as e:
            Debug.logger.error("Failed to fetch GEC POIs")
            Debug.logger.error(e)
            plug.show_error("Canonn: Failed to fetch GEC POIs")

        entries = {}

        categories = {}

        self.patrol_name = "Galactic Mapping"

        for entry in gmpentries:

            if entry.get("type") in validtypes and "Archived: " not in entry.get(
                "name"
            ):
                # cache these systems we may need them later
                Systems.storeSystem(entry.get("galMapSearch"), entry.get("coordinates"))

                entries[entry.get("galMapSearch")] = {
                    "system": entry.get("galMapSearch"),
                    "coordinates": entry.get("coordinates"),
                    "instructions": "GMP: {} : {}".format(
                        types.get(entry.get("type")), html.unescape(entry.get("name"))
                    ),
                    "url": entry.get("galMapUrl"),
                }

        for entry in gecentries:

            # cache these systems we may need them later
            Systems.storeSystem(entry.get("galMapSearch"), entry.get("coordinates"))

            entries[entry.get("galMapSearch")] = {
                "system": entry.get("galMapSearch"),
                "coordinates": entry.get("coordinates"),
                "instructions": "GEC: {} : {} (Rating {}/10)".format(
                    html.unescape(entry.get("name")),
                    html.unescape(entry.get("summary")),
                    entry.get("rating"),
                ),
                "url": entry.get("poiUrl"),
            }

        edsm_patrol = []

        for entry in entries.values():
            edsm_patrol.append(
                newPatrol(
                    "Galactic Mapping",
                    entry.get("system"),
                    entry.get("coordinates"),
                    entry.get("instructions"),
                    entry.get("url"),
                    None,
                )
            )

        if not config.shutting_down:
            self.event_generate("<<PatrolDone>>", when="tail")
        return edsm_patrol

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        """Called to get a tk Frame for the settings dialog."""

        self.canonnbtn = tk.IntVar(value=config.get_int("HideCanonn"))
        self.factionbtn = tk.IntVar(value=config.get_int("HideFaction"))
        # self.hideshipsbtn = tk.IntVar(value=config.get_int("HideShips"))
        self.edsmbtn = tk.IntVar(value=config.get_int("HideEDSM"))
        self.thargoidbtn = tk.IntVar(value=config.get_int("HideThargoids"))
        self.guardianbtn = tk.IntVar(value=config.get_int("HideGuardians"))
        self.copypatrolbtn = tk.IntVar(value=config.get_int("CopyPatrol"))
        # self.fleetbtn = tk.IntVar(value=config.get_int("HideFleet"))

        # Overlay part
        self.overlay_enabled_btn = tk.IntVar(value=config.get_int("EnableOverlay"))
        self.overlay_patrol_enabled_btn = tk.IntVar(
            value=config.get_int("EnableOverlayPatrol")
        )
        self.overlay_addinfo_enabled_btn = tk.IntVar(
            value=config.get_int("EnableOverlayAddinfo")
        )
        self.overlay_nearest_enabled_btn = tk.IntVar(
            value=config.get_int("EnableOverlayNearest")
        )

        self.overlay_enabled = self.overlay_enabled_btn.get()
        self.overlay_patrol_enabled = self.overlay_patrol_enabled_btn.get()
        self.overlay_addinfo_enabled = self.overlay_addinfo_enabled_btn.get()
        self.overlay_nearest_enabled = self.overlay_nearest_enabled_btn.get()

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        # self.hideships = self.hideshipsbtn.get()
        self.edsm = self.edsmbtn.get()
        self.copypatrol = self.copypatrolbtn.get()
        self.thargoids = self.thargoidbtn.get()
        self.guardians = self.guardianbtn.get()
        # self.fleet = self.fleetbtn.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Label(frame, text="Patrol Settings").grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Hide Canonn Patrols", variable=self.canonnbtn).grid(
            row=1, column=0, sticky="NW"
        )
        nb.Checkbutton(
            frame, text="Hide Canonn Faction Systems", variable=self.factionbtn
        ).grid(row=1, column=2, sticky="NW")
        # nb.Checkbutton(frame, text="Hide Your Ships", variable=self.hideshipsbtn).grid(row=1, column=3, sticky="NW")
        nb.Checkbutton(frame, text="Hide GMP/GEC POIS", variable=self.edsmbtn).grid(
            row=2, column=0, sticky="NW"
        )
        nb.Checkbutton(
            frame, text="Hide Thargoid Sites", variable=self.thargoidbtn
        ).grid(row=2, column=1, sticky="NW")
        nb.Checkbutton(
            frame, text="Hide Guardian Sites", variable=self.guardianbtn
        ).grid(row=2, column=2, sticky="NW")
        # nb.Checkbutton(frame, text="Hide DSSA Fleet", variable=self.fleetbtn).grid(row=2, column=3,
        #                                                                                  sticky="NW")
        nb.Checkbutton(
            frame,
            text="Automatically copy the patrol to the clipboard (Recommended if using overlay patrols)",
            variable=self.copypatrolbtn,
        ).grid(
            row=3,
            column=0,
            sticky="NW",
        )

        # Overlay part
        nb.Label(frame, text="Overlay Settings").grid(row=4, column=0, sticky="NW")
        nb.Checkbutton(
            frame, text="Enable Overlay", variable=self.overlay_enabled_btn
        ).grid(row=5, column=0, sticky="NW")
        nb.Checkbutton(
            frame, text="Enable Patrols", variable=self.overlay_patrol_enabled_btn
        ).grid(row=5, column=1, sticky="NW")
        nb.Checkbutton(
            frame,
            text="Enable additional information",
            variable=self.overlay_addinfo_enabled_btn,
        ).grid(row=6, column=0, sticky="NW")
        nb.Checkbutton(
            frame,
            text="Enable nearest command",
            variable=self.overlay_nearest_enabled_btn,
        ).grid(row=6, column=1, sticky="NW")

        return frame

    def visible(self):

        # nopatrols = self.canonn == 1 and self.faction == 1 and self.hideships == 1 and self.edsm == 1 and self.thargoids == 1 and self.guardians == 1 and self.fleet == 1
        nopatrols = (
            self.canonn == 1
            and self.faction == 1
            and self.edsm == 1
            and self.thargoids == 1
            and self.guardians == 1
        )

        Debug.logger.debug("no patrols {}".format(nopatrols))

        if nopatrols:
            self.grid()
            self.grid_remove()
            self.isvisible = False
            return False
        else:
            self.grid()

            self.isvisible = True
            return True

    def getNearest(self, location):
        nearest = ""
        for num, patrol in enumerate(self.patrol_list):
            # add the index to the patrol so we can navigate
            if patrol:
                self.patrol_list[num]["index"] = int(num)

                if not patrol.get("excluded"):
                    if nearest != "":

                        if getDistance(location, patrol.get("coords")) < getDistance(
                            location, nearest.get("coords")
                        ):
                            nearest = patrol

                    else:

                        nearest = patrol

        return nearest

    def prefs_changed(self, cmdr, is_beta):
        """Called when the user clicks OK on the settings dialog."""
        config.set("HideCanonn", self.canonnbtn.get())
        config.set("HideFaction", self.factionbtn.get())
        # config.set('HideShips', self.hideshipsbtn.get())
        config.set("HideEDSM", self.edsmbtn.get())
        config.set("HideThargoids", self.thargoidbtn.get())
        config.set("HideGuardians", self.guardianbtn.get())
        # config.set('HideFleet', self.fleetbtn.get())
        config.set("CopyPatrol", self.copypatrolbtn.get())

        # Overlay
        config.set("EnableOverlay", self.overlay_enabled_btn.get())
        config.set("EnableOverlayPatrol", self.overlay_patrol_enabled_btn.get())
        config.set("EnableOverlayAddinfo", self.overlay_addinfo_enabled_btn.get())
        config.set("EnableOverlayNearest", self.overlay_nearest_enabled_btn.get())

        self.overlay_enabled = self.overlay_enabled_btn.get()
        self.overlay_patrol_enabled = self.overlay_patrol_enabled_btn.get()
        self.overlay_addinfo_enabled = self.overlay_addinfo_enabled_btn.get()
        self.overlay_nearest_enabled = self.overlay_nearest_enabled_btn.get()

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        # self.hideships = self.hideshipsbtn.get()
        self.edsm = self.edsmbtn.get()
        self.copypatrol = self.copypatrolbtn.get()
        self.thargoids = self.thargoidbtn.get()
        self.gaurdians = self.guardianbtn.get()
        # self.fleet = self.fleetbtn.get()

        if self.visible():
            # we should fire off an extra download
            UpdateThread(self).start()

    def trigger(self, system, entry):
        # exit if the events dont match

        event = json.loads(self.nearest.get("event"))
        Debug.logger.debug("event {}".format(event))
        for key in event.keys():
            if event.get(key):
                Debug.logger.debug("event key {} value {}".format(key, event.get(key)))

                if not str(entry.get(key)).upper() == str(event.get(key)).upper():
                    return False

        Debug.logger.debug("triggered")
        # autosubmit the form -- allowing for google forms
        if self.nearest.get("url"):
            j = requests.get(
                self.nearest.get("url").replace("viewform", "formResponse")
            )
        self.patrol_next(None)

    def closest(self, message, x, y, z, ship, odyssey):
        # strip the first
        if odyssey:
            horizons = ""
        else:
            horizons = "&horizons=y"

        location = message.lower()[8:].strip().replace(" ", "_")
        if location:
            is_challenge = message.lower() == "nearest challenge"
            trade = message.split(" ")[1].lower()
            is_trade = trade in ("buying", "selling") and len(message.split(" ")) > 2
            if is_trade:
                quantity = message.split(" ")[2]
                if quantity.isnumeric():
                    location = (
                        "_".join(message.split(" ")[3:])
                        .lower()
                        .strip()
                        .replace(" ", "_")
                    )
                else:
                    # set to something sensible
                    quantity = 800
                    location = (
                        "_".join(message.split(" ")[2:])
                        .lower()
                        .strip()
                        .replace(" ", "_")
                    )
                if location:
                    url = f"https://us-central1-populated.cloudfunctions.net/hcs/{trade}/{location}/{ship}/{quantity}?x={x}&y={y}&z={z}{horizons}"
                else:
                    plug.show_error("nearest what?")

            if is_challenge:
                url = f"https://us-central1-canonn-api-236217.cloudfunctions.net/query/challenge/next?cmdr={self.cmdr}&x={x}&y={y}&z={z}{horizons}"

            if not is_trade and not is_challenge:
                url = f"https://us-central1-populated.cloudfunctions.net/hcs/nearest/{location}/{ship}?x={x}&y={y}&z={z}{horizons}"

            Debug.logger.debug(url)
            r = requests.get(url, timeout=30)
            # print(url)
            r.encoding = "utf-8"
            if r.status_code == requests.codes.ok:

                try:

                    j = r.json()

                    system = j.get("system")
                    distance = j.get("distance")
                    station = j.get("station")
                    if j.get("commodity"):
                        if trade == "buying":
                            price = int(j.get("commodity").get("sellPrice"))
                            quantity = int(j.get("commodity").get("demand"))
                        else:
                            price = int(j.get("commodity").get("buyPrice"))
                            quantity = int(j.get("commodity").get("supply"))

                    cfg = {
                        "EnableOverlay": self.overlay_enabled,
                        "EnableOverlayPatrol": self.overlay_patrol_enabled,
                        "EnableOverlayAddinfo": self.overlay_addinfo_enabled,
                        "EnableOverlayNearest": self.overlay_nearest_enabled,
                    }
                    global overlay_settings

                    if message.lower() == "nearest challenge":
                        location = j.get("english_name")
                        distance = float(j.get("distance"))

                        # Overlay nearest_challenge
                        data = {
                            "system": system,
                            "distance": distance,
                            "location": location,
                        }

                        overlayService.overlayDisplayMessage(
                            data, cfg, "nearest_challenge", overlay_settings
                        )
                        self.copyclip(system)

                    self.hyperlink["text"] = system
                    self.hyperlink["url"] = (
                        f"https://www.edsm.net/en/system?systemName={system}"
                    )
                    self.distance["text"] = "{}ly".format(
                        Locale.stringFromNumber(distance, 2)
                    )
                    l = location.replace("_", " ")

                    if is_trade:
                        self.infolink["text"] = (
                            f"{station} is {trade} {Locale.stringFromNumber(quantity,0)} {l} for ${Locale.stringFromNumber(price,0)} in system {system}"
                        )

                        # Overlay trading
                        data = {
                            "station": station,
                            "trade": trade,
                            "text": self.infolink["text"],
                            "system": system,
                            "distance": self.distance["text"],
                        }

                        overlayService.overlayDisplayMessage(
                            data, cfg, "nearest_trading", overlay_settings
                        )
                        self.copyclip(system)

                    else:
                        if station:
                            self.infolink["text"] = (
                                f"Nearest {l} is at {station} in system {system}"
                            )

                            # Overlay station
                            data = {
                                "station": station,
                                "location": l,
                                "text": self.infolink["text"],
                                "system": system,
                                "distance": self.distance["text"],
                            }

                            overlayService.overlayDisplayMessage(
                                data, cfg, "nearest_station", overlay_settings
                            )
                            self.copyclip(system)

                        else:
                            if message != "nearest challenge":  # Avoid triggering twice

                                # Overlay nearest
                                data = {
                                    "station": station,
                                    "location": l,
                                    "text": self.infolink["text"],
                                    "system": system,
                                    "distance": self.distance["text"],
                                }

                                overlayService.overlayDisplayMessage(
                                    data, cfg, "nearest", overlay_settings
                                )
                                self.copyclip(system)

                            self.infolink["text"] = f"Nearest {l} is in system {system}"

                    self.infolink["url"] = (
                        f"https://www.edsm.net/en/system?systemName={system}"
                    )
                except:
                    plug.show_error(f'Can\'t understand "{message}"')
            else:
                plug.show_error("nearest failure")
        else:
            plug.show_error("nearest what?")

    def journal_entry(
        self,
        cmdr,
        is_beta,
        system,
        station,
        entry,
        state,
        x,
        y,
        z,
        body,
        lat,
        lon,
        client,
    ):
        # We don't care what the journal entry is as long as the system has changed.

        self.body = body
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.z = z

        if cmdr:
            self.cmdr = cmdr

        if entry.get("event") in ("Location", "StartUp") and not self.patrol_list:
            self.system = system
            # Overlay startup message

            cfg = {
                "EnableOverlay": self.overlay_enabled,
                "EnableOverlayPatrol": self.overlay_patrol_enabled,
                "EnableOverlayAddinfo": self.overlay_addinfo_enabled,
            }
            global overlay_settings
            overlayService.overlayDisplayMessage(
                "Startup", cfg, "startup", overlay_settings
            )

            if not self.downloaded:
                self.downloaded = True
                self.patrol_update()
            self.update()

        if self.system != system and entry.get("event") in (
            "Location",
            "FSDJump",
            "StartUp",
        ):

            self.system = system
            self.update()
            if self.nearest and self.copypatrol == 1:
                self.copyclip(self.nearest.get("system"))

        # If we have visted a system and then jump out then lets clicknext
        if system and self.nearest:
            if (
                self.nearest.get("system").upper() == system.upper()
                and entry.get("event") == "StartJump"
                and entry.get("JumpType") == "Hyperspace"
            ):
                self.patrol_next(None)

        # After we have done everything else let's see if we can automatically submit and move on
        if (
            system
            and self.nearest.get("event")
            and self.nearest.get("system").upper() == system.upper()
        ):
            self.trigger(system, entry)

        if (
            entry.get("event") == "SendText"
            and entry.get("Message")
            and entry.get("Message").lower().startswith("nearest")
        ):
            self.closest(
                entry.get("Message"),
                x,
                y,
                z,
                getShipSize(state.get("ShipType")),
                state.get("Odyssey"),
            )

    def load_excluded(self):
        Debug.logger.debug("loading excluded")
        self.patrol_config = os.path.join(
            config.app_dir_path, "canonn", "EDMC-Canonn.patrol"
        )
        try:
            with open(self.patrol_config) as json_file:
                self.excluded = json.load(json_file)
        except:
            Debug.logger.debug("no config file {}".format(self.patrol_config))

    def save_excluded(self):
        self.patrol_config = os.path.join(
            config.app_dir_path, "canonn", "EDMC-Canonn.patrol"
        )
        excluded = {}
        for patrol in self.patrol_list:
            if patrol.get("excluded") and not patrol.get("type") in ("BGS", "SHIPS"):
                if not excluded.get(patrol.get("type")):
                    excluded[patrol.get("type")] = {}
                excluded[patrol.get("type")][patrol.get("system")] = True

        with open(self.patrol_config, "w+") as outfile:
            json.dump(excluded, outfile)

    def plugin_stop(self):
        """
        When the plugin stops we want to save the patrols where excluded = True
        We will not inclde ships or BGS in this as they can be excluded in other ways.
        """
        self.save_excluded()

    def cmdr_data(self, data, is_beta):
        """
        We have new data on our commander

        Lets get a list of ships
        """
        self.cmdr = data.get("commander").get("name")

        self.ships = []
        self.system = data.get("lastSystem").get("name")

        self.capi_update = True
        if not self.downloaded:
            self.downloaded = True
            self.patrol_update()
        self.update()


def getDistance(p, g):
    # gets the distance between two systems
    return math.sqrt(sum(tuple([math.pow(p[i] - g[i], 2) for i in range(3)])))


def newPatrol(type, system, coords, instructions, url, event=None):
    return {
        "type": type,
        "system": system,
        "coords": coords,
        "instructions": instructions,
        "url": url,
        "event": event,
    }
