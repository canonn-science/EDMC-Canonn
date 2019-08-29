"""
Patrols
"""

import Tkinter as tk
from Tkinter import Frame
import uuid
from ttkHyperlinkLabel import HyperlinkLabel
import requests
import json
import re
import myNotebook as nb
from config import config
import threading
from systems import Systems
import math
from debug import Debug
from debug import debug, error
import csv
import os
from contextlib import closing
from urllib import quote_plus
from datetime import datetime
from release import Release
from l10n import Locale

CYCLE = 60 * 1000 * 60  # 60 minutes
DEFAULT_URL = ""
WRAP_LENGTH = 200

ship_types = {
    'adder': 'Adder',
    'typex_3': 'Alliance Challenger',
    'typex': 'Alliance Chieftain',
    'typex_2': 'Alliance Crusader',
    'anaconda': 'Anaconda',
    'asp explorer': 'Asp Explorer',
    'asp': 'Asp Explorer',
    'asp scout': 'Asp Scout',
    'asp_scout': 'Asp Scout',
    'beluga liner': 'Beluga Liner',
    'belugaliner': 'Beluga Liner',
    'cobra mk. iii': 'Cobra MkIII',
    'cobramkiii': 'Cobra MkIII',
    'cobra mk. iv': 'Cobra MkIV',
    'cobramkiv': 'Cobra MkIV',
    'diamondback explorer': 'Diamondback Explorer',
    'diamondbackxl': 'Diamondback Explorer',
    'diamondback scout': 'Diamondback Scout',
    'diamondback': 'Diamondback Scout',
    'dolphin': 'Dolphin',
    'eagle': 'Eagle',
    'federal assault ship': 'Federal Assault Ship',
    'federation_dropship_mkii': 'Federal Assault Ship',
    'federal corvette': 'Federal Corvette',
    'federation_corvette': 'Federal Corvette',
    'federal dropship': 'Federal Dropship',
    'federation_dropship': 'Federal Dropship',
    'federal gunship': 'Federal Gunship',
    'federation_gunship': 'Federal Gunship',
    'fer-de-lance': 'Fer-de-Lance',
    'ferdelance': 'Fer-de-Lance',
    'hauler': 'Hauler',
    'imperial clipper': 'Imperial Clipper',
    'empire_trader': 'Imperial Clipper',
    'imperial courier': 'Imperial Courier',
    'empire_courier': 'Imperial Courier',
    'imperial cutter': 'Imperial Cutter',
    'cutter': 'Imperial Cutter',
    'imperial eagle': 'Imperial Eagle',
    'empire_eagle': 'Imperial Eagle',
    'keelback': 'Keelback',
    'independant_trader': 'Keelback',
    'krait_mkii': 'Krait MkII',
    'krait_light': 'Krait Phantom',
    'mamba': 'Mamba',
    'orca': 'Orca',
    'python': 'Python',
    'sidewinder': 'Sidewinder',
    'type 6 transporter': 'Type-6 Transporter',
    'type6': 'Type-6 Transporter',
    'type 7 transporter': 'Type-7 Transporter',
    'type7': 'Type-7 Transporter',
    'type 9 heavy': 'Type-9 Heavy',
    'type9': 'Type-9 Heavy',
    'type 10 defender': 'Type-10 Defender',
    'type9_military': 'Type-10 Defender',
    'viper mk. iii': 'Viper MkIII',
    'viper': 'Viper MkIII',
    'viper mk. iv': 'Viper MkIV',
    'viper_mkiv': 'Viper MkIV',
    'vulture': 'Vulture'
}


def getShipType(key):
    try:
        name = ship_types.get(key.lower())
    except:
        return "None"
    if name:
        return name
    else:
        return key


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
        debug("Patrol: UpdateThread")
        # download cannot contain any tkinter changes
        self.widget.download()


def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)


class PatrolLink(HyperlinkLabel):

    def __init__(self, parent):
        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching Patrol...",
            url=DEFAULT_URL,
            popup_copy=True,
            # wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        # self.bind('<Configure>', self.__configure_event)

    def __configure_event(self, event):
        """Handle resizing."""

        self.configure(wraplength=event.width)


class InfoLink(HyperlinkLabel):

    def __init__(self, parent):
        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching Patrol...",
            url=DEFAULT_URL,
            popup_copy=True,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.resized = False
        self.bind('<Configure>', self.__configure_event)

    def __reset(self):
        self.resized = False;

    def __configure_event(self, event):
        """Handle resizing."""

        if not self.resized:
            self.resized = True
            self.configure(wraplength=event.width)
            self.after(500, self.__reset)


class CanonnPatrol(Frame):

    def __init__(self, parent, gridrow):
        """Initialise the ``Patrol``."""

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        Frame.__init__(
            self,
            parent
        )
        self.ships = []

        self.IMG_PREV = tk.PhotoImage(file=u'{}\\icons\\left_arrow.gif'.format(CanonnPatrol.plugin_dir))
        self.IMG_NEXT = tk.PhotoImage(file=u'{}\\icons\\right_arrow.gif'.format(CanonnPatrol.plugin_dir))

        self.patrol_config = os.path.join(Release.plugin_dir, 'data', 'EDMC-Canonn.patrol')

        self.canonnbtn = tk.IntVar(value=config.getint("HideCanonn"))
        self.factionbtn = tk.IntVar(value=config.getint("HideFaction"))
        self.hideshipsbtn = tk.IntVar(value=config.getint("HideShips"))
        self.copypatrolbtn = tk.IntVar(value=config.getint("CopyPatrol"))

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.hideships = self.hideshipsbtn.get()
        self.copypatrol = self.copypatrolbtn.get()

        self.columnconfigure(1, weight=1)
        self.columnconfigure(4, weight=4)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        ## Text Instructions for the patrol
        self.label = tk.Label(self, text="Patrol:")
        self.label.grid(row=0, column=0, sticky=sticky)

        self.hyperlink = PatrolLink(self)
        self.hyperlink.grid(row=0, column=2)
        self.distance = tk.Label(self, text="...")
        self.distance.grid(row=0, column=3, sticky="NSEW")
        self.distance.grid_remove()

        ## Text Instructions for the patrol
        self.infolink = InfoLink(self)
        self.infolink.grid(row=1, column=0, sticky="NSEW", columnspan=5)
        self.infolink.grid_remove()

        # buttons for the patrol
        self.prev = tk.Button(self, text="Prev", image=self.IMG_PREV, width=14, height=14, borderwidth=0)
        # self.submit=tk.Button(self, text="Open")
        self.next = tk.Button(self, text="Next", image=self.IMG_NEXT, width=14, height=14, borderwidth=0)
        self.prev.grid(row=0, column=1, sticky="W")

        # self.submit.grid(row = 2, column = 1,sticky="NSW")
        self.next.grid(row=0, column=4, sticky="E")
        self.next.bind('<Button-1>', self.patrol_next)
        self.prev.bind('<Button-1>', self.patrol_prev)

        self.prev.grid_remove()
        self.next.grid_remove()

        self.excluded = {}

        self.patrol_list = []
        self.capi_update = False
        self.patrol_count = 0
        self.patrol_pos = 0
        self.minutes = 0
        self.visible()
        self.cmdr = ""
        self.nearest = {}

        self.system = ""

        self.body = ""
        self.lat = ""
        self.lon = ""

        self.started = False

        # wait 10 seconds before updatinb the ui
        self.after(1000, self.update_ui)

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

    '''
    Every hour we will download the latest data
    '''

    def patrol_update(self):
        UpdateThread(self).start()
        self.after(CYCLE, self.patrol_update)

    def patrol_next(self, event):
        """
        When the user clicks next it will hide the current patrol for the duration of the session
        It does this by setting an excluded flag on the patrl list
        """
        # if it the last patrol lets not go any further.
        index = self.nearest.get("index")
        if index + 1 < len(self.patrol_list):
            debug("len {} ind {}".format(len(self.patrol_list), index))
            self.nearest["excluded"] = True
            self.patrol_list[index]["excluded"] = True
            self.update()
            if self.copypatrol == 1:
                copyclip(self.nearest.get("system"))
            # if there are excluded closer then we might need to deal with it
            # self.prev.grid()

    def patrol_prev(self, event):
        """
        When the user clicks next it will unhide the previous patrol
        It does this by unsetting the excluded flag on the previous patrol
        """
        index = self.nearest.get("index")
        debug("prev {}".format(index))
        if index > 0:
            self.patrol_list[index - 1]["excluded"] = False
            self.update()
            if self.copypatrol == 1:
                copyclip(self.nearest.get("system"))

    def update_ui(self):
        # rerun every 10 seconds
        self.after(1000, self.update_ui)
        self.update()

    def update(self):

        if self.visible():

            capi_update = self.patrol_list and self.system and self.capi_update
            journal_update = self.patrol_list and self.system

            if journal_update or capi_update:
                self.sort_patrol()
                p = Systems.edsmGetSystem(self.system)
                self.nearest = self.getNearest(p)
                self.hyperlink['text'] = self.nearest.get("system")
                self.hyperlink['url'] = "https://www.edsm.net/en/system?systemName={}".format(
                    quote_plus(self.nearest.get("system")))
                self.distance['text'] = "{}ly".format(
                    Locale.stringFromNumber(getDistance(p, self.nearest.get("coords")), 2))
                self.infolink['text'] = self.nearest.get("instructions")
                self.infolink['url'] = self.parseurl(self.nearest.get("url"))

                self.infolink.grid()
                self.distance.grid()
                self.prev.grid()
                self.next.grid()
                self.capi_update = False

            else:
                if self.system:
                    self.hyperlink['text'] = "Fetching patrols..."
                else:
                    self.hyperlink['text'] = "Waiting for location"
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
        d1 = datetime.strptime(bgs.get("updated_at"), '%Y-%m-%dT%H:%M:%S.%fZ')
        d2 = datetime.now()

        last_updated = (d2 - d1).days
        if last_updated == 0:
            update_text = ""
        elif last_updated == 1:
            update_text = ". Last updated 1 day ago"
        elif last_updated < 7:
            update_text = ". Last updated {} days ago".format(last_updated)
        elif last_updated > 6:
            update_text = ". Last updated {} days ago. Please jump into the system to update the stats".format(
                last_updated)

        # if  self.getStates("pending_states",bgs):
        # pstates=" Pending: {}".format(self.getStates("pending_states",bgs))
        # else:
        # pstates=""

        # debug(bgs)
        if target:
            retval = "Canonn Influence {}%{}{}".format(Locale.stringFromNumber(float(bgs.get("influence") * 100), 2),
                                                       states, update_text)
        if over:
            retval = "Canonn Influence {}%{} Check #mission_minor_faction on discord for instructions.{}".format(
                Locale.stringFromNumber(float(bgs.get("influence") * 100), 2), states, update_text)
        if under:
            retval = "Canonn Influence {}%{} Please complete missions for Canonn to increase our influence{}".format(
                Locale.stringFromNumber(float(bgs.get("influence") * 100), 2), states, update_text)

        debug("{}: {}".format(bgs.get("system_name"), retval))
        return retval

    def getBGSOveride(self):
        BGSOveride = []
        SystemsOvireden = []
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTqwb4MYDrfSuBzRRGpA3R1u0kzKzSPuPBudVukWm4_Ti9G9KPaW2hWdwxwOJ2vHybywVOb-O2-tTBH/pub?gid=0&single=true&output=tsv"  # Set your BGS override link(tsv)
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.reader(r.iter_lines(), delimiter='\t')
            next(reader)
            for row in reader:

                system, x, y, z, TINF, TFAC, Description = row
                instructions = Description.format(TFAC, TINF)
                SystemsOvireden = []

                if system != '':
                    try:
                        BGSOveride.append(
                            newPatrol("BGSO", system, (float(x), float(y), float(z)), instructions, None, None))
                        SystemsOvireden.append(system)
                    except:
                        error(
                            "patrol {},{},{},{},{},{},{},{}".format("BGSO", system, x, y, z, instructions, None, None))
                else:
                    error("Patrol contains blank lines")
                debug(BGSOveride)
        return BGSOveride, SystemsOvireden

    def getBGSPatrol(self, bgs, BGSOSys):
        x, y, z = Systems.edsmGetSystem(bgs.get("system_name"))
        if bgs.get("system_name") in BGSOSys:
            return
        else:
            return newPatrol("BGS", bgs.get("system_name"), (x, y, z), self.getBGSInstructions(bgs),
                             "https://elitebgs.app/system/{}".format(bgs.get("system_id")))

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
            r = url.replace('{CMDR}', self.cmdr)

            # We will need to initialise to "" if not

            if not self.lat:
                self.lat = ""
            if not self.lon:
                self.lon = ""
            if not self.body:
                self.body = ""

            r = r.replace('{LAT}', str(self.lat))
            r = r.replace('{LON}', str(self.lon))
            r = r.replace('{BODY}', self.body)

            return r
        else:
            return url


    def getJsonPatrol(self,url):
        canonnpatrol = []

        with closing(requests.get(url)) as r:
            reader = r.json()
            for row in reader:

                type = row.get("type")
                system = row.get("system")
                x=  row.get("x")
                y=  row.get("y")
                z = row.get("z")
                instructions = row.get("instructions")
                url = row.get("url")
                event = row.get("event")
                if system != '':
                    try:
                        canonnpatrol.append(
                            newPatrol(type, system, (float(x), float(y), float(z)), instructions, url, event))
                    except:
                        error("patrol {},{},{},{},{},{},{},{}".format(type, system, x, y, z, instructions, url, event))
                else:
                    error("Patrol contains blank lines")

        return canonnpatrol

    def getCanonnPatrol(self):
        canonnpatrol = []
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQgIlIQE8XMugQVchWr417uB9yvOcgn1ak0LGxwmNnGg2wjJudNXrntpppcH_KFR_xTuPsKPS6uBvSb/pub?gid=0&single=true&output=tsv"
        with closing(requests.get(url, stream=True)) as r:
            reader = csv.reader(r.iter_lines(), delimiter='\t')
            next(reader)
            for row in reader:

                type, system, x, y, z, instructions, url, event = row
                if system != '':
                    try:
                        canonnpatrol.append(
                            newPatrol(type, system, (float(x), float(y), float(z)), instructions, url, event))
                    except:
                        error("patrol {},{},{},{},{},{},{},{}".format(type, system, x, y, z, instructions, url, event))
                else:
                    error("Patrol contains blank lines")

        canonnpatrol = canonnpatrol+self.getJsonPatrol("https://us-central1-canonn-api-236217.cloudfunctions.net/codex_gap_patrol")
        canonnpatrol = canonnpatrol + self.getJsonPatrol("https://us-central1-canonn-api-236217.cloudfunctions.net/edsm_gap_patrol")
        return canonnpatrol

    def keyval(self, k):
        x, y, z = Systems.edsmGetSystem(self.system)
        return getDistance((x, y, z), k.get("coords"))

    def sort_patrol(self):
        patrol_list = sorted(self.patrol_list, key=self.keyval)

        for num, val in enumerate(patrol_list):
            system = val.get("system")
            type = val.get("type")

            patrol_list[num]["index"] = num

        self.patrol_list = patrol_list

    def download(self):
        debug("Download Patrol Data")

        # if patrol list is populated then was can save
        if self.patrol_list:
            self.save_excluded()
        else:
            self.load_excluded()

        # no point if we have no idea where we are
        if self.system:
            patrol_list = []
            if self.faction != 1:
                debug("Getting Faction Data")
                BGSO, BGSOSys = self.getBGSOveride()  # first variable- for patrol_list, second-for ignore existant systems
                patrol_list.extend(BGSO)

                patrol_list.extend(self.getFactionData("Canonn", BGSOSys))
                patrol_list.extend(self.getFactionData("Canonn Deep Space Research", BGSOSys))
                try:
                    patrol_list.remove(None)
                except:
                    debug("Nothing to delete")

            if self.ships and self.hideships != 1:
                patrol_list.extend(self.ships)

            if self.canonn != 1:
                self.canonnpatrol = self.getCanonnPatrol()
                patrol_list.extend(self.canonnpatrol)

            # add exclusions from configuration
            for num, val in enumerate(patrol_list):
                system = val.get("system")
                type = val.get("type")

                if self.excluded.get(type):
                    if self.excluded.get(type).get(system):
                        patrol_list[num]["excluded"] = self.excluded.get(type).get(system)

            # we will sort the patrol list
            self.patrol_list = patrol_list
            self.sort_patrol()

            debug("download done")

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        """Called to get a tk Frame for the settings dialog."""

        self.canonnbtn = tk.IntVar(value=config.getint("HideCanonn"))
        self.factionbtn = tk.IntVar(value=config.getint("HideFaction"))
        self.hideshipsbtn = tk.IntVar(value=config.getint("HideShips"))
        self.copypatrolbtn = tk.IntVar(value=config.getint("CopyPatrol"))

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.hideships = self.hideshipsbtn.get()
        self.copypatrol = self.copypatrolbtn.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Label(frame, text="Patrol Settings").grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Hide Canonn Patrols", variable=self.canonnbtn).grid(row=1, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Hide Canonn Faction Systems", variable=self.factionbtn).grid(row=1, column=2,
                                                                                                 sticky="NW")
        nb.Checkbutton(frame, text="Hide Your Ships", variable=self.hideshipsbtn).grid(row=1, column=3, sticky="NW")
        nb.Checkbutton(frame, text="Automatically copy the patrol to the clipboard", variable=self.copypatrolbtn).grid(
            row=2, column=0, sticky="NW", )

        debug("canonn: {}, faction: {} hideships {}".format(self.canonn, self.faction, self.hideships))

        return frame

    def visible(self):

        nopatrols = self.canonn == 1 and self.faction == 1 and self.hideships == 1

        if nopatrols:
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
            self.patrol_list[num]["index"] = int(num)

            if not patrol.get("excluded"):
                if nearest != "":

                    if getDistance(location, patrol.get("coords")) < getDistance(location, nearest.get("coords")):
                        nearest = patrol

                else:

                    nearest = patrol

        return nearest

    def prefs_changed(self, cmdr, is_beta):
        """Called when the user clicks OK on the settings dialog."""
        config.set('HideCanonn', self.canonnbtn.get())
        config.set('HideFaction', self.factionbtn.get())
        config.set('HideShips', self.hideshipsbtn.get())
        config.set('CopyPatrol', self.copypatrolbtn.get())

        self.canonn = self.canonnbtn.get()
        self.faction = self.factionbtn.get()
        self.hideships = self.hideshipsbtn.get()
        self.copypatrol = self.copypatrolbtn.get()

        if self.visible():
            # we should fire off an extra download
            UpdateThread(self).start()
            self.update_ui()

        debug("canonn: {}, faction: {} hideships {}".format(self.canonn, self.faction, self.hideships))

    def trigger(self, system, entry):
        # exit if the events dont match

        event = json.loads(self.nearest.get("event"))
        for key in event.keys():
            if event.get(key):
                if not entry.get(key).upper() == event.get(key).upper():
                    return False

        debug("triggered")
        # autosubmit the form -- allowing for google forms
        if self.nearest.get("url"):
            j = requests.get(self.nearest.get("url").replace('viewform', 'formResponse'))
        self.patrol_next(None)

    def journal_entry(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        # We don't care what the journal entry is as long as the system has changed.

        self.body = body
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.z = z

        if system and not self.started:
            debug("Patrol download cycle commencing")
            self.started = True
            self.patrol_update()

        if cmdr:
            self.cmdr = cmdr

        if self.system != system and entry.get("event") in ("Location", "FSDJump", "StartUp"):
            debug("Refresshing Patrol ({})".format(entry.get("event")))
            self.system = system
            self.update_ui()
            if self.nearest and self.copypatrol == 1:
                copyclip(self.nearest.get("system"))

        if body:
            self.update_ui()
        # else:
        # error("nope {}".format(entry.get("event")))
        # error(system)
        # error(self.system)

        # If we have visted a system and then jump out then lets clicknext
        if system and self.nearest:
            if self.nearest.get("system").upper() == system.upper() and entry.get("event") == "StartJump" and entry.get(
                    "JumpType") == "Hyperspace":
                self.patrol_next(None)

        # After we have done everything else let's see if we can automatically submit and move on
        if system and self.nearest.get("event") and self.nearest.get("system").upper() == system.upper():
            self.trigger(system, entry)

    def load_excluded(self):
        debug("loading excluded")
        self.patrol_config = os.path.join(Release.plugin_dir, 'data', 'EDMC-Canonn.patrol')
        try:
            with open(self.patrol_config) as json_file:
                self.excluded = json.load(json_file)
        except:
            debug("no config file {}".format(self.patrol_config))

    def save_excluded(self):
        self.patrol_config = os.path.join(Release.plugin_dir, 'data', 'EDMC-Canonn.patrol')
        excluded = {}
        for patrol in self.patrol_list:
            if patrol.get("excluded") and not patrol.get("type") in ('BGS', 'SHIPS'):
                if not excluded.get(patrol.get("type")):
                    excluded[patrol.get("type")] = {}
                excluded[patrol.get("type")][patrol.get("system")] = True

        with open(self.patrol_config, 'w+') as outfile:
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
        self.cmdr = data.get('commander').get('name')

        self.ships = []
        self.system = data.get("lastSystem").get("name")

        current_ship = data.get("commander").get("currentShipId")

        shipsystems = {}

        # debug(json.dumps(data.get("ships"),indent=4))

        for ship in data.get("ships").keys():

            if int(ship) != int(current_ship):
                ship_system = data.get("ships").get(ship).get("starsystem").get("name")
                if not shipsystems.get(ship_system):
                    debug("first: {}".format(ship_system))
                    shipsystems[ship_system] = []
                # else:
                #    debug("second: {}".format(ship_system))

                shipsystems[ship_system].append(data.get("ships").get(ship))
                # if ship_system == "Celaeno":
                #    debug(json.dumps(shipsystems[ship_system],indent=4))
            # else:
            # debug("skipping {}".format(ship))

        for system in shipsystems.keys():
            ship_pos = Systems.edsmGetSystem(system)
            ship_count = len(shipsystems.get(system))
            # if system == "Celaeno":
            #    debug(json.dumps(shipsystems.get(system),indent=4))
            if ship_count == 1:
                # debug(shipsystems.get(system))
                ship_type = getShipType(shipsystems.get(system)[0].get("name"))
                ship_name = shipsystems.get(system)[0].get("shipName")
                ship_station = shipsystems.get(system)[0].get("station").get("name")
                ship_info = "Your {}, {} is docked at {}".format(ship_type, ship_name, ship_station)
            elif ship_count == 2:

                if shipsystems.get(system)[0].get("station").get("name") == shipsystems.get(system)[1].get(
                        "station").get("name"):
                    ship_info = "Your {} ({}) and {} ({}) are docked at {}".format(
                        getShipType(shipsystems.get(system)[0].get("name")),
                        getShipType(shipsystems.get(system)[0].get("shipName")),
                        getShipType(shipsystems.get(system)[1].get("name")),
                        getShipType(shipsystems.get(system)[1].get("shipName")),
                        shipsystems.get(system)[0].get("station").get("name"))
                    debug(ship_info)
                else:

                    ship_info = "Your {} ({}) is docked at {} and your {} ({}) is docked at {}".format(
                        getShipType(shipsystems.get(system)[0].get("name")),
                        getShipType(shipsystems.get(system)[0].get("shipName")),
                        shipsystems.get(system)[1].get("station").get("name"),
                        getShipType(shipsystems.get(system)[1].get("name")),
                        getShipType(shipsystems.get(system)[1].get("shipName")),
                        shipsystems.get(system)[0].get("station").get("name"))
                    debug(ship_info)
            else:
                ship_info = "You have {} ships stored in this system".format(ship_count)
                debug(ship_info)

            self.ships.append(newPatrol("SHIPS", system, ship_pos, ship_info, None))

        self.capi_update = True
        if self.system and not self.started:
            debug("Patrol download cycle commencing")
            self.started = True
            self.patrol_update()


def copyclip(value):
    window = tk.Tk()
    window.withdraw()
    window.clipboard_clear()  # clear clipboard contents
    window.clipboard_append(value)
    window.destroy()


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
