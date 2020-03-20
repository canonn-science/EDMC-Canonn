# assume python3 and try python 2.7 if it fails
try:
    import tkinter as tk
except:
    import Tkinter as tk

import json
import myNotebook as nb
import requests
import sys

from canonn import clientreport
from canonn import codex
from canonn import factionkill
from canonn import fssreports
from canonn import hdreport
from canonn import journaldata
from canonn import materialReport
from canonn import news
from canonn import nhss
from canonn import patrol
from canonn import release
from canonn.debug import Debug
from canonn.debug import debug
from canonn.systems import Systems
from canonn.whitelist import whiteList
from config import config

this = sys.modules[__name__]

this.nearloc = {
    'Latitude': None,
    'Longitude': None,
    'Altitude': None,
    'Heading': None,
    'Time': None
}

myPlugin = "EDMC-Canonn"

this.SysFactionState = None  # variable for state of controling faction
this.SysFactionAllegiance = None  # variable for allegiance of controlling faction
this.DistFromStarLS = None  # take distance to star

this.version = "5.20.0"

this.client_version = "{}.{}".format(myPlugin, this.version)
this.body_name = None


def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)

    this.news.plugin_prefs(frame, cmdr, is_beta, 1)
    this.release.plugin_prefs(frame, cmdr, is_beta, 2)
    this.patrol.plugin_prefs(frame, cmdr, is_beta, 3)
    Debug.plugin_prefs(frame, this.client_version, 4)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta, 5)
    hdreport.HDInspector(frame, cmdr, is_beta, this.client_version, 6)

    return frame


def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    this.news.prefs_changed(cmdr, is_beta)
    this.release.prefs_changed(cmdr, is_beta)
    this.patrol.prefs_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)
    Debug.prefs_changed()


def plugin_start3(plugin_dir):
    """
    Load Template plugin into EDMC
    """
    return plugin_start(plugin_dir)


def plugin_start(plugin_dir):
    """
    Load Template plugin into EDMC
    """

    # print this.patrol
    release.Release.plugin_start(plugin_dir)
    Debug.setClient(this.client_version)
    patrol.CanonnPatrol.plugin_start(plugin_dir)
    codex.CodexTypes.plugin_start(plugin_dir)
    journaldata.plugin_start(plugin_dir)

    return 'Canonn'


def plugin_stop():
    """
    EDMC is closing
    """
    debug("Stopping the plugin")
    this.patrol.plugin_stop()


def plugin_app(parent):
    this.parent = parent
    # create a new frame as a containier for the status
    padx, pady = 10, 5  # formatting
    sticky = tk.EW + tk.N  # full width, stuck to the top
    anchor = tk.NW

    frame = this.frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)

    table = tk.Frame(frame)
    table.columnconfigure(1, weight=1)
    table.grid(sticky="NSEW")

    this.news = news.CanonnNews(table, 0)
    this.release = release.Release(table, this.version, 1)
    this.codexcontrol = codex.CodexTypes(table, 2)
    this.patrol = patrol.CanonnPatrol(table, 3)
    this.hyperdiction = hdreport.hyperdictionDetector.setup(table, 4)

    whitelist = whiteList(parent)
    whitelist.fetchData()

    return frame


def journal_entry(cmdr, is_beta, system, station, entry, state):
    # capture some stats when we launch not read for that yet
    # startup_stats(cmdr)
    if "SystemFaction" in entry:

        SystemFaction = entry.get("SystemFaction")
        debug(SystemFaction)
        try:
            this.SysFactionState = SystemFaction["FactionState"]
        except:
            this.SysFactionState = None
        debug("SysFaction's state is" + str(this.SysFactionState))

    if "SystemAllegiance" in entry:

        SystemAllegiance = entry.get("SystemAllegiance")
        debug(SystemAllegiance)
        try:
            this.SysFactionAllegiance = SystemAllegiance
        except:
            this.SysFactionAllegiance = None
        debug("SysFaction's allegiance is" + str(this.SysFactionAllegiance))

    if "DistFromStarLS" in entry:
        '''"DistFromStarLS":144.821411'''
        try:
            this.DistFromStarLS = entry.get("DistFromStarLS")
        except:
            this.DistFromStarLS = None
        debug("DistFromStarLS=" + str(this.DistFromStarLS))

    if entry.get("event") == "FSDJump":
        Systems.storeSystem(system, entry.get("StarPos"))
        this.DistFromStarLS = None

    if ('Body' in entry):
        this.body_name = entry['Body']

    if system:
        x, y, z = Systems.edsmGetSystem(system)
    else:
        x = None
        y = None
        z = None

    return journal_entry_wrapper(cmdr, is_beta, system, this.SysFactionState, this.SysFactionAllegiance,
                                 this.DistFromStarLS, station, entry,
                                 state, x, y, z, this.body_name, this.nearloc['Latitude'], this.nearloc['Longitude'],
                                 this.client_version)
    # Now Journal_entry_wrapper take additional variable this.SysFactionState, this.SysFactionAllegiance, and this.DistFromStarLS


# Detect journal events
def journal_entry_wrapper(cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, entry,
                          state, x, y, z, body,
                          lat, lon, client):
    factionkill.submit(cmdr, is_beta, system, station, entry, client)
    nhss.submit(cmdr, is_beta, system, station, entry, client)
    hdreport.submit(cmdr, is_beta, system, station, entry, client)
    codex.submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
    fssreports.submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
    journaldata.submit(cmdr, is_beta, system, station, entry, client, body, lat, lon)
    clientreport.submit(cmdr, is_beta, client, entry)
    this.patrol.journal_entry(cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client)
    this.codexcontrol.journal_entry(cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client)
    whiteList.journal_entry(cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client)
    materialReport.submit(cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, entry,
                          x, y, z, body, lat,
                          lon, client)
    codex.saaScan.journal_entry(cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client)


def dashboard_entry(cmdr, is_beta, entry):
    this.landed = entry['Flags'] & 1 << 1 and True or False
    this.SCmode = entry['Flags'] & 1 << 4 and True or False
    this.SRVmode = entry['Flags'] & 1 << 26 and True or False
    this.landed = this.landed or this.SRVmode
    # print "LatLon = {}".format(entry['Flags'] & 1<<21 and True or False)
    # print entry
    if (entry['Flags'] & 1 << 21 and True or False):
        if ('Latitude' in entry):
            this.nearloc['Latitude'] = entry['Latitude']
            this.nearloc['Longitude'] = entry['Longitude']
    else:
        this.nearloc['Latitude'] = None
        this.nearloc['Longitude'] = None

    if entry.get("BodyName"):
        this.body_name = entry.get("BodyName")
    else:
        this.body_name = None


def cmdr_data(data, is_beta):
    """
    We have new data on our commander
    """
    # debug(json.dumps(data,indent=4))
    this.patrol.cmdr_data(data, is_beta)
