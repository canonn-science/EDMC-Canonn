# assume python3 and try python 2.7 if it fails
try:
    import tkinter as tk
except:
    import Tkinter as tk

import json
import myNotebook as nb
import requests
import sys
import os
import time
import canonn
from canonn import clientreport
from canonn import codex
from canonn import factionkill
from canonn import fssreports
from canonn import hdreport
from canonn import news
from canonn import nhss
from canonn import patrol
from canonn import release
from canonn import organic_scanner
from canonn.release import ClientVersion
from canonn.release import Release
from canonn.player import Player
from canonn import extool
import canonn.target
import canonn.guardian
from canonn.debug import Debug
from canonn.debug import debug
from canonn.systems import Systems, journalGetSystem
from canonn.whitelist import whiteList
from config import config
from ttkHyperlinkLabel import HyperlinkLabel
import webbrowser

import logging
from config import appname
import plug

this = sys.modules[__name__]

plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f"{appname}.{plugin_name}")

# If the Logger has handlers then it was already set up by the core code, else
# it needs setting up here.
if not logger.hasHandlers():
    level = logging.INFO  # So logger.info(...) is equivalent to print()

    logger.setLevel(level)
    logger_channel = logging.StreamHandler()
    logger_formatter = logging.Formatter(
        f"%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d:%(funcName)s: %(message)s"
    )
    logger_formatter.default_time_format = "%Y-%m-%d %H:%M:%S"
    logger_formatter.default_msec_format = "%s.%03d"
    logger_channel.setFormatter(logger_formatter)
    logger.addHandler(logger_channel)

Debug.setLogger(logger)

this.nearloc = {
    "Latitude": None,
    "Longitude": None,
    "Altitude": None,
    "Heading": None,
    "Temperature": None,
    "Gravity": None,
    "Time": None,
}

this.SysFactionState = None  # variable for state of controling faction
this.SysFactionAllegiance = None  # variable for allegiance of controlling faction
this.DistFromStarLS = None  # take distance to star

this.version = ClientVersion.version()
this.client_version = ClientVersion.client()

Debug.logger.debug(this.client_version)

this.body_name = None
this.planet_radius = None


def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)

    this.news.plugin_prefs(frame, cmdr, is_beta, 0)
    this.release.plugin_prefs(frame, cmdr, is_beta, 1)
    this.patrol.plugin_prefs(frame, cmdr, is_beta, 2)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta, 3)
    # hdreport.HDInspector(frame, cmdr, is_beta, this.client_version, 4)
    Debug.plugin_prefs(frame, this.client_version, 5)
    capture.plugin_prefs(frame, cmdr, is_beta, 6)
    this.extool.plugin_prefs(frame, cmdr, is_beta, 7)
    return frame


def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    this.news.prefs_changed(cmdr, is_beta)
    this.release.prefs_changed(cmdr, is_beta)
    this.patrol.prefs_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)


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
    patrol.CanonnPatrol.plugin_start(plugin_dir)
    codex.CodexTypes.plugin_start(plugin_dir)
    capture.plugin_start(plugin_dir)
    extool.BearingDestination.plugin_start(plugin_dir)

    canonn.target.TargetDisplay.set_plugin_dir(plugin_dir)

    return plugin_name


def plugin_stop():
    """
    EDMC is closing
    """
    Debug.logger.debug("Stopping the plugin")
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
    # this.extoolcontrol = extool.extoolTypes()
    this.extool = extool.BearingDestination(table, 3)
    this.codexcontrol.setDestinationWidget(this.extool)
    this.patrol = patrol.CanonnPatrol(this.parent, table, 4)
    this.hyperdiction = hdreport.hyperdictionDetector.setup(table, 5)
    this.guestbook = guestBook.setup(table, 6)
    this.target = canonn.target.TargetDisplay(table, 7, this.codexcontrol)
    this.scan_organic = organic_scanner.OrganicScanner(table, 8)
    this.guardian = canonn.guardian.Display(table, 9)

    whitelist = whiteList(parent)
    whitelist.fetchData()

    return frame


def journal_entry(cmdr, is_beta, system, station, entry, state):
    if entry.get("StarSystem") and entry.get("StarPos"):
        Systems.storeSystem(entry.get("StarSystem"), entry.get("StarPos"))

    # we will cache some date from the latest journal because we will probably need it.
    if entry.get("event" == "LoadGame"):
        journalGetSystem()
    # navroute has some info that we can use in the event that system is null
    Systems.storeNavroute(state)
    Systems.storeId64(entry)

    # if system does not match the systemAddress in the event then
    # we need to set the correct system
    if system and entry.get("SystemAddress"):
        d = Systems.systemFromId64(entry.get("SystemAddress"))
        if d and system != d.get("StarSystem"):
            system = d.get("StarSystem")

    # we need to fix system if its not set.
    if system is None and entry.get("SystemAddress") is not None:
        d = Systems.systemFromId64(entry.get("SystemAddress"))
        if d:
            Debug.logger.debug(f"setting unknown system to {d}")
            system = d.get("StarSystem")
            x, y, z = Systems.edsmGetSystem(system)
        else:
            Debug.logger.debug("Can't locate system leaving it blank")

    if "SystemFaction" in entry:
        SystemFaction = entry.get("SystemFaction")
        Debug.logger.debug(SystemFaction)
        try:
            this.SysFactionState = SystemFaction["FactionState"]
        except:
            this.SysFactionState = None
        Debug.logger.debug("SysFaction's state is" + str(this.SysFactionState))

    if "SystemAllegiance" in entry:
        SystemAllegiance = entry.get("SystemAllegiance")
        Debug.logger.debug(SystemAllegiance)
        try:
            this.SysFactionAllegiance = SystemAllegiance
        except:
            this.SysFactionAllegiance = None
        Debug.logger.debug(
            "SysFaction's allegiance is" + str(this.SysFactionAllegiance)
        )

    if "DistFromStarLS" in entry:
        """ "DistFromStarLS":144.821411"""
        try:
            this.DistFromStarLS = entry.get("DistFromStarLS")
        except:
            this.DistFromStarLS = None
        Debug.logger.debug("DistFromStarLS=" + str(this.DistFromStarLS))

    if entry.get("event") == "FSDJump":
        Systems.storeSystem(system, entry.get("StarPos"))
        this.DistFromStarLS = None

    if entry.get("event") == "CarrierJump" and entry.get("StarSystem"):
        system = entry.get("StarSystem")
        Systems.storeSystem(system, entry.get("StarPos"))

    x = None
    y = None
    z = None

    if system and entry.get("StarPos") is None:
        try:
            x, y, z = Systems.edsmGetSystem(system)
        except:
            x = None
            y = None
            z = None

    if system and entry.get("StarPos"):
        x, y, z = entry.get("StarPos")

    ignorelist = [
        "LoadGame",
        "Statistics",
        "Friends",
        "ReceiveText",
        "FSSSignalDiscovered",
        "SquadronStartup",
        "FSDTarget",
    ]

    mismatch64 = entry.get("SystemAddress") and entry.get(
        "SystemAddress"
    ) != Systems.id64FromSystem(system)
    badsystem = system is None or system == "" or mismatch64

    if badsystem and not entry.get("event") in ignorelist:
        if system is None or system == "":
            # plug.show_error(f"Canonn: system is blank {entry.get('event')}")
            Debug.logger.error(f"Canonn: system is blank {entry.get('event')}")
        else:
            # plug.show_error(f"Canonn: id64 mismatch {entry.get('event')}")
            Debug.logger.error(f"Canonn: id64 mismatch {entry.get('event')}")
        Debug.logger.error(entry)

    if entry.get("event") == "SendText" and entry.get("Message") == "test nagging":
        Player(Release.plugin_dir, ["sounds\\prefixd.mp3", "sounds\\nag1d.mp3"]).start()

    return journal_entry_wrapper(
        cmdr,
        is_beta,
        system,
        this.SysFactionState,
        this.SysFactionAllegiance,
        this.DistFromStarLS,
        station,
        entry,
        state,
        x,
        y,
        z,
        this.body_name,
        this.nearloc,
        this.client_version,
    )

    # Now Journal_entry_wrapper take additional variable this.SysFactionState, this.SysFactionAllegiance, and this.DistFromStarLS


# Detect journal events
def journal_entry_wrapper(
    cmdr,
    is_beta,
    system,
    SysFactionState,
    SysFactionAllegiance,
    DistFromStarLS,
    station,
    entry,
    state,
    x,
    y,
    z,
    body,
    nearloc,
    client,
):
    canonn.debug.inject(
        cmdr,
        is_beta,
        system,
        SysFactionState,
        SysFactionAllegiance,
        DistFromStarLS,
        station,
        entry,
        state,
        x,
        y,
        z,
        body,
        nearloc,
        client,
        journal_entry_wrapper,
        this.frame,
    )
    clientreport.submit(cmdr, is_beta, client, entry)
    factionkill.submit(cmdr, is_beta, system, station, entry, client)
    nhss.submit(cmdr, is_beta, system, station, entry, client)

    codex.submit(
        cmdr,
        is_beta,
        system,
        x,
        y,
        z,
        entry,
        body,
        nearloc["Latitude"],
        nearloc["Longitude"],
        client,
        state,
    )
    fssreports.submit(
        cmdr,
        is_beta,
        system,
        x,
        y,
        z,
        entry,
        body,
        nearloc["Latitude"],
        nearloc["Longitude"],
        client,
        state,
    )
    this.patrol.journal_entry(
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
        nearloc["Latitude"],
        nearloc["Longitude"],
        client,
    )
    this.codexcontrol.journal_entry(
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
        nearloc["Latitude"],
        nearloc["Longitude"],
        client,
    )

    whiteList.journal_entry(
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
        nearloc["Latitude"],
        nearloc["Longitude"],
        client,
    )
    codex.saaScan.journal_entry(
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
        nearloc["Latitude"],
        nearloc["Longitude"],
        client,
    )
    codex.organicScan.journal_entry(
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
        nearloc["Latitude"],
        nearloc["Longitude"],
        nearloc["Temperature"],
        nearloc["Gravity"],
        client,
    )
    capture.journal_entry(
        cmdr,
        is_beta,
        system,
        SysFactionState,
        SysFactionAllegiance,
        DistFromStarLS,
        station,
        entry,
        state,
        x,
        y,
        z,
        body,
        nearloc["Latitude"],
        nearloc["Longitude"],
        client,
    )
    this.extool.journal_entry(cmdr, is_beta, system, entry, client)
    guestBook.journal_entry(entry)
    this.scan_organic.journal_entry(
        cmdr,
        is_beta,
        system,
        SysFactionState,
        SysFactionAllegiance,
        DistFromStarLS,
        station,
        entry,
        state,
        x,
        y,
        z,
        body,
        nearloc,
        client,
    )
    this.target.journal_entry(
        cmdr,
        is_beta,
        system,
        SysFactionState,
        SysFactionAllegiance,
        DistFromStarLS,
        station,
        entry,
        state,
        x,
        y,
        z,
        body,
        nearloc,
        client,
    )
    this.guardian.journal_entry(
        cmdr,
        is_beta,
        system,
        SysFactionState,
        SysFactionAllegiance,
        DistFromStarLS,
        station,
        entry,
        state,
        x,
        y,
        z,
        body,
        nearloc,
        client,
    )

    hdreport.submit(cmdr, is_beta, system, station, entry, client, state)


def dashboard_entry(cmdr, is_beta, entry):
    this.landed = False
    this.SCmode = False
    this.SRVmode = False
    this.FOOTmode = False
    if "Flags" in entry:
        this.landed = entry["Flags"] & 1 << 1 and True or False
        this.SCmode = entry["Flags"] & 1 << 4 and True or False
        this.SRVmode = entry["Flags"] & 1 << 26 and True or False
    if "Flags2" in entry:
        this.FOOTmode = entry["Flags2"] & 1 << 4 and True or False
    this.landed = this.landed or this.SRVmode or this.FOOTmode

    if "Latitude" in entry and "Longitude" in entry:
        this.nearloc["Latitude"] = entry.get("Latitude")
        this.nearloc["Longitude"] = entry.get("Longitude")
    else:
        this.nearloc["Latitude"] = None
        this.nearloc["Longitude"] = None

    if "Altitude" in entry:
        this.nearloc["Altitude"] = entry.get("Altitude")
    else:
        if this.landed:
            this.nearloc["Altitude"] = 0
        else:
            this.nearloc["Altitude"] = None

    if "Heading" in entry:
        this.nearloc["Heading"] = entry.get("Heading")
    else:
        this.nearloc["Heading"] = None

    if "Temperature" in entry:
        this.nearloc["Temperature"] = entry.get("Temperature")
    else:
        this.nearloc["Temperature"] = None

    if "Gravity" in entry:
        this.nearloc["Gravity"] = entry.get("Gravity")
    else:
        this.nearloc["Gravity"] = None

    if "BodyName" in entry:
        this.body_name = entry.get("BodyName")
    else:
        this.body_name = None
        this.planet_radius = None

    if "PlanetRadius" in entry:
        this.planet_radius = entry.get("PlanetRadius")

    if "timestamp" in entry:
        this.nearloc["Time"] = time.mktime(
            time.strptime(entry["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
        )
    else:
        this.nearloc["Time"] = None

    return dashboard_entry_wrapper(cmdr, is_beta, entry)


def dashboard_entry_wrapper(
    cmdr,
    is_beta,
    entry,
):
    this.codexcontrol.updatePlanetData(
        this.body_name,
        this.nearloc["Latitude"],
        this.nearloc["Longitude"],
        this.nearloc["Temperature"],
        this.nearloc["Gravity"],
    )

    this.extool.updatePosition(
        this.body_name,
        this.planet_radius,
        this.nearloc["Latitude"],
        this.nearloc["Longitude"],
        this.nearloc["Heading"],
    )
    this.scan_organic.updatePosition(this.body_name, this.planet_radius, this.nearloc)


def cmdr_data(data, is_beta):
    """
    We have new data on our commander
    """
    # Debug.logger.debug(json.dumps(data,indent=4))
    this.patrol.cmdr_data(data, is_beta)


class capture:
    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

    @classmethod
    def journal_entry(
        cls,
        cmdr,
        is_beta,
        system,
        SysFactionState,
        SysFactionAllegiance,
        DistFromStarLS,
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
        if entry.get("event") == "SendText":
            message_part = entry.get("Message").lower().split(" ")
            canonn_capture = len(message_part) > 1
            canonn_capture = canonn_capture and message_part[0] == "canonn"
            canonn_capture = canonn_capture and message_part[1] == "capture"

        if entry.get("event") == "SendText" and canonn_capture:
            structured_msg = (
                len(message_part) > 3
                and message_part[2]
                in (
                    "guardian",
                    "thargoid",
                    "human",
                    "biology",
                    "geology",
                    "other",
                    "nsp",
                )
                and message_part[3].isnumeric()
            )
            if structured_msg:
                site_type = message_part[2]
                site_index = message_part[3]
            else:
                site_type = None
                site_index = None

            # fetch status.json
            journal_dir = config.get_str("journaldir") or config.default_journal_dir
            with open(
                os.path.join(os.path.expanduser(journal_dir), "status.json")
            ) as json_file:
                status = json.load(json_file)

            if structured_msg:
                comment = " ".join(message_part[4:])
            else:
                comment = " ".join(message_part[2:])

            Debug.logger.debug(status)

            plug.show_error("Sending status to Canonn")

            canonn.emitter.post(
                "https://us-central1-canonn-api-236217.cloudfunctions.net/postStatus",
                {
                    "cmdr": cmdr,
                    "system": system,
                    "x": x,
                    "y": y,
                    "z": z,
                    "status": status,
                    "body": body,
                    "lat": status.get("Latitude"),
                    "lon": status.get("Longitude"),
                    "heading": status.get("Heading"),
                    "altitude": status.get("Altitude"),
                    "comment": comment,
                    "site_type": site_type,
                    "site_index": site_index,
                },
            )

    @classmethod
    def plugin_prefs(cls, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        cls.frame = nb.Frame(parent)
        cls.frame.columnconfigure(1, weight=1)
        cls.frame.grid(row=gridrow, column=0, sticky="NSEW")
        nb.Label(
            cls.frame,
            text=f"These followed in-game text command are used to save personnal POI :\ncanonn capture <type> <number> <comment>\ncanonn capture <comment>\n\t<type> = guardian, thargoid, human, biology, geology, other, nsp\n\t<number> = integer\n\t<comment> = string",
            justify=tk.LEFT,
            anchor="w",
        ).grid(row=0, column=0, sticky="NW")

        return cls.frame


class guestBook:
    state = 0
    target_system = ""

    @classmethod
    def hide(cls):
        cls.frame.grid_remove()

    @classmethod
    def show(cls):
        cls.frame.grid()
        # cls.frame.after(120000, cls.hide)

    @classmethod
    def visit_book(cls, event):
        url = "https://forms.gle/Qp1JDiz7ocqwbZRH9"
        webbrowser.open_new(url)
        cls.hide()

    @classmethod
    def setup(cls, parent, gridrow):
        cls.frame = tk.Frame(parent)
        cls.frame.grid(row=gridrow, sticky="NSEW")
        cls.container = tk.Frame(cls.frame)
        cls.container.columnconfigure(1, weight=1)
        cls.container.grid(row=0)
        # cls.banner = HyperlinkLabel(cls.container, text="Guest Book")
        # cls.banner["url"]="https://forms.gle/Qp1JDiz7ocqwbZRH9"
        # cls.banner.grid(row=0, column=0, columnspan=1, sticky="NSEW")
        # cls.banner.config(font=("Arial Black", 22))
        cls.instructions = tk.Label(
            cls.container,
            text="click here to sign the gnosis guest book",
            fg="blue",
            underline=True,
        )
        cls.instructions.grid(row=1, column=0, columnspan=1, sticky="NSEW")
        cls.instructions.config(font=("Arial Black", 8))
        cls.instructions.bind("<Button-1>", cls.visit_book)
        cls.visited = False

        cls.hide()
        # cls.show()
        return cls.frame

    @classmethod
    def journal_entry(cls, entry):
        if "The Gnosis" in str(entry) and not cls.visited:
            cls.visited = True
            cls.show()
