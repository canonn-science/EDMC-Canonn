# Try python3 before 2.7
try:
    import tkinter as tk
    from tkinter import Frame
    from urllib.parse import quote_plus
    from urllib.parse import unquote
except:
    import Tkinter as tk
    from Tkinter import Frame
    from urllib import quote_plus
    from urllib import unquote

import traceback
from operator import truediv
import canonn.emitter
import json
import math
import myNotebook as nb
import os
import re
import requests
import threading
import webbrowser
from theme import theme
from canonn.debug import Debug
from canonn.debug import debug, error

from config import config
from canonn.tooltip import CreateToolTip
from ttkHyperlinkLabel import HyperlinkLabel
from canonn.release import ClientVersion

import plug
from math import sqrt, pow
import queue
import re

from datetime import datetime


def is_timestamp_older(timestamp1, timestamp2):
    try:
        format_str = "%Y-%m-%d %H:%M:%S%z"
        if len(timestamp1) == len("2023-03-24 21:04:46+00"):
            timestamp1 = timestamp1 + "00"
        if len(timestamp2) == len("2023-03-24 21:04:46+00"):
            timestamp2 = timestamp2 + "00"
        signal = datetime.strptime(timestamp1, format_str)
        update = datetime.strptime(timestamp2, format_str)
    except Exception as e:
        Debug.logger.error(e)
        return False

    return signal < update


DWARFS = (
    "L (Brown dwarf) Star",
    "T (Brown dwarf) Star",
    "Y (Brown dwarf) Star",
    "L",
    "T",
    "Y",
)


def plugin_error(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            error_message = traceback.format_exc()
            Debug.logger.error(f"{func.__name__} had an error")
            Debug.logger.error(args)
            Debug.logger.error(e)
            self = args[0]
            try:
                self.add_poi("Other", "Plugin Error", args[3])
            except:
                self.add_poi("Other", "Plugin Error", None)
            canonn.emitter.post(
                "https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent/plugin/error",
                {
                    "system_name": self.system,
                    "function_name": func.__name__,
                    "clientVersion": ClientVersion.client(),
                    "error_text": error_message,
                },
            )

    return wrapper


# identify the genus


def get_genus(value):
    for type in CodexTypes.genus.values():
        if type in value:
            return type
    else:
        return "Unkown"


class Queue(queue.Queue):
    """
    A custom queue subclass that provides a :meth:`clear` method.
    """

    def clear(self):
        """
        Clears all items from the queue.
        """

        with self.mutex:
            unfinished = self.unfinished_tasks - len(self.queue)
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError("task_done() called too many times")
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished
            self.queue.clear()
            self.not_full.notify_all()


def nvl(a, b):
    return a or b


def get_parent(body):
    parents = body.get("parents")
    if parents:
        pd = parents[0]
        pl = list(pd.values())
        p = pl[0]
        return p


def get_null(body):
    parents = body.get("parents")
    if parents:
        p1 = parents[0]
        id = p1.get("Null")
        if not p1 == None:
            return p1
    return None


def isBinary(body):
    parents = body.get("parents")
    # find out if we are a binary
    if parents and parents[0].get("Null"):
        return True

    return False


def get_sibling(body, bodies):
    p1 = get_null(body)
    for candidate in bodies.values():
        p2 = get_null(candidate)
        if (
            not p2 == None
            and p2 == p1
            and body.get("bodyId") != candidate.get("bodyId")
        ):
            return candidate
    return None


def get_area(inner, outer):
    a1 = math.pi * pow(inner, 2)
    a2 = math.pi * pow(outer, 2)
    return a2 - a1


def hasRings(body):
    if body.get("rings") or body.get("belts"):
        rings = body.get("rings")
        if body.get("belts") and not rings:
            rings = body.get("belts")

        for ring in rings:
            if "Belt" not in ring.get("name"):
                return True
    return False


def get_density(mass, inner, outer):
    a = get_area(inner, outer)
    # print("{} {} {}".format(mass,inner,outer))
    # add a tiny number to force non zero
    if a > 0:
        density = mass / a
        # print(density)
    else:
        density = 0
    return density


def get_outer_radius(body):
    if body.get("rings") or body.get("belts"):
        rings = body.get("rings")
        if body.get("belts") and not rings:
            rings = body.get("belts")
    outer = None
    for ring in rings:
        if not outer or "Belt" not in ring.get("name"):
            if not outer:
                outer = ring.get("outerRadius")
            if ring.get("outerRadius") > outer:
                outer = ring.get("outerRadius")
    # convert to light seconds from km
    result = outer / 299792.458

    return result


def convert_materials(mats):
    retval = {}
    for material in mats:
        name = material.get("Name").capitalize()
        pct = material.get("Percent")
        retval[name] = pct
    return retval


# This function will return a body in edsm format


def journal2edsm(j):
    # Debug.logger.debug(json.dumps(j, indent=4))

    def convertAtmosphere(a):
        r = {}
        for elem in a:
            r[elem.get("Name")] = round(elem.get("Percent"), 2)

        return r

    e = {}
    if j.get("OrbitalPeriod"):
        e["orbitalPeriod"] = j.get("OrbitalPeriod") / 24 / 60 / 60

    e["surfaceTemperature"] = int(j.get("SurfaceTemperature"))
    e["distanceToArrival"] = int(round(j.get("DistanceFromArrivalLS"), 0))
    e["bodyId"] = j.get("BodyID")
    e["parents"] = j.get("Parents")
    e["axialTilt"] = j.get("AxialTilt")
    if j.get("StarType"):
        e["subType"] = j.get("StarType")
        e["type"] = "Star"
        e["spectralClass"] = "{}{}".format(j.get("StarType"), j.get("Subclass"))
        e["absoluteMagnitude"] = j.get("AbsoluteMagnitude")
        e["solarMasses"] = j.get("StellarMass")
        e["solarRadius"] = j.get("Radius") / 695500000
        e["luminosity"] = j.get("Luminosity")
        e["age"] = j.get("Age_MY")
    else:
        e["type"] = "Planet"
        e["radius"] = j.get("Radius") / 1000
        e["subType"] = j.get("PlanetClass")
        e["gravity"] = j.get("SurfaceGravity") / 9.798064999864019
        e["isLandable"] = j.get("Landable")
        if j.get("AtmosphereComposition"):
            e["atmosphereComposition"] = convertAtmosphere(
                j.get("AtmosphereComposition")
            )
        if j.get("Atmosphere") != "":
            e["atmosphereType"] = j.get("Atmosphere").title()
        else:
            e["atmosphereType"] = "No atmosphere"
        if j.get("TerraformState") == "Terraformable":
            e["terraformingState"] = "Terraformable"
        elif j.get("TerraformState") == "Terraforming":
            e["terraformingState"] = "Terraforming"
        else:
            e["terraformingState"] = "Not terraformable"
        if j.get("Volcanism") == "":
            e["volcanismType"] = "No volcanism"
        else:
            e["volcanismType"] = j.get("Volcanism").title()

        e["rotationalPeriod"] = j.get("RotationalPeriod")
        e["solidComposition"] = j.get("SolidComposition")
        e["earthMasses"] = j.get("MassEM")
        e["surfacePressure"] = j.get("SurfacePressure")

    e["orbitalInclination"] = j.get("OrbitalInclination")
    e["rotationalPeriod"] = j.get("RotationPeriod") / 24 / 60 / 60
    e["argOfPeriapsis"] = j.get("Periapsis")
    e["orbitalEccentricity"] = j.get("Eccentricity")
    e["meanAnomaly"] = j.get("MeanAnomaly")
    e["updateTime"] = j.get("timestamp")
    e["rotationalPeriodTidallyLocked"] = j.get("TidalLock") or False
    e["name"] = j.get("BodyName")
    if j.get("Rings"):
        e["rings"] = []
        for ring in j.get("Rings"):
            e["rings"].append(
                {
                    "name": ring.get("Name"),
                    "type": ring.get("RingClass")
                    .replace("eRingClass_", "")
                    .replace("MetalRich", "Metal Rich"),
                    "mass": float(ring.get("MassMT")),
                    "innerRadius": float(ring.get("InnerRad")) / 1000,
                    "outerRadius": float(ring.get("OuterRad")) / 1000,
                }
            )
    if j.get("SemiMajorAxis"):
        e["semiMajorAxis"] = j.get("SemiMajorAxis") / 149597870700
    if j.get("ReserveLevel"):
        e["reserveLevel"] = j.get("ReserveLevel")
    if j.get("Materials"):
        e["materials"] = convert_materials(j.get("Materials"))

    return e


def surface_pressure(tag, value):
    if tag == "surfacePressure":
        return value * 100000
    else:
        return value


def get_synodic_period(b1, b2):
    T1 = b1.get("orbitalPeriod")
    T2 = b2.get("orbitalPeriod")
    # make sure we dont divide by zero.
    if T1 == T2 or abs((1 / T1) - (1 / T2)) or T1 + T2 == 0:
        return 9999999999
    Tsyn = 1 / abs((1 / T1) - (1 / T2))
    return Tsyn


class codexName(threading.Thread):
    def __init__(self, callback):
        Debug.logger.debug("initialise codexName Thread")
        threading.Thread.__init__(self)
        self.callback = callback

    def run(self):
        self.callback()


class poiTypes(threading.Thread):
    def __init__(self, system, system64, cmdr, callback):
        # debug("initialise POITYpes Thread")
        threading.Thread.__init__(self)
        self.system = system
        self.system64 = system64
        self.cmdr = cmdr
        self.callback = callback

    def run(self):
        # debug("running poitypes")
        self.callback(self.system, self.system64, self.cmdr)
        # debug("poitypes Callback Complete")


# class planetTypes(threading.Thread):
#    def __init__(self, system, body, cmdr, callback):
#        # debug("initialise POITYpes Thread")
#        threading.Thread.__init__(self)
#        self.system = system
#        self.body = body
#        self.cmdr = cmdr
#        self.callback = callback
#
#    def run(self):
#        # debug("running poitypes")
#        self.callback(self.system, self.body, self.cmdr)
#        # debug("poitypes Callback Complete")


class saaScan:
    def __init__(self):
        Debug.logger.debug("We only use class methods here")

    @classmethod
    def journal_entry(
        cls,
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
        if entry.get("event") == "SAASignalsFound":
            canonn.emitter.post(
                "https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent",
                {
                    "gameState": {
                        "systemName": system,
                        "systemCoordinates": [x, y, z],
                        "bodyName": body,
                        "clientVersion": client,
                        "isBeta": is_beta,
                        "platform": "PC",
                        "odyssey": state.get("Odyssey"),
                    },
                    "rawEvent": entry,
                    "eventType": entry.get("event"),
                    "cmdrName": cmdr,
                },
            )


class organicScan:
    def __init__(self):
        Debug.logger.debug("We only use class methods here")

    @classmethod
    def journal_entry(
        cls,
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
        latitude,
        longitude,
        temperature,
        gravity,
        client,
    ):
        if entry.get("event") in ("ScanOrganic", "SellOrganicData"):
            canonn.emitter.post(
                "https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent",
                {
                    "gameState": {
                        "systemName": system,
                        "systemCoordinates": [x, y, z],
                        "bodyName": body,
                        "clientVersion": client,
                        "isBeta": is_beta,
                        "platform": "PC",
                        "odyssey": state.get("Odyssey"),
                        "latitude": latitude,
                        "longitude": longitude,
                        "temperature": temperature,
                        "gravity": gravity,
                    },
                    "rawEvent": entry,
                    "eventType": entry.get("event"),
                    "cmdrName": cmdr,
                },
            )


class CodexTypes:
    tooltips = {
        "MissingData": "Missing data in DB",
        "Geology": "Geology: Vents and fumeroles",
        "Cloud": "Lagrange Clouds",
        "Anomaly": "Anomalous stellar phenomena",
        "Thargoid": "Thargoid sites or barnacles",
        "Biology": "Biological surface signals",
        "Guardian": "Guardian sites",
        "None": "Unclassified codex entry",
        "Human": "Human Sites",
        "Ring": "Planetary Ring Resources",
        "Other": "Other Sites",
        "Personal": "Personal Sites",
        "Planets": "Valuable Planets",
        "Tourist": "Tourist Informatiom",
        "Jumponium": "Jumponium Planets",
        "GreenSystem": "Jumponium Planets",
    }

    canonndata = {
        "apsites": ["Biology", "Amphora Plants"],
        "bmsites": ["Biology", "Bark Mounds"],
        "btsites": ["Biology", "Brain Trees"],
        "cssites": ["Biology", "Crystalline Shards"],
        "fgsites": ["Biology", "Fungal Gourds"],
        "fmsites": ["Geology", "Fumaroles"],
        "gbsites": ["Guardian", "Guardian Beacons"],
        "gensites": ["Human", "Generation Ships"],
        "grsites": ["Guardian", "Guardian Ruins"],
        "gssites": ["Guardian", "Guardian Structures"],
        "gvsites": ["Geology", "Gas Vents"],
        "gysites": ["Geology", "Geysers"],
        "lssites": ["Geology", "Lava Spouts"],
        "tbsites": ["Thargoid", "Thargoid Barnacles"],
        "tssites": ["Thargoid", "Thargoid Structures"],
        "twsites": ["Biology", "Tube Worms"],
    }

    # these are high value body types used for Tourist Spots
    # no longer using for High Value Planet POIs
    hv_body_types = {
        "Metal-rich body": "Metal-Rich Body",
        "Metal rich body": "Metal-Rich Body",
        "Earth-like world": "Earthlike World",
        "Earthlike body": "Earthlike World",
        "Water world": "Water World",
        "Ammonia world": "Ammonia World",
    }

    # Translate all body types to human readable
    body_types = {
        "Class IV gas giant": "Class IV Gas Giant",
        "Sudarsky class IV gas giant": "Class IV Gas Giant",
        "Earth-like world": "Earthlike World",
        "Earthlike body": "Earthlike World",
        "High metal content body": "High Metal Content World",
        "High metal content world": "High Metal Content World",
        "Class II gas giant": "Class II Gas Giant",
        "Sudarsky class II gas giant": "Class II Gas Giant",
        "Water world": "Water World",
        "Class III gas giant": "Class III Gas Giant",
        "Sudarsky class III gas giant": "Class III Gas Giant",
        "Gas giant with ammonia-based life": "Gas Giant With Ammonia Based Life",
        "Gas giant with ammonia based life": "Gas Giant With Ammonia Based Life",
        "Ammonia world": "Ammonia World",
        "Rocky body": "Rocky Body",
        "Water giant": "Water Giant",
        "Gas giant with water-based life": "Gas Giant With Water Based Life",
        "Gas giant with water based life": "Gas Giant With Water Based Life",
        "Class I gas giant": "Class I Gas Giant",
        "Sudarsky class I gas giant": "Class I Gas Giant",
        "Icy body": "Icy Body",
        "Class V gas giant": "Class V Gas Giant",
        "Sudarsky class V gas giant": "Class V Gas Giant",
        "Helium gas giant": "Helium Gas Giant",
        "Rocky Ice world": "Rocky Ice World",
        "Rocky ice body": "Rocky Ice World",
        "Helium-rich gas giant": "Helium Rich Gas Giant",
        "Helium rich gas giant": "Helium Rich Gas Giant",
        "Metal-rich body": "Metal Rich Body",
        "Metal rich body": "Metal Rich Body",
        "Unknown": "Unknown",
    }

    economies = {
        "$economy_None;": "None",
        "$economy_Agri;": "Agriculture",
        "$economy_Refinery;": "Refinery",
        "$economy_Industrial;": "Industrial",
        "$economy_Colony;": "Colony",
        "$economy_Extraction;": "Extraction",
        "$economy_HighTech;": "High Tech",
        "$economy_Military;": "Military",
        "$economy_Terraforming;": "Terraforming",
        "$economy_Service;": "Service",
        "$economy_Tourism;": "Tourism",
        "$economy_Undefined;": "Undefined",
        "$economy_Damaged;": "Damaged",
        "$economy_Repair;": "Repair",
        "$economy_Prison;": "Prison",
        "$economy_Rescue;": "Rescue",
        "$economy_Carrier;": "Private Enterprise",
        "$economy_Engineer;": "Engineering",
    }

    genus = {
        "$Codex_Ent_Aleoids_Genus_Name;": "Aleoida",
        "$Codex_Ent_Bacterial_Genus_Name;": "Bacterium",
        "$Codex_Ent_Brancae_Name;": "Brain Tree",
        "$Codex_Ent_Cactoid_Genus_Name;": "Cactoida",
        "$Codex_Ent_Clepeus_Genus_Name;": "Clypeus",
        "$Codex_Ent_Clypeus_Genus_Name;": "Clypeus",
        "$Codex_Ent_Conchas_Genus_Name;": "Concha",
        "$Codex_Ent_Cone_Name;": "Bark Mounds",
        "$Codex_Ent_Electricae_Genus_Name;": "Electricae",
        "$Codex_Ent_Fonticulus_Genus_Name;": "Fonticulua",
        "$Codex_Ent_Fumerolas_Genus_Name;": "Fumerola",
        "$Codex_Ent_Fungoids_Genus_Name;": "Fungoida",
        "$Codex_Ent_Ground_Struct_Ice_Name;": "Crystalline Shards",
        "$Codex_Ent_Osseus_Genus_Name;": "Osseus",
        "$Codex_Ent_Recepta_Genus_Name;": "Recepta",
        "$Codex_Ent_Seed_Name;": "Brain Trees",
        "$Codex_Ent_Shrubs_Genus_Name;": "Frutexa",
        "$Codex_Ent_Sphere_Name;": "Anemone",
        "$Codex_Ent_Stratum_Genus_Name;": "Stratum",
        "$Codex_Ent_Tube_Name;": "Sinuous Tubers",
        "$Codex_Ent_Tubus_Genus_Name;": "Tubus",
        "$Codex_Ent_Tussocks_Genus_Name;": "Tussock",
        "$Codex_Ent_Vents_Name;": "Amphora Plant",
    }

    odyssey_bio = [
        "Aleoida",
        "Bacterium",
        "Cactoida",
        "Clypeus",
        "Concha",
        "Electricae",
        "Fonticulua",
        "Frutexa",
        "Fumerola",
        "Fungoida",
        "Osseus",
        "Recepta",
        "Stratum",
        "Tubus",
        "Tussock",
    ]

    horizon_bio = [
        "Brain Tree",
        "Sinuous Tubers",
        "Amphora Plant",
        "Crystalline Shards",
        "Anemone",
        "Bark Mounds",
    ]

    bodycount = 0

    parentRadius = 0
    minPressure = 80

    close_orbit = 0.02
    eccentricity = 0.9

    intaxi = False
    waitingPOI = True
    waitingPlanet = True
    fsscount = 0
    fccount = 0

    logqueue = True
    logq = Queue()

    spansh_bodyq = Queue()
    edsm_stationq = Queue()
    poiq = Queue()
    saaq = Queue()
    cmdrq = Queue()
    planetq = Queue()
    canonnq = Queue()
    raw_mats = None

    def __init__(self, parent, gridrow):
        "Initialise the ``Patrol``."
        # Frame.__init__(
        #    self,
        #   parent
        # )
        self.parent = parent
        self.hidecodexbtn = tk.IntVar(value=config.get_int("CanonnHideCodex"))
        self.hidecodex = self.hidecodexbtn.get()
        self.hidehumandetailedbtn = tk.IntVar(
            value=config.get_int("CanonnHideHumanDetailed")
        )
        self.hidehumandetailed = self.hidehumandetailedbtn.get()
        self.hidemissingdatabtn = tk.IntVar(
            value=config.get_int("CanonnHideMissingData")
        )
        self.hidemissingdata = self.hidemissingdatabtn.get()

        self.frame = Frame(parent)
        theme.update(self.frame)
        self.frame.columnconfigure(0, weight=1)
        self.frame.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)
        self.frame.bind("<<refreshPOIData>>", self.refreshPOIData)
        # self.frame.bind('<<refreshPlanetData>>', self.refreshPlanetData)

        self.container = Frame(self.frame, highlightthickness=1)
        self.container.grid(row=0, column=0, sticky="NSEW", columnspan=2)
        self.container.grid_remove()

        self.titlepanel = Frame(self.container)
        self.titlepanel.grid(row=1, column=0, sticky="NSEW")

        self.systempanel = Frame(self.container)
        self.systempanel.grid(row=2, column=0, sticky="NSEW")
        self.systempanel.grid_remove()

        self.systemtitle = Frame(self.titlepanel)
        self.systemtitle.grid(row=0, column=0, sticky="NSEW")
        self.systemtitle.grid_remove()
        self.systemtitle_name = HyperlinkLabel(
            self.container, text="?", url=None
        )  # moved to container
        self.systemtitle_name.grid(row=0, column=0, sticky="W")
        # self.systemprogress = tk.Label(self.systemtitle, text="?")
        self.systemprogress = tk.Label(self.container, text="?")
        self.systemprogress.grid(row=0, column=1, sticky="W")  # moved to next row
        self.systemprogress.grid_remove()

        self.planetpanel = Frame(self.container)
        self.planetpanel.grid(row=3, column=0, sticky="NSEW")
        self.planetpanel.grid_remove()

        self.planettitle = Frame(self.titlepanel)
        self.planettitle.grid(row=1, column=0, sticky="NSEW")
        self.planettitle.grid_remove()

        self.images_prev = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "left_arrow.gif")
        )
        self.planettitle_prev = tk.Label(
            self.planettitle, image=self.images_prev, cursor="hand2"
        )
        self.planettitle_prev.grid(row=0, column=0, sticky="NSEW")
        self.planettitle_prev.bind(
            "<Button-1>", lambda event, x=-1: self.changeBodyFocus(event, x)
        )
        self.images_next = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "right_arrow.gif")
        )
        self.planettitle_next = tk.Label(
            self.planettitle, image=self.images_next, cursor="hand2"
        )
        self.planettitle_next.grid(row=0, column=1, sticky="NSEW")
        self.planettitle_next.bind(
            "<Button-1>", lambda event, x=1: self.changeBodyFocus(event, x)
        )
        self.planettitle_name = tk.Label(self.planettitle, text="?")
        self.planettitle_name.grid(row=0, column=2, sticky="NSEW")
        self.planetprogress = tk.Label(self.planettitle, text="?")
        self.planetprogress.grid(row=0, column=3, sticky="NSEW")
        self.planetprogress.grid_remove()

        self.system64 = 0
        self.images = {}
        self.labels = {}
        self.systemlist = {}
        self.systemcol1 = []
        self.systemcol2 = []
        self.planetlist = {}
        self.planetcol1 = []
        self.planetcol2 = []
        self.stationdata = {}
        self.settlementdata = {}
        self.poidata = {}
        self.ppoidata = {}
        self.scandata = {}
        self.saadata = {}
        self.fssdata = {}
        self.organicscan = {}
        self.nfss = 0
        self.fccount = 0
        # self.stationPlanetData = {}

        self.temp_poidata = None
        self.temp_spanshdata = None

        # self.cmdrData = {}

        self.images_body = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "planet.gif")
        )
        self.images_body_auto = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "system_planet.gif")
        )
        self.images_body_grey = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "system.gif")
        )
        self.icon_body = tk.Label(
            self.systemtitle, image=self.images_body_auto, text="Body_auto"
        )
        self.icon_body.grid(row=0, column=1)
        self.icon_body.bind("<Button-1>", self.nextBodyMode)
        # self.icon_body.grid_remove()

        self.types = (
            "MissingData",
            "Geology",
            "Cloud",
            "Anomaly",
            "Thargoid",
            "Biology",
            "Guardian",
            "Human",
            "Ring",
            "None",
            "Other",
            "Personal",
            "Planets",
            "Tourist",
            "Jumponium",
            "GreenSystem",
        )
        k = 0
        for category in self.types:
            self.addimage(category, k + 3)
            self.systemlist[category] = Frame(self.systempanel)
            self.systemlist[category].grid(row=k + 1, column=0, sticky="W")
            self.systemlist[category].grid_remove()
            k += 1

        self.typesPlanet = (
            "Geology",
            "Thargoid",
            "Biology",
            "Guardian",
            "Human",
            "Other",
            "Personal",
            "Tourist",
            "Jumponium",
        )
        k = 0
        for category in self.typesPlanet:
            self.addimage_planet(category, k + 4)
            self.planetlist[category] = Frame(self.planetpanel)
            self.planetlist[category].grid(row=k + 1, column=0, sticky="W")
            self.planetlist[category].grid_remove()
            k += 1

        self.odyssey = False

        self.event = None
        self.system = None
        self.bodies = None
        self.body = None
        self.latitude = None
        self.longitude = None
        self.temperature = None
        self.gravity = None
        self.allowed = False
        self.lock = []
        self.lockPlanet = []

        self.planetlist_body = None
        self.planetlist_show = False
        self.planetlist_auto = True
        # self.systemprogress.grid_remove()

    def nextBodyMode(self, event):
        # Debug.logger.debug(f"nextBodyMode {self.event}")
        if self.icon_body["text"] == "Body":
            self.switchBodyMode("Body_auto")
        elif self.icon_body["text"] == "Body_auto":
            self.switchBodyMode("Body_grey")
        elif self.icon_body["text"] == "Body_grey":
            if len(self.ppoidata) != 0:
                self.switchBodyMode("Body")
            else:
                self.switchBodyMode("Body_auto")

    def switchBodyMode(self, mode):
        # Debug.logger.debug(f"switchBodyMode {mode}")
        if mode == "Body":
            self.planetlist_auto = False
            self.planetlist_show = True
            if self.planetlist_body is None:
                self.planetlist_body = next(iter(self.ppoidata))
            self.icon_body["image"] = self.images_body
            self.icon_body["text"] = "Body"
        elif mode == "Body_auto":
            self.planetlist_auto = True
            self.planetlist_show = False
            self.icon_body["image"] = self.images_body_auto
            self.icon_body["text"] = "Body_auto"
        elif mode == "Body_grey":
            self.planetlist_auto = False
            self.planetlist_show = False
            self.planetlist_body = None
            self.icon_body["image"] = self.images_body_grey
            self.icon_body["text"] = "Body_grey"
        self.visualisePlanetData()

    def setDestinationWidget(self, widget):
        self.dest_widget = widget

    def changeBodyFocus(self, event, inext):
        # next or prev body to ffocus when using green arrow
        body_list = []
        for body in self.ppoidata:
            body_list.append(body)

        body_list = sorted(body_list)
        k = 0
        for body in body_list:
            if self.planetlist_body == body:
                k_selected = k
            k += 1

        if inext == -1:
            if k_selected - 1 < 0:
                self.planetlist_body = body_list[len(body_list) - 1]
            else:
                self.planetlist_body = body_list[k_selected - 1]
        elif inext == 1:
            if k_selected + 1 > len(body_list) - 1:
                self.planetlist_body = body_list[0]
            else:
                self.planetlist_body = body_list[k_selected + 1]

        self.switchBodyMode("Body")
        self.visualisePlanetData()

    def bodyFocus(self, body):
        self.planetlist_body = body
        self.switchBodyMode("Body")
        tmplock = self.lock.copy()
        for category in tmplock:
            self.switchPOI(category)
            self.switchPlanet(category)
        self.visualisePlanetData()

    def activateDestination(self, latlon):
        lat = float(latlon.split(",")[0][1:])
        lon = float(latlon.split(",")[1][:-1])
        self.dest_widget.ActivateTarget(lat, lon)

    def switchPOI(self, category):
        if category in self.types:
            if category in self.lock:
                self.lock.remove(category)
                self.systemlist[category].grid_remove()
                self.labels[category]["image"] = self.images["{}_grey".format(category)]
                if len(self.lock) == 0:
                    self.systempanel.grid_remove()
            else:
                self.lock.append(category)
                self.systemlist[category].grid()
                self.labels[category]["image"] = self.images[category]
        else:
            if category in self.lock:
                self.lock.remove(category)
            else:
                self.lock.append(category)

    def switchPlanet(self, category):
        if category in self.typesPlanet:
            if category in self.lockPlanet:
                self.lockPlanet.remove(category)
                self.planetlist[category].grid_remove()
                self.labels[category + "_planet"]["image"] = self.images[
                    "{}_grey_planet".format(category)
                ]
                remove_panel = True
                if self.planetlist_body in self.ppoidata:
                    for c in self.ppoidata[self.planetlist_body]:
                        if c in self.lockPlanet:
                            remove_panel = False
                if remove_panel:
                    self.planetpanel.grid_remove()
            else:
                self.lockPlanet.append(category)
                self.planetlist[category].grid()
                self.labels[category + "_planet"]["image"] = self.images[
                    category + "_planet"
                ]
        else:
            if category in self.lockPlanet:
                self.lockPlanet.remove(category)
            else:
                self.lockPlanet.append(category)

    def lockPOIData(self, name):
        if name not in self.lock:
            self.switchPOI(name)
            self.systempanel.grid()
            self.planetpanel.grid_remove()
            for category in self.typesPlanet:
                if category in self.lockPlanet:
                    self.switchPlanet(category)
            if name != "MissingData":
                if self.planetlist_auto and self.planetlist_show:
                    self.switchBodyMode("Body")
        else:
            self.switchPOI(name)
        # self.visualisePOIData()

    def lockPlanetData(self, name):
        if name not in self.lockPlanet:
            self.switchPlanet(name)
            self.planetpanel.grid()
            self.systempanel.grid_remove()
            for category in self.types:
                if category in self.lock:
                    self.switchPOI(category)
        else:
            self.switchPlanet(name)
        # self.visualisePlanetData()

    def enter(self, event):
        name = event.widget["text"]
        if name[len(name) - 7 :] == "_planet":
            name = name[: len(name) - 7]
            if name not in self.lockPlanet:
                self.labels[name + "_planet"]["image"] = self.images[name + "_planet"]
                self.planetlist[name].grid()
                self.planetpanel.grid()
                self.systempanel.grid_remove()
        else:
            if name not in self.lock:
                self.labels[name]["image"] = self.images[name]
                self.systemlist[name].grid()
                self.systempanel.grid()
                self.planetpanel.grid_remove()

    def leave(self, event):
        name = event.widget["text"]
        if name[len(name) - 7 :] == "_planet":
            name = name[: len(name) - 7]
            if name not in self.lockPlanet:
                self.labels[name + "_planet"]["image"] = self.images[
                    "{}_grey_planet".format(name)
                ]
                self.planetlist[name].grid_remove()
                remove_panel = True
                if self.planetlist_body in self.ppoidata:
                    for category in self.ppoidata[self.planetlist_body]:
                        if category in self.lockPlanet:
                            remove_panel = False
                if remove_panel:
                    self.planetpanel.grid_remove()
                if len(self.lock) != 0:
                    remove_panel = True
                    for category in self.poidata:
                        if category in self.lock:
                            remove_panel = False
                    if not remove_panel:
                        self.systempanel.grid()

        else:
            if name not in self.lock:
                self.labels[name]["image"] = self.images["{}_grey".format(name)]
                self.systemlist[name].grid_remove()
                remove_panel = True
                for category in self.poidata:
                    if category in self.lock:
                        remove_panel = False
                if remove_panel:
                    self.systempanel.grid_remove()
                if len(self.lockPlanet) != 0:
                    remove_panel = True
                    if self.planetlist_body in self.ppoidata:
                        for category in self.ppoidata[self.planetlist_body]:
                            if category in self.lockPlanet:
                                remove_panel = False
                    if not remove_panel:
                        self.planetpanel.grid()

    def addimage(self, name, col):
        grey = "{}_grey".format(name)
        self.images[name] = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(name))
        )
        self.images[grey] = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(grey))
        )
        self.labels[name] = tk.Label(
            self.systemtitle, image=self.images.get(grey), text=name
        )
        self.labels[name].grid(row=0, column=col)
        self.labels[name].grid_remove()
        self.labels[name].bind("<Enter>", self.enter)
        self.labels[name].bind("<Leave>", self.leave)
        self.labels[name].bind("<Button-1>", lambda event, x=name: self.lockPOIData(x))
        self.labels[name]["image"] = self.images[name]

    def addimage_planet(self, name, col):
        grey = "{}_grey".format(name)
        self.images[name + "_planet"] = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(name))
        )
        self.images[grey + "_planet"] = tk.PhotoImage(
            file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(grey))
        )
        self.labels[name + "_planet"] = tk.Label(
            self.planettitle,
            image=self.images.get(grey + "_planet"),
            text=name + "_planet",
        )
        self.labels[name + "_planet"].grid(row=0, column=col)
        self.labels[name + "_planet"].grid_remove()
        self.labels[name + "_planet"].bind("<Enter>", self.enter)
        self.labels[name + "_planet"].bind("<Leave>", self.leave)
        self.labels[name + "_planet"].bind(
            "<Button-1>", lambda event, x=name: self.lockPlanetData(x)
        )
        self.labels[name + "_planet"]["image"] = self.images[name + "_planet"]

    def set_image(self, name, enabled):
        if name not in self.labels:
            return

        forplanet = False
        lock = self.lock
        types = self.types
        if name[len(name) - 7 :] == "_planet":
            name = name[: len(name) - 7]
            forplanet = True
            lock = self.lockPlanet
            types = self.typesPlanet

        if name == None:
            error("set_image: name is None")
            return
        if name not in types:
            error("set_image: name {} is not allowed")

        grey = "{}_grey".format(name)

        if name not in lock:
            setting = grey
        else:
            setting = name

        if forplanet:
            setting = setting + "_planet"
            name = name + "_planet"

        if enabled and self.labels.get(name):
            self.labels[name]["image"] = self.images[setting]
            self.labels[name].grid()
        else:
            self.labels[name].grid()
            self.labels[name].grid_remove()

    def bodymismatch(self, systemname, bodyname):
        procgen_sysname_re = re.compile(
            """
            ^
            ([A-Za-z0-9.()\' -]+?)[ ]
            ([A-Z][A-Z]-[A-Z])[ ]
            ([a-h])(?:([0-9]+)-|)([0-9]+)
            $
        """,
            re.VERBOSE,
        )

        procgen_sys_body_name_re = re.compile(
            """
            ^
            (?P<sysname>.+?)
            (?P<desig>|[ ](?P<stars>A?B?C?D?E?F?G?H?I?J?K?L?M?N?O?))
            (?:
            |[ ](?P<nebula>Nebula)
            |[ ](?P<belt>[A-Z])[ ]Belt(?:|[ ]Cluster[ ](?P<cluster>[1-9][0-9]?))
            |[ ]Comet[ ](?P<stellarcomet>[1-9][0-9]?)
            |[ ](?P<planet>[1-9][0-9]?(?:[+][1-9][0-9]?)*)
            (?:
            |[ ](?P<planetring>[A-Z])[ ]Ring
            |[ ]Comet[ ](?P<planetcomet>[1-9][0-9]?)
            |[ ](?P<moon1>[a-z](?:[+][a-z])*)
                (?:
                |[ ](?P<moon1ring>[A-Z])[ ]Ring
                |[ ]Comet[ ](?P<moon1comet>[1-9][0-9]?)
                |[ ](?P<moon2>[a-z](?:[+][a-z])*)
                (?:
                |[ ](?P<moon2ring>[A-Z])[ ]Ring
                |[ ]Comet[ ](?P<moon2comet>[1-9][0-9]?)
                |[ ](?P<moon3>[a-z])
                )
                )
            )
            )
            $
        """,
            re.VERBOSE,
        )

        pgsysmatch = procgen_sysname_re.match(systemname)
        pgbodymatch = procgen_sys_body_name_re.match(bodyname)
        bodymismatch = not bodyname.startswith(systemname)

        if pgsysmatch and pgbodymatch and bodymismatch:
            return True
        return False

    # this seems horribly confused
    def refreshPOIData(self, event):
        # Debug.logger.debug(f"refreshPOIData {self.event} {self.waitingPOI}")

        if self.waitingPOI:
            return
        try:
            while not self.spansh_bodyq.empty():
                # only expecting to go around once
                self.temp_spanshdata = self.spansh_bodyq.get()

            # if self.temp_edsmdata:
            if not self.bodies:
                self.systemprogress["text"] = ""
                self.systemprogress["fg"] = None
                theme.update(self.systemprogress)
                self.systemprogress.grid_remove()
                self.bodies = {}
            # restructure the EDSM data
            if self.temp_spanshdata:
                spansh_bodies = self.temp_spanshdata.get("bodies")
            else:
                spansh_bodies = {}

            if spansh_bodies:
                for b in spansh_bodies:
                    if not "Belt Cluster" in b.get("name"):
                        # filter out any data errors in spansh
                        if b.get("bodyId") not in self.bodies and not self.bodymismatch(
                            self.temp_spanshdata.get("name"), b.get("name")
                        ):
                            self.bodies[b.get("bodyId")] = b

            # Debug.logger.debug("self.bodies")
            # Debug.logger.debug(self.bodies)
            if (
                nvl(CodexTypes.fsscount, 0) == 0
                and self.temp_spanshdata
                and self.temp_spanshdata.get("bodyCount")
            ):
                CodexTypes.fsscount = self.temp_spanshdata.get("bodyCount")

            bodies = self.bodies

            if len(self.bodies) > 0:
                # bodies = self.temp_edsmdata.json().get("bodies")
                bodies = self.bodies
                if bodies:
                    len_bodies = 0
                    for body in bodies.values():
                        if body.get("type") in ("Planet", "Star"):
                            len_bodies += 1
                    CodexTypes.bodycount = len_bodies
                    if not CodexTypes.fsscount:
                        CodexTypes.fsscount = 0

                    if nvl(CodexTypes.fsscount, 0) >= nvl(CodexTypes.bodycount, 0):
                        if CodexTypes.fsscount > 0:
                            self.systemprogress.grid()
                            # self.systemprogress["text"]="{}%".format(round((float(CodexTypes.bodycount)/float(CodexTypes.fsscount))*100,1))
                            self.systemprogress["text"] = "{}/{}".format(
                                CodexTypes.bodycount, nvl(CodexTypes.fsscount, "?")
                            )
                    # else:

                    #    self.systemprogress.grid()
                    #    self.systemprogress.grid_remove()

                    for k in bodies.keys():
                        # if bodies.get(k).get("name") == self.system and bodies.get(k).get("type") == "Star":
                        #    CodexTypes.parentRadius = self.light_seconds(
                        #        "solarRadius", bodies.get(k).get("solarRadius"))

                        # lets normalise radius between planets and stars
                        if bodies.get(k).get("solarRadius") is not None:
                            bodies[k]["radius"] = bodies.get(k).get("solarRadius")

                    for k in bodies.keys():
                        b = bodies.get(k)

                        ## handle missing subTYpe
                        if b.get("type") == "Planet" and b.get("subType") is None:
                            print("fixing subtype")
                            b["subType"] = "Unknown"

                        # debug(json.dumps(b,indent=4))
                        body_code = b.get("name").replace(self.system + " ", "")
                        body_name = b.get("name")

                        self.shepherd_moon(b, bodies, body_code)
                        self.hot_landable(b)
                        self.synchronous_orbit(b)
                        self.helium_rich(b)
                        self.trojan(b, bodies)
                        self.ringed_star(b)
                        self.close_rings(b, bodies, body_code)
                        self.close_bodies(b, bodies, body_code)
                        self.close_flypast(b, bodies, body_code)
                        self.rings(b, body_name)
                        self.green_system(bodies)
                        self.deeply_nested(b, body_code)
                        self.satellite_star(b, body_code)
                        self.high_value(b, body_code)

                        # Terraforming
                        if b.get("terraformingState") == "Terraformable":
                            if b.get("isLandable"):
                                if not b.get("rings"):
                                    self.add_poi(
                                        "Tourist", "Landable Terraformable", body_code
                                    )
                                else:
                                    self.add_poi(
                                        "Tourist",
                                        "Landable Ringed Terraformable",
                                        body_code,
                                    )

                        elif b.get("terraformingState") == "Terraforming":
                            if b.get("isLandable"):
                                if not b.get("rings"):
                                    self.add_poi(
                                        "Tourist", "Landable Terraforming", body_code
                                    )
                                else:
                                    self.add_poi(
                                        "Tourist",
                                        "Landable Ringed Terraforming",
                                        body_code,
                                    )
                            else:
                                self.add_poi("Tourist", "Terraforming", body_code)
                        else:
                            if b.get("rings") and b.get("isLandable"):
                                self.add_poi(
                                    "Tourist", "Landable Ringed Body", body_code
                                )

                        # Landable Volcanism
                        if (
                            b.get("type") == "Planet"
                            and b.get("volcanismType")
                            and b.get("volcanismType") != "No volcanism"
                            and b.get("isLandable")
                        ):
                            self.add_poi(
                                "Geology",
                                "$Volcanism:"
                                + b.get("volcanismType").replace(" Volcanism", ""),
                                body_code,
                            )
                            # check SAA signals
                            """  if body_code not in self.saadata:
                                if body_code not in self.ppoidata:
                                    # self.add_poi("Geology", "$Sites:Need DSS", body_code)
                                    self.add_poi(
                                        "MissingData", "$Geology:Need DSS", body_code)
                                    # self.ppoidata[body_code] = {}
                                else:
                                    if "Geology" not in self.ppoidata[body_code]:
                                        # self.add_poi("Geology", "$Sites:Need DSS", body_code)
                                        self.add_poi(
                                            "MissingData", "$Geology:Need DSS", body_code) """

                        # Landable Atmosphere
                        if (
                            b.get("type") == "Planet"
                            and b.get("atmosphereType") != "No atmosphere"
                            and b.get("isLandable")
                        ):
                            self.remove_poi(
                                "MissingData", "$Planets:Need FSS", body_code
                            )
                            """ if body_code not in self.saadata:
                                if body_code not in self.ppoidata:
                                    # self.add_poi("Biology", "$Species:Need DSS", body_code)
                                    self.add_poi(
                                        "MissingData", "$Biology:Need DSS", body_code)
                                    # self.ppoidata[body_code] = {}
                                else:
                                    if "Biology" not in self.ppoidata[body_code]:
                                        # self.add_poi("Biology", "$Species:Need DSS", body_code)
                                        self.add_poi(
                                            "MissingData", "$Biology:Need DSS", body_code) """

                        # Thin Atmosphere
                        if (
                            b.get("type") == "Planet"
                            and b.get("atmosphereType")
                            and "Thin" in b.get("atmosphereType")
                            and not b.get("isLandable")
                        ):
                            if body_code not in self.saadata:
                                if body_code not in self.ppoidata:
                                    self.add_poi(
                                        "MissingData", "$Planets:Need FSS", body_code
                                    )

                        # fast orbits
                        if b.get("orbitalPeriod"):
                            if abs(float(b.get("orbitalPeriod"))) <= 0.042:
                                self.add_poi(
                                    "Tourist", "Fast Orbital Period", body_code
                                )

                        if b.get("subType") and "life" in b.get("subType"):
                            # journal and spansh have different sub-types
                            self.add_poi(
                                "Tourist", b.get("subType").replace("-", " "), body_code
                            )
                        # Ringed ELW etc
                        if b.get("subType") and b.get("subType") in (
                            "Earthlike body",
                            "Earth-like world",
                            "Water world",
                            "Ammonia world",
                        ):
                            if b.get("rings"):
                                self.add_poi(
                                    "Tourist",
                                    "Ringed {}".format(
                                        CodexTypes.hv_body_types.get(b.get("subType"))
                                    ),
                                    body_code,
                                )
                            if (
                                b.get("parents")
                                and b.get("parents")[0]
                                and b.get("parents")[0].get("Planet")
                            ):
                                self.add_poi(
                                    "Tourist",
                                    "{} Moon".format(
                                        CodexTypes.hv_body_types.get(b.get("subType"))
                                    ),
                                    body_code,
                                )
                        # if b.get('subType') and b.get('subType') in ('Earthlike body', 'Earth-like world') and b.get('rotationalPeriodTidallyLocked'):
                        #    self.add_poi(
                        #        "Tourist", 'Tidal Locked Earthlike World', body_code)

                        #    Landable high-g (>3g)
                        if (
                            b.get("type") == "Planet"
                            and b.get("isLandable")
                            and float(b.get("gravity")) > 2.7
                        ):
                            self.add_poi("Tourist", "High Gravity", body_code)
                        elif (
                            b.get("type") == "Planet"
                            and b.get("isLandable")
                            and float(b.get("gravity")) > 2.5
                        ):
                            self.add_poi("Tourist", "Walkable High Gravity", body_code)

                        #    Landable large (>18000km radius)
                        if (
                            b.get("type") == "Planet"
                            and b.get("isLandable")
                            and b.get("radius") > 18000
                        ):
                            self.add_poi("Tourist", "Large Radius Landable", body_code)

                        #    Moons of moons

                        #    Tiny objects (<300km radius)
                        if (
                            b.get("type") == "Planet"
                            and b.get("isLandable")
                            and b.get("radius") < 300
                        ):
                            self.add_poi("Tourist", "Tiny Radius Landable", body_code)

                        #    Fast and non-locked rotation
                        if (
                            b.get("type") == "Planet"
                            and b.get("rotationalPeriod")
                            and abs(float(b.get("rotationalPeriod"))) < 1 / 24
                            and not b.get("rotationalPeriodTidallyLocked")
                        ):
                            self.add_poi("Tourist", "Fast unlocked rotation", body_code)

                        #    High eccentricity
                        if (
                            b.get("orbitalEccentricity")
                            and float(b.get("orbitalEccentricity") or 0)
                            > CodexTypes.eccentricity
                        ):
                            self.add_poi("Tourist", "Highly Eccentric Orbit", body_code)

            else:
                CodexTypes.bodycount = 0

            while not self.poiq.empty():
                r = self.poiq.get()
                if "EXTOOL" in r:
                    body = r.get("PLANET")
                    body_code = body.replace(self.system + " ", "")
                    hud_category = r.get("TYPE")
                    if hud_category in ("Biology", "Geology"):
                        continue
                    english_name = r.get("NAME")
                    if r.get("LATITUDE") is not None and r.get("LONGITUDE") is not None:
                        latlon = (
                            "("
                            + str(r.get("LATITUDE"))
                            + ","
                            + str(r.get("LONGITUDE"))
                            + ")"
                        )
                    else:
                        latlon = None

                    if r.get("SUBTYPE") is not None:
                        self.add_poi(hud_category, r.get("SUBTYPE"), body_code)
                    self.add_ppoi(body_code, hud_category, english_name)
                    self.ppoidata[body_code][hud_category][english_name] = [
                        [None, latlon]
                    ]

                else:
                    if r.get("entryid"):
                        codex_name_ref = CodexTypes.name_ref[str(r.get("entryid"))]
                        hud_category = codex_name_ref.get("hud_category")
                        english_name = codex_name_ref.get("english_name")
                        reward = codex_name_ref.get("reward")
                    else:
                        hud_category = r.get("hud_category")
                        english_name = r.get("english_name")
                        reward = None

                    body = r.get("body")
                    # if the body is unknown we will set body code to ?
                    if body:
                        body_code = body.replace(self.system + " ", "")
                    else:
                        body_code = "?"

                    if hud_category == "Geology":
                        subcat = "$Sites:" + english_name
                    else:
                        subcat = english_name
                        if self.odyssey:
                            if hud_category == "Biology":
                                if english_name.split(" ")[0] in self.odyssey_bio:
                                    subcat = " ".join(english_name.split(" ")[0:2])
                            # rewards scale
                            if reward is not None and int(reward / 1000000) != 0:
                                subcat = (
                                    "(" + str(int(reward / 1000000)) + "$) " + subcat
                                )
                                english_name = (
                                    "("
                                    + str(int(reward / 1000000))
                                    + "$) "
                                    + english_name
                                )

                    self.add_poi(hud_category, subcat, body_code)

                    if (r.get("latitude") is None) or (r.get("longitude") is None):
                        latlon = None
                    else:
                        latlon = (
                            "("
                            + str(float(r.get("latitude")))
                            + ","
                            + str(float(r.get("longitude")))
                            + ")"
                        )

                    if r.get("index_id") is None:
                        index = None
                    else:
                        index = "#" + str(r.get("index_id"))

                    self.add_ppoi(body_code, hud_category, english_name)

                    if hud_category in ("Geology", "Biology"):
                        if body_code not in self.scandata:
                            self.scandata[body_code] = {}
                        if hud_category not in self.scandata[body_code]:
                            self.scandata[body_code][hud_category] = {}
                        if english_name not in self.scandata[body_code][hud_category]:
                            self.scandata[body_code][hud_category][english_name] = False
                        if r.get("scanned") == "true":
                            self.scandata[body_code][hud_category][english_name] = True

                        if hud_category == "Biology":
                            k = 0
                            if english_name.split(" ")[0] in (
                                "(1$)",
                                "(2$)",
                                "(3$)",
                                "(4$)",
                                "(5$)",
                                "(6$)",
                                "(7$)",
                                "(8$)",
                                "(9$)",
                            ):
                                k = 1
                            if english_name.split(" ")[k] in self.odyssey_bio:
                                subcat = " ".join(english_name.split(" ")[0 : k + 2])
                                if subcat not in self.scandata[body_code][hud_category]:
                                    self.scandata[body_code][hud_category][
                                        subcat
                                    ] = False
                                if r.get("scanned") == "true":
                                    self.scandata[body_code][hud_category][
                                        subcat
                                    ] = True

                    if self.odyssey:
                        if hud_category == "Geology" or hud_category == "Biology":
                            # if index == None:
                            index = "#" + str(
                                len(
                                    self.ppoidata[body_code][hud_category][english_name]
                                )
                                + 1
                            )

                    if [None, latlon] in self.ppoidata[body_code][hud_category][
                        english_name
                    ]:
                        self.ppoidata[body_code][hud_category][english_name].remove(
                            [None, latlon]
                        )

                    if hud_category != "Geology" and hud_category != "Biology":
                        addpoi = True
                        replacepoi = False
                        for poi in self.ppoidata[body_code][hud_category][english_name]:
                            if poi[0] == index:
                                addpoi = False
                                if latlon != None and poi[1] == None:
                                    replacepoi = True
                        if not addpoi:
                            if replacepoi:
                                self.ppoidata[body_code][hud_category][
                                    english_name
                                ].remove([index, None])
                                self.ppoidata[body_code][hud_category][
                                    english_name
                                ].append([index, latlon])
                            continue

                    if hud_category == "Thargoid" or hud_category == "Guardian":
                        if index == None:
                            continue

                    if self.odyssey:
                        if latlon is not None:
                            self.ppoidata[body_code][hud_category][english_name].append(
                                [index, latlon]
                            )
                    else:
                        self.ppoidata[body_code][hud_category][english_name].append(
                            [index, latlon]
                        )

            while not self.saaq.empty():
                r = self.saaq.get()
                if "SAAScanComplete" in r:
                    for bodyID in r.get("SAAScanComplete"):
                        body_code = (
                            r.get("SAAScanComplete")
                            .get(bodyID)
                            .replace(self.system + " ", "")
                        )
                        if body_code not in self.saadata:
                            self.saadata[body_code] = {}
                        self.remove_poi("MissingData", "$Geology:Need DSS", body_code)
                        self.remove_poi("MissingData", "$Biology:Need DSS", body_code)
                        self.remove_poi("MissingData", "$Planets:Need FSS", body_code)
                        self.remove_poi("MissingData", "$Rings:Need DSS", body_code)
                else:
                    body = r.get("body")
                    body_code = body.replace(self.system + " ", "")

                    if body_code not in self.saadata:
                        self.saadata[body_code] = {}
                    self.saadata[body_code][r.get("hud_category")] = r.get("count")
                    # self.remove_poi("Geology", "$Sites:Need DSS", body_code)
                    # self.remove_poi("Biology", "$Species:Need DSS", body_code)
                    self.remove_poi("MissingData", "$Geology:Need DSS", body_code)
                    self.remove_poi("MissingData", "$Biology:Need DSS", body_code)
                    self.remove_poi("MissingData", "$Planets:Need FSS", body_code)
                    self.remove_poi("MissingData", "$Rings:Need DSS", body_code)
                    # self.remove_poi("MissingData", "$Rings:Need DSS", body_code)

                    if r.get("hud_category") == "Ring":
                        self.add_poi(
                            r.get("hud_category"),
                            "$Hotspots:" + r.get("english_name"),
                            body_code,
                        )
                    elif r.get("hud_category") == "Geology":
                        if body_code not in self.ppoidata:
                            self.ppoidata[body_code] = {}
                        self.update_unknown_ppoi(body_code)
                        if "Unknown" in self.ppoidata[body_code]["Geology"]:
                            if len(self.ppoidata[body_code]["Geology"]["Unknown"]) == 0:
                                self.remove_poi("Geology", "$Sites:Unknown", body_code)
                                self.remove_poi(
                                    "MissingData", "$Geology:Unknown", body_code
                                )
                            elif (
                                len(self.ppoidata[body_code]["Geology"]["Unknown"]) > 0
                            ):
                                self.add_poi("Geology", "$Sites:Unknown", body_code)
                                self.add_poi(
                                    "MissingData", "$Geology:Unknown", body_code
                                )
                    elif r.get("hud_category") == "Biology":
                        if body_code not in self.ppoidata:
                            self.ppoidata[body_code] = {}
                        self.update_unknown_ppoi(body_code)
                        if "Unknown" in self.ppoidata[body_code]["Biology"]:
                            if len(self.ppoidata[body_code]["Biology"]["Unknown"]) == 0:
                                self.remove_poi("Biology", "Unknown", body_code)
                                self.remove_poi(
                                    "MissingData", "$Biology:Unknown", body_code
                                )
                            elif (
                                len(self.ppoidata[body_code]["Biology"]["Unknown"]) > 0
                            ):
                                self.add_poi("Biology", "Unknown", body_code)
                                self.add_poi(
                                    "MissingData", "$Biology:Unknown", body_code
                                )

            while not self.cmdrq.empty():
                # only expecting to go around once
                temp_cmdrdata = self.cmdrq.get()
                body = temp_cmdrdata.get("body")
                body_code = body.replace(self.system + " ", "")

                if temp_cmdrdata["description"] is None:
                    name = temp_cmdrdata["category"]
                    index = "#1"
                    if body_code in self.ppoidata:
                        if "Personal" in self.ppoidata[body_code]:
                            if name in self.ppoidata[body_code]["Personal"]:
                                index = "#" + str(
                                    len(self.ppoidata[body_code]["Personal"][name])
                                )
                else:
                    name = temp_cmdrdata["description"]
                    index = None
                latlon = (
                    "("
                    + str(float(temp_cmdrdata["latitude"]))
                    + ","
                    + str(float(temp_cmdrdata["longitude"]))
                    + ")"
                )
                self.add_poi("Personal", name, body_code)

                self.add_ppoi(body_code, "Personal", name)
                if [index, latlon] not in self.ppoidata[body_code]["Personal"][name]:
                    self.ppoidata[body_code]["Personal"][name].append([index, latlon])

            while not self.edsm_stationq.empty():
                # only expecting to go around once
                temp_stationdata = self.edsm_stationq.get()

                # restructure the EDSM data
                if temp_stationdata:
                    edsm_stations = temp_stationdata.get("stations")
                else:
                    edsm_stations = {}

                if edsm_stations:
                    for s in edsm_stations:
                        if s["type"] != "Fleet Carrier":
                            add_station_poi = True
                            bodyname = None
                            if "body" in s:
                                bodyname = s["body"].get("name")
                                if ("latitude" in s["body"]) and (
                                    "longitude" in s["body"]
                                ):
                                    latlon = [
                                        s["body"].get("latitude"),
                                        s["body"].get("longitude"),
                                    ]
                                else:
                                    latlon = None
                            else:
                                bodyname = None
                                latlon = None

                            if s["type"] == "Planetary Outpost":
                                stype = "Planetary Outpost"
                            elif s["type"] == None or s["type"] == "Odyssey Settlement":
                                stype = "Settlement"
                            else:
                                stype = "Space Station"

                            self.stationdata[s["name"]] = {
                                "type": stype,
                                "economy": s["economy"],
                            }
                            if bodyname is not None:
                                self.settlementdata[s["name"]] = {
                                    "body": bodyname,
                                    "coords": latlon,
                                }

            for station in self.stationdata:
                # Debug.logger.debug(json.dumps(self.stationdata, indent=4))
                stype = self.stationdata[station]["type"]
                etype = self.stationdata[station].get("economy") or "None"
                ecotype = " [" + etype + "]"

                if station in self.settlementdata:
                    bodycode = self.settlementdata[station]["body"].replace(
                        self.system + " ", ""
                    )
                    latlon = None
                    if self.settlementdata[station]["coords"] is not None:
                        latlon = (
                            "("
                            + str(float(self.settlementdata[station]["coords"][0]))
                            + ","
                            + str(float(self.settlementdata[station]["coords"][1]))
                            + ")"
                        )
                    if self.hidehumandetailed:
                        self.add_poi("Human", stype, bodycode)
                    else:
                        if self.stationdata[station].get("economy"):
                            self.add_poi(
                                "Human",
                                "$"
                                + stype
                                + ":"
                                + self.stationdata[station]["economy"],
                                bodycode,
                            )
                        else:
                            self.add_poi(
                                "Human",
                                stype,
                                bodycode,
                            )

                    if bodycode is not None:
                        keep_latlon = None
                        if bodycode in self.ppoidata:
                            if "Human" in self.ppoidata[bodycode]:
                                if station in self.ppoidata[bodycode]["Human"]:
                                    keep_latlon = self.ppoidata[bodycode]["Human"][
                                        station
                                    ]
                                    self.remove_ppoi(bodycode, "Human", station)
                                if (
                                    station + ecotype
                                    in self.ppoidata[bodycode]["Human"]
                                ):
                                    keep_latlon = self.ppoidata[bodycode]["Human"][
                                        station + ecotype
                                    ]
                        self.add_ppoi(bodycode, "Human", station + ecotype)
                        if keep_latlon is None:
                            self.ppoidata[bodycode]["Human"][station + ecotype] = [
                                [None, latlon]
                            ]
                        else:
                            self.ppoidata[bodycode]["Human"][
                                station + ecotype
                            ] = keep_latlon
                else:
                    if self.hidehumandetailed:
                        self.add_poi("Human", stype, None)
                    else:
                        if etype != "None":
                            self.add_poi("Human", "$" + stype + ":" + etype, None)

            self.logqueue = False
            while not self.logq.empty():
                (
                    tmpcmdr,
                    tmpis_beta,
                    tmpsystem,
                    tmpstation,
                    tmpentry,
                    tmpstate,
                    tmpx,
                    tmpy,
                    tmpz,
                    tmpbody,
                    tmplat,
                    tmplon,
                    tmpclient,
                ) = self.logq.get()
                # Debug.logger.debug(f"logq not empty {tmpentry}")
                # self.journal_entry(tmpcmdr, tmpis_beta, tmpsystem, tmpstation, tmpentry,
                #                   tmpstate, tmpx, tmpy, tmpz, tmpbody, tmplat, tmplon, tmpclient)

        except Exception as e:
            # line = sys.exc_info()[-1].tb_lineno
            self.add_poi("Other", "Plugin Error", None)
            Debug.logger.error("Plugin Error")
            Debug.logger.error(e)
            Debug.logger.exception(e)

        # Debug.logger.debug(f"refreshPOIData end {self.event}")

        self.visualisePOIData()
        self.visualisePlanetData()

    def update_unknown_ppoi(self, body):
        """
        get the maximum index in Geology and Biology category
        and generate unknown for missing index
        """

        # Debug.logger.debug(f"update_unknown_ppoi")

        if body not in self.ppoidata:
            return

        unk_category = ["Geology", "Biology"]
        horizon_found = []

        # for odyssey
        if self.odyssey:
            max_category = {}
            min_category = {}

            for category in self.ppoidata[body]:
                if category in unk_category:
                    min_category[category] = 0
                    max_category[category] = 0
                    for type in self.ppoidata[body][category]:
                        if type != "Unknown":
                            doit = True
                            bio_found = None
                            for bio_test in self.horizon_bio:
                                if bio_test in type:
                                    bio_found = bio_test
                                    break
                            if bio_found is not None:
                                if bio_found in horizon_found:
                                    doit = False
                                else:
                                    horizon_found.append(bio_found)
                            if doit:
                                min_category[category] += 1
                                max_category[category] += 1

            if body in self.saadata:
                for category in self.saadata[body]:
                    if category in unk_category:
                        if category not in min_category:
                            min_category[category] = 0
                        max_category[category] = self.saadata[body][category]
                        if category not in self.ppoidata[body]:
                            self.ppoidata[body][category] = {}

            for category in max_category:
                if category in unk_category:
                    if category in self.ppoidata[body]:
                        self.ppoidata[body][category]["Unknown"] = []
                        for i in range(
                            min_category[category] + 1, max_category[category] + 1
                        ):
                            self.ppoidata[body][category]["Unknown"].append(
                                ["#" + str(i), None]
                            )
        # if not odyssey then do it for horizons
        else:
            max_category = {}
            for category in self.ppoidata[body]:
                if (category == "Geology") or (category == "Biology"):
                    max_category[category] = 0
                    for type in self.ppoidata[body][category]:
                        for poi in self.ppoidata[body][category][type]:
                            if poi[0] is not None:
                                if int(poi[0][1:]) > max_category[category]:
                                    max_category[category] = int(poi[0][1:])

            if body in self.saadata:
                if "Geology" in self.saadata[body]:
                    max_category["Geology"] = self.saadata[body]["Geology"]
                    if "Geology" not in self.ppoidata[body]:
                        self.ppoidata[body]["Geology"] = {}
                if "Biology" in self.saadata[body]:
                    max_category["Biology"] = self.saadata[body]["Biology"]
                    if "Biology" not in self.ppoidata[body]:
                        self.ppoidata[body]["Biology"] = {}

            for category in max_category:
                for i in range(1, max_category[category] + 1):
                    find_i = False
                    for type in self.ppoidata[body][category]:
                        for poi in self.ppoidata[body][category][type]:
                            if poi[0] == "#" + str(i):
                                find_i = True
                                break
                        if find_i:
                            break
                    if not find_i:
                        if "Unknown" not in self.ppoidata[body][category]:
                            self.ppoidata[body][category]["Unknown"] = []
                        self.ppoidata[body][category]["Unknown"].append(
                            ["#" + str(i), None]
                        )

    def remove_ppoi(self, body, hud_category, english_name):
        """
        remove the index in the hud_category
        and add it in the unknown list for this hud_category
        """

        # Debug.logger.debug(f"remove_ppoi {hud_category} {english_name}")

        if body not in self.ppoidata:
            return
        if hud_category not in self.ppoidata[body]:
            return
        if english_name not in self.ppoidata[body][hud_category]:
            return
        del self.ppoidata[body][hud_category][english_name]

    def add_ppoi(self, body, hud_category, type):
        """
        add new index
        check if it exist in the unknown list and remove it
        """

        # Debug.logger.debug(f"add_ppoi {body} {hud_category} {type}")

        if body not in self.ppoidata:
            self.ppoidata[body] = {}
        if hud_category not in self.ppoidata[body]:
            self.ppoidata[body][hud_category] = {}
        if type not in self.ppoidata[body][hud_category]:
            self.ppoidata[body][hud_category][type] = []

    def add_ppoi_wsaa(self, body, hud_category, type, index, lat, lon, scanned):
        """
        add new index
        check if it exist in the unknown list and remove it
        """

        # Debug.logger.debug(
        #    f"add_ppoi_wsaa {body} {hud_category} {type} {index} {lat} {lon} {scanned}")

        self.add_ppoi(body, hud_category, type)
        if "Unknown" not in self.ppoidata[body][hud_category]:
            self.ppoidata[body][hud_category]["Unknown"] = []

        if body not in self.scandata:
            self.scandata[body] = {}
        if hud_category not in self.scandata[body]:
            self.scandata[body][hud_category] = {}
        if type not in self.scandata[body][hud_category]:
            self.scandata[body][hud_category][type] = False
        if scanned:
            self.scandata[body][hud_category][type] = True

        if hud_category == "Biology":
            k = 0
            if type.split(" ")[0] in (
                "(1$)",
                "(2$)",
                "(3$)",
                "(4$)",
                "(5$)",
                "(6$)",
                "(7$)",
                "(8$)",
                "(9$)",
            ):
                k = 1
            if type.split(" ")[k] in self.odyssey_bio:
                subcat = " ".join(type.split(" ")[0 : k + 2])
                if subcat not in self.scandata[body][hud_category]:
                    self.scandata[body][hud_category][subcat] = False
                if scanned:
                    self.scandata[body][hud_category][subcat] = True

        total_index = 0
        for t in self.ppoidata[body][hud_category]:
            total_index += len(self.ppoidata[body][hud_category][t])

        if self.odyssey:
            if index == 0:
                index = len(self.ppoidata[body][hud_category][type]) + 1

            self.ppoidata[body][hud_category][type].append(
                [
                    "#" + str(index),
                    "(" + str(round(lat, 4)) + "," + str(round(lon, 4)) + ")",
                ]
            )
            self.update_unknown_ppoi(body)

        else:
            if index > total_index:
                self.ppoidata[body][hud_category][type].append(
                    ["#" + str(index), "(" + str(lat) + "," + str(lon) + ")"]
                )
                self.update_unknown_ppoi(body)
            else:
                find_i = False
                for i in range(len(self.ppoidata[body][hud_category]["Unknown"])):
                    poi = self.ppoidata[body][hud_category]["Unknown"][i]
                    if "#" + str(index) == poi[0]:
                        del self.ppoidata[body][hud_category]["Unknown"][i]
                        find_i = True
                    if find_i:
                        break
                if find_i:
                    self.ppoidata[body][hud_category][type].append(
                        ["#" + str(index), "(" + str(lat) + "," + str(lon) + ")"]
                    )

    """
    This function is called in a thread so the only TKinter code that can run here is to insert an event
    using self.frame.event_generate('<<refreshPOIData>>', when='head')
    Remember no tk inter calls in threads please!
    """

    def getPOIdata(self, system, system64, cmdr):
        if not config.shutting_down:
            Debug.logger.debug(
                f"Getting POI data in thread {self.event} - system = {system} - system64 = {system64}"
            )
            self.waitingPOI = True
            # debug("CodexTypes.waiting = True")
            # first we will clear the queues
            self.logq.clear()
            self.spansh_bodyq.clear()
            self.edsm_stationq.clear()
            self.poiq.clear()
            self.saaq.clear()
            self.cmdrq.clear()
            temp_spanshdata = {}
            self.temp_spanshdata = {}
            self.ppoidata = {}
            self.poidata = {}
            self.saadata = {}
            self.bodies = None
            CodexTypes.bodycount = None
            CodexTypes.fsscount = None
            try:
                url = f"https://spansh.co.uk/api/dump/{system64}"
                headers = {"User-Agent": f"{ClientVersion.client()} (canonn.codex.py)"}

                r = requests.get(url, timeout=30, headers=headers)
                # debug("request complete")
                r.encoding = "utf-8"
                if r.status_code == requests.codes.ok:
                    # debug("got EDSM Data")
                    j = r.json()
                    temp_spanshdata = j.get("system")
                    for b in temp_spanshdata.get("bodies"):
                        mismatch = self.bodymismatch(
                            temp_spanshdata.get("name"), b.get("name")
                        )
                        in_date = (
                            b.get("signals")
                            and b.get("signals").get("updateTime")
                            and not b.get("signals")
                            .get("updateTime")
                            .startswith("2020")
                        )
                        in_date = in_date and is_timestamp_older(
                            b.get("updateTime"), b.get("signals").get("updateTime")
                        )

                        if (
                            b.get("signals")
                            and b.get("signals").get("signals")
                            and not mismatch
                            and in_date
                        ):
                            signals = b.get("signals").get("signals")
                            for key in signals.keys():
                                type = key
                                english_name = (
                                    type.replace("$SAA_SignalType_", "")
                                    .replace("ical;", "y")
                                    .replace(";", "")
                                )
                                if " Ring" in b.get("name"):
                                    cat = "Ring"
                                if "$SAA_SignalType_" in type:
                                    cat = english_name

                                saa_signal = {}
                                saa_signal["body"] = b.get("name")
                                saa_signal["hud_category"] = cat
                                saa_signal["english_name"] = english_name
                                saa_signal["count"] = signals.get(key)
                                self.saaq.put(saa_signal)
                        if b.get("signals") and b.get("signals").get("genuses"):
                            debug("got genuses")
                            b.get("signals").get("genuses")
                            for genus in b.get("signals").get("genuses"):
                                english_name = CodexTypes.genus.get(genus)
                                debug(f"genus {english_name}")
                                saa_signal = {}
                                saa_signal["body"] = b.get("name")
                                saa_signal["hud_category"] = "Biology"
                                saa_signal["english_name"] = english_name
                                self.poiq.put(saa_signal)
                        if b.get("rings"):
                            for ring in b.get("rings"):
                                mismatch = self.bodymismatch(
                                    temp_spanshdata.get("name"), ring.get("name")
                                )
                                if (
                                    ring.get("signals")
                                    and ring.get("signals").get("signals")
                                    and not mismatch
                                ):
                                    signals = ring.get("signals").get("signals")
                                    for key in signals.keys():
                                        saa_signal = {}
                                        saa_signal["body"] = b.get("name")
                                        saa_signal["hud_category"] = "Ring"
                                        saa_signal["english_name"] = key
                                        saa_signal["count"] = signals.get(key)

                                        self.saaq.put(saa_signal)

                    # push edsm data only a queue
                    self.spansh_bodyq.put(temp_spanshdata)
                else:
                    Debug.logger.error(f"Spansh result {r.status_code}")
            except Exception as e:
                Debug.logger.error("Error getting Spansh data")
                Debug.logger.error(e)
                Debug.logger.exception(e)

            try:
                url = (
                    "https://www.edsm.net/api-system-v1/stations?systemName={}".format(
                        quote_plus(system.encode("utf8"))
                    )
                )

                # debug("request {}:  Active Threads {}".format(
                #    url, threading.activeCount()))

                r = requests.get(url, timeout=30)
                # debug("request complete")
                r.encoding = "utf-8"
                if r.status_code == requests.codes.ok:
                    # debug("got EDSM Data")
                    temp_stationdata = r.json()
                    # push edsm data only a queue
                    self.edsm_stationq.put(temp_stationdata)
                else:
                    Debug.logger.error(f"EDSM Failed {r.status_code}")
            except:
                Debug.logger.error("Error getting EDSM data")

            temp_poidata = {}
            # if temp_spanshdata.get("bodies") and len(temp_spanshdata.get("bodies")) > 0:
            Debug.logger.debug("Getting Canonn Data")
            try:
                EDversion = "N"
                if self.odyssey:
                    EDversion = "Y"
                url = "https://us-central1-canonn-api-236217.cloudfunctions.net/query/getSystemPoi?system={}&odyssey={}&cmdr={}".format(
                    quote_plus(system.encode("utf8")), EDversion, cmdr
                )

                # debug(url)
                # debug("request {}:  Active Threads {}".format(
                #    url, threading.activeCount()))
                if (
                    temp_spanshdata.get("bodies")
                    and len(temp_spanshdata.get("bodies")) > 0
                ):
                    headers = {
                        "Accept-Encoding": "gzip, deflate",
                    }
                    r = requests.get(url, headers=headers, timeout=45)
                    # debug("request complete")
                    r.encoding = "utf-8"
                    if r.status_code == requests.codes.ok:
                        # debug("got POI Data")
                        temp_poidata = r.json()
                    else:
                        Debug.logger.error("Canonn data not recived")
                else:
                    Debug.logger.debug("Skipping Canonn Fetch")
                    temp_poidata = []
                # push the data ont a queue
                if "codex" in temp_poidata:
                    for v in temp_poidata["codex"]:
                        self.poiq.put(v)

                if "ScanOrganic" in temp_poidata:
                    for v in temp_poidata["ScanOrganic"]:
                        self.poiq.put(v)

                if "SAAsignals" in temp_poidata:
                    for v in temp_poidata["SAAsignals"]:
                        self.saaq.put(v)
                if "cmdr" in temp_poidata:
                    for v in temp_poidata["cmdr"]:
                        self.cmdrq.put(v)
            except:
                Debug.logger.error("Error getting POI data")
            # else:
            #    Debug.logger.debug("Skipping Canonn Fetch")
            #    Debug.logger.debug(temp_spanshdata.get("bodies"))

            self.waitingPOI = False
            Debug.logger.debug("Triggering Event")
            debug("getPOIdata frame.event_generate <<refreshPOIData>>")
            self.frame.event_generate("<<refreshPOIData>>", when="head")
            # self.frame.event_generate('<<refreshPlanetData>>', when='head')

            Debug.logger.debug("Finished getting POI data in thread")

        else:
            Debug.logger.debug("get POI data in shut sown")

        # really important not to call any functions tha use TK inter in thread or
        # the plugin will go Kablooie!
        # self.refreshPOIData(None)

    def cleanPOIPanel(self):
        for col in self.systemcol1:
            try:
                col.destroy()
            except:
                error("Col1 grid_remove error")
        for col in self.systemcol2:
            try:
                col.destroy()
            except:
                error("Col2 grid_remove error")
        self.systemcol1 = []
        self.systemcol2 = []

    """
    We need to make sure that if we have genus and species we only display species.
    """

    def cleanPOIdata(self):
        # create a list of bodies from poidata
        def get_bodies(data):
            bodies = []
            for key in data.keys():
                bodies.extend(data.get(key))
            return list(set(bodies))

        bio = self.poidata.get("Biology")

        newbio = {}
        bodies = {}

        if bio:
            for body in get_bodies(bio):
                bodies[body] = {}

            # reorganise data
            for entry in bio.keys():
                for body in bio.get(entry):
                    # Debug.logger.debug(f"{body} -> {entry}")
                    # populate bodies with bodyid->genus->entry
                    if not bodies[body].get(get_genus(entry)):
                        bodies[body][get_genus(entry)] = []
                    bodies[body][get_genus(entry)].append(entry)
            # Debug.logger.debug(bodies)
            # now we need to recreate bio without the genus if another entry exists

            for bodyid, genus in bodies.items():
                for entries in genus.values():
                    # Debug.logger.debug(f"{bodyid} -> {genus} -> {entries}")
                    # if we only have one entry we must add it regardless
                    if len(entries) == 1:
                        if not newbio.get(entries[0]):
                            newbio[entries[0]] = []
                            newbio[entries[0]].append(bodyid)
                    # then we only add entries if they are not the genus
                    # the genus may already have been added in teh previous step
                    for entry in entries:
                        if not entry == get_genus(entry):
                            if not newbio.get(entry):
                                newbio[entry] = []
                            newbio[entry].append(bodyid)
                        if newbio.get(entry):
                            newbio[entry] = list(set(newbio.get(entry)))
            Debug.logger.debug(f"newbio {newbio}")
            self.poidata["Biology"] = newbio

    def visualisePOIData(self):
        # clear it if it exists
        self.cleanPOIPanel()

        self.systempanel.grid_remove()

        # Debug.logger.debug(f"visualise POI Data event={self.event}")

        self.set_image("MissingData", False)
        self.set_image("Geology", False)
        self.set_image("Cloud", False)
        self.set_image("Anomaly", False)
        self.set_image("Thargoid", False)
        self.set_image("Biology", False)
        self.set_image("Guardian", False)
        self.set_image("Human", False)
        self.set_image("Ring", False)
        self.set_image("None", False)
        self.set_image("Other", False)
        self.set_image("Personal", False)
        self.set_image("Planets", False)
        self.set_image("Tourist", False)
        self.set_image("Jumponium", False)
        self.set_image("GreenSystem", False)

        nothing = True
        for category in self.poidata:
            if self.hidemissingdata:
                if category == "MissingData":
                    continue
            self.set_image(category, True)
            nothing = False
        nothing = False
        # fix the poi data to remove genus
        self.cleanPOIdata()
        # need to initialise if not exists
        self.systemtitle_name["text"] = self.system
        # self.systemtitle_name["url"] = f"https://us-central1-canonn-api-236217.cloudfunctions.net/query/codex/biostats?id={self.system64}"
        self.systemtitle_name["url"] = (
            f"https://canonn-science.github.io/canonn-signals/index.html?system={self.system64}"
        )

        openlist = False
        for category in self.types:
            self.systemlist[category].grid_remove()

            if category in self.poidata:
                self.systemcol1.append(
                    tk.Label(self.systemlist[category], text=category + ":")
                )
                self.systemcol2.append(tk.Label(self.systemlist[category], text=""))
                theme.update(self.systemcol1[-1])
                theme.update(self.systemcol2[-1])
                self.systemcol1[-1].grid(
                    row=len(self.systemcol1), column=0, columnspan=1, sticky="NW"
                )
                self.systemcol2[-1].grid(
                    row=len(self.systemcol1), column=1, sticky="NW"
                )

                self.poidata[category] = dict(sorted(self.poidata[category].items()))

                prev_subcategory = "Others"
                isSubcategory = ""
                label = []
                for type in self.poidata[category]:
                    if len(self.poidata[category][type]) == 0:
                        continue

                    self.poidata[category][type] = sorted(self.poidata[category][type])

                    if type[0] == "$":
                        subcategory = type.split(":")[0][1:]
                        name = type.split(":")[1]
                    else:
                        subcategory = "Others"
                        name = type

                    if subcategory != prev_subcategory:
                        isSubcategory = "   "
                        prev_subcategory = subcategory
                        n_fss = ""
                        if category == "Human" and subcategory == "Others":
                            if self.nfss != 0:
                                n_fss = "WarZone [" + str(self.nfss) + "]"
                        self.systemcol1.append(
                            tk.Label(
                                self.systemlist[category],
                                text="   " + subcategory + ":",
                            )
                        )
                        self.systemcol2.append(
                            tk.Label(self.systemlist[category], text=n_fss)
                        )
                        theme.update(self.systemcol1[-1])
                        theme.update(self.systemcol2[-1])
                        self.systemcol1[-1].grid(
                            row=len(self.systemcol1),
                            column=0,
                            columnspan=1,
                            sticky="NW",
                        )
                        self.systemcol2[-1].grid(
                            row=len(self.systemcol1), column=1, sticky="NW"
                        )

                    self.systemcol1.append(
                        tk.Label(
                            self.systemlist[category], text="   " + isSubcategory + name
                        )
                    )
                    self.systemcol2.append(tk.Frame(self.systemlist[category]))
                    theme.update(self.systemcol1[-1])
                    theme.update(self.systemcol2[-1])

                    i = 0
                    col = 0
                    for poibody in self.poidata[category][type]:
                        col = ((i % 5) + 1) * 4
                        row = int(i / 5)
                        # row = 0
                        label.append(tk.Label(self.systemcol2[-1], text=poibody))
                        if poibody in self.ppoidata:
                            if config.get_int("theme") == 0:
                                label[-1]["fg"] = "blue"
                            if config.get_int("theme") == 1:
                                label[-1]["fg"] = "white"
                            label[-1]["cursor"] = "hand2"
                            label[-1].bind(
                                "<Button-1>",
                                lambda event, body=poibody: self.bodyFocus(body),
                            )
                        theme.update(label[-1])
                        label[-1].grid(row=row, column=col, sticky="NW")
                        i += 1
                        col += 1
                        if category in ("Geology", "Biology"):
                            if poibody in self.scandata:
                                if category in self.scandata[poibody]:
                                    if type in self.scandata[poibody][category]:
                                        if not self.scandata[poibody][category][type]:
                                            label[-1]["text"] = "*" + label[-1]["text"]
                                            # label.append(tk.Label(self.systemcol2[-1], text="(*)"))
                                            # theme.update(label[-1])
                                            # label[-1].grid(row=row, column=col, sticky="NW")
                                            # col += 1
                        if category in (
                            "Geology",
                            "Biology",
                            "Human",
                            "Thargoid",
                            "Guardian",
                        ):
                            if name == "Unknown":
                                nunk = len(self.ppoidata[poibody][category]["Unknown"])
                                nsites = len(self.ppoidata[poibody][category])
                                if poibody in self.saadata:
                                    if category in self.saadata[poibody]:
                                        nsites = self.saadata[poibody][category]
                                label.append(
                                    tk.Label(
                                        self.systemcol2[-1],
                                        text="["
                                        + str(nsites - nunk)
                                        + "/"
                                        + str(nsites)
                                        + "]",
                                    )
                                )
                                theme.update(label[-1])
                                label[-1].grid(row=row, column=col, sticky="NW")
                                col += 1
                        if category == "MissingData":
                            if name == "Unknown":
                                nunk = len(
                                    self.ppoidata[poibody][subcategory]["Unknown"]
                                )
                                nsites = len(self.ppoidata[poibody][subcategory])
                                if poibody in self.saadata:
                                    if subcategory in self.saadata[poibody]:
                                        nsites = self.saadata[poibody][subcategory]
                                label.append(
                                    tk.Label(
                                        self.systemcol2[-1],
                                        text="["
                                        + str(nsites - nunk)
                                        + "/"
                                        + str(nsites)
                                        + "]",
                                    )
                                )
                                theme.update(label[-1])
                                label[-1].grid(row=row, column=col, sticky="NW")
                                col += 1
                        if i < len(self.poidata[category][type]):
                            label.append(tk.Label(self.systemcol2[-1], text=","))
                            theme.update(label[-1])
                            label[-1].grid(row=row, column=col, sticky="N")
                            col += 1

                    self.systemcol1[-1].grid(
                        row=len(self.systemcol1), column=0, columnspan=1, sticky="NW"
                    )
                    self.systemcol2[-1].grid(
                        row=len(self.systemcol1), column=1, sticky="NW"
                    )

                if category in self.lock:
                    openlist = True
                    self.systemlist[category].grid()

        if not nothing:
            self.visible()
            self.systemtitle.grid()
            if openlist:
                self.systempanel.grid()
        # self.tooltip["text"]=CodexTypes.tooltips.get(event.widget["text"])

    def cleanPlanetPanel(self):
        for col in self.planetcol1:
            col.destroy()
        for col in self.planetcol2:
            col.destroy()
        self.planetcol1 = []
        self.planetcol2 = []

    def visualisePlanetData(self):
        """
        A helper function to remove Genus when a sample of the species is
        already found.
        """

        def cleanPlanetData(data):
            newbio = {}
            genuses = {}
            # ensure that if we have a full entry we do not display genus
            bio = data.get("Biology")
            if bio:
                for key in bio.keys():
                    # build a dict of genuses containing array of specimens
                    if not genuses.get(get_genus(key)):
                        genuses[get_genus(key)] = []
                    genuses[get_genus(key)].append({"key": key, "value": bio.get(key)})

                # Debug.logger.debug(genuses)

                # we will check if we have more than one specimen
                # for each genus and decide which to keep
                for genus in genuses.keys():
                    for specimen in genuses.get(genus):
                        isGenus = specimen.get("key") == genus
                        # Debug.logger.debug(
                        #    f"genus {genus} specimen {specimen} hasGenus {hasGenus}")
                        # The genus is the only entry so we keep it
                        if isGenus and len(genuses.get(genus)) == 1:
                            newbio[specimen.get("key")] = specimen.get("value")
                            # Debug.logger.debug(f"adding {specimen}")
                        # we are not a genus so can always be returned
                        elif not isGenus:
                            # Debug.logger.debug(f"adding {specimen}")
                            newbio[specimen.get("key")] = specimen.get("value")
                        else:
                            pass
                            # Debug.logger.debug(f"skipping {specimen}")

                data["Biology"] = newbio
                # Debug.logger.debug(newbio)
            return data

        self.cleanPlanetPanel()
        self.planettitle.grid_remove()
        self.planetpanel.grid_remove()

        if self.planetlist_body not in self.ppoidata:
            return
            # self.planetlist_body = None
            # self.planetlist_show = False

        if not self.planetlist_show:
            return

        self.set_image("Geology_planet", False)
        self.set_image("Thargoid_planet", False)
        self.set_image("Biology_planet", False)
        self.set_image("Guardian_planet", False)
        self.set_image("Human_planet", False)
        self.set_image("Other_planet", False)
        self.set_image("Personal_planet", False)
        self.set_image("Tourist_planet", False)
        self.set_image("Jumponium_planet", False)

        # refresh ppoi for unknown list
        self.update_unknown_ppoi(self.planetlist_body)
        Debug.logger.debug(self.ppoidata[self.planetlist_body])
        for category in self.ppoidata[self.planetlist_body]:
            self.set_image(category + "_planet", True)

        self.planettitle_name["text"] = self.planetlist_body

        for category in self.typesPlanet:
            self.planetlist[category].grid_remove()

            self.ppoidata[self.planetlist_body] = cleanPlanetData(
                self.ppoidata[self.planetlist_body]
            )

            if category in self.ppoidata[self.planetlist_body]:
                self.ppoidata[self.planetlist_body][category] = dict(
                    sorted(self.ppoidata[self.planetlist_body][category].items())
                )

                self.planetcol1.append(
                    tk.Label(self.planetlist[category], text=category + ":")
                )
                self.planetcol2.append(tk.Label(self.planetlist[category], text=""))
                theme.update(self.planetcol1[-1])
                theme.update(self.planetcol2[-1])
                self.planetcol1[-1].grid(
                    row=len(self.planetcol1), column=0, columnspan=1, sticky="NW"
                )
                self.planetcol2[-1].grid(
                    row=len(self.planetcol1), column=1, sticky="NW"
                )

                if self.odyssey:
                    if "Unknown" in self.ppoidata[self.planetlist_body][category]:
                        nunk = len(
                            self.ppoidata[self.planetlist_body][category]["Unknown"]
                        )
                        nsites = len(self.ppoidata[self.planetlist_body][category])
                        if self.planetlist_body in self.saadata:
                            if category in self.saadata[self.planetlist_body]:
                                nsites = self.saadata[self.planetlist_body][category]
                        self.planetcol2[-1]["text"] = (
                            str(round((nsites - nunk) / nsites * 100, 2))
                            + "% ["
                            + str(nsites - nunk)
                            + "/"
                            + str(nsites)
                            + "]"
                        )

                label = []
                for type in self.ppoidata[self.planetlist_body][category]:
                    if self.odyssey and type == "Unknown":
                        continue
                    self.planetcol1.append(
                        tk.Label(self.planetlist[category], text="   " + type)
                    )
                    self.planetcol2.append(tk.Frame(self.planetlist[category]))
                    theme.update(self.planetcol1[-1])
                    theme.update(self.planetcol2[-1])
                    if category in ("Geology", "Biology"):
                        if self.planetlist_body in self.scandata:
                            if category in self.scandata[self.planetlist_body]:
                                if (
                                    type
                                    in self.scandata[self.planetlist_body][category]
                                ):
                                    if not self.scandata[self.planetlist_body][
                                        category
                                    ][type]:
                                        # self.planetcol1[-1]['fg'] = "red"
                                        # self.planetcol1[-1]['text'] = "   (*) " + type
                                        self.planetcol1[-1]["text"] = "   *" + type

                    if len(self.ppoidata[self.planetlist_body][category][type]) > 0:
                        self.ppoidata[self.planetlist_body][category][type] = sorted(
                            self.ppoidata[self.planetlist_body][category][type],
                            key=lambda poi: int(nvl(poi[0], "#0")[1:]),
                        )

                        i = 0
                        for poi in self.ppoidata[self.planetlist_body][category][type]:
                            col = (i % 10) + 1
                            row = int(i / 10)
                            if poi[0] is not None:
                                label.append(tk.Label(self.planetcol2[-1], text=poi[0]))
                                if poi[1] is not None:
                                    if config.get_int("theme") == 0:
                                        label[-1]["fg"] = "blue"
                                    if config.get_int("theme") == 1:
                                        label[-1]["fg"] = "white"
                                    label[-1]["cursor"] = "hand2"
                                    label[-1].bind(
                                        "<Button-1>",
                                        lambda event, latlon=poi[
                                            1
                                        ]: self.activateDestination(latlon),
                                    )
                                theme.update(label[-1])
                                label[-1].grid(row=row, column=col, sticky="NW")
                            if poi[1] is not None:
                                if poi[0] is None:
                                    label.append(
                                        tk.Label(self.planetcol2[-1], text=poi[1])
                                    )
                                    theme.update(label[-1])
                                    label[-1].grid(row=row, column=col, sticky="NW")
                                    if config.get_int("theme") == 0:
                                        label[-1]["fg"] = "blue"
                                    if config.get_int("theme") == 1:
                                        label[-1]["fg"] = "white"
                                    label[-1]["cursor"] = "hand2"
                                    label[-1].bind(
                                        "<Button-1>",
                                        lambda event, latlon=poi[
                                            1
                                        ]: self.activateDestination(latlon),
                                    )
                            i += 1

                    self.planetcol1[-1].grid(
                        row=len(self.planetcol1), column=0, columnspan=1, sticky="NW"
                    )
                    self.planetcol2[-1].grid(
                        row=len(self.planetcol1), column=1, sticky="NW"
                    )

                if self.odyssey:
                    if "Unknown" in self.ppoidata[self.planetlist_body][category]:
                        for iunk in range(nunk):
                            self.planetcol1.append(
                                tk.Label(self.planetlist[category], text="   Unknown")
                            )
                            self.planetcol2.append(tk.Frame(self.planetlist[category]))
                            theme.update(self.planetcol1[-1])
                            theme.update(self.planetcol2[-1])
                            self.planetcol1[-1].grid(
                                row=len(self.planetcol1),
                                column=0,
                                columnspan=1,
                                sticky="NW",
                            )
                            self.planetcol2[-1].grid(
                                row=len(self.planetcol1), column=1, sticky="NW"
                            )

                if category in self.lockPlanet:
                    self.planetlist[category].grid()

        if self.planetlist_show:
            self.planettitle.grid()

            remove_panel = True
            for category in self.ppoidata[self.planetlist_body]:
                if category in self.lockPlanet:
                    remove_panel = False
            if not remove_panel:
                self.planetpanel.grid()

    def add_poi(self, hud_category, english_name, body):
        # check if its bark mounds. if no volcanism then we will adjust the name
        if "Bark Mounds" in english_name and self.odyssey:
            # we need to change for volcanism
            for b in self.bodies.values():
                novolcanoes = (
                    b.get("volcanismType") is None
                    or b.get("volcanismType") == "No volcanism"
                )
                if (
                    b.get("name") == str(body)
                    or b.get("name") == f"{self.system} {str(body)}"
                    and novolcanoes
                ):
                    english_name = "Ex-Bark Mounds"

        # Debug.logger.debug(f"add_poi - {hud_category} {english_name} {body}")

        if hud_category not in self.poidata:
            self.poidata[hud_category] = {}
        if english_name not in self.poidata[hud_category]:
            self.poidata[hud_category][english_name] = []
        poinotexist = True
        for poibody in self.poidata[hud_category][english_name]:
            if body is not None:
                if poibody is None:
                    self.poidata[hud_category][english_name].remove(None)
            if body is None and poibody is not None:
                poinotexist = False
                break
            if poibody == body:
                poinotexist = False
                break
        if poinotexist:
            self.poidata[hud_category][english_name].append(body)
        # else:
        #    Debug.logger.debug(f"add_poi - body already in poidata")

    def remove_poi(self, hud_category, english_name, body):
        # Debug.logger.debug(
        #    f"remove_poi - {hud_category} {english_name} {body}")

        if hud_category in self.poidata:
            if english_name in self.poidata[hud_category]:
                poinotexist = True
                for poibody in self.poidata[hud_category][english_name]:
                    if poibody == body:
                        poinotexist = False
                        break
                if not poinotexist:
                    self.poidata[hud_category][english_name].remove(body)
                if len(self.poidata[hud_category][english_name]) == 0:
                    del self.poidata[hud_category][english_name]
            if len(self.poidata[hud_category]) == 0:
                del self.poidata[hud_category]

    @plugin_error
    def helium_rich(self, b):
        body_code = b.get("name").replace(self.system + " ", "")
        gasgiant = b.get("subType") and "gas giant" in b.get("subType").lower()
        composition = b.get("atmosphereComposition")

        if gasgiant and b.get("subType").lower() in (
            "helium rich gas giant",
            "helium-rich gas giant",
            "helium gas giant",
        ):
            self.add_poi("Tourist", f"{b.get('subType').replace('-',' ')}", body_code)

        if (
            gasgiant
            and composition
            and composition.get("Helium")
            and float(composition.get("Helium")) >= 30
        ):
            self.add_poi("Tourist", f"Helium Rich System", None)

    @plugin_error
    def hot_landable(self, b):

        body_code = b.get("name").replace(self.system + " ", "")
        if b.get("subType"):
            type = b.get("subType").replace("-", " ")
        temperature = b.get("surfaceTemperature")
        if b.get("isLandable") and temperature and float(temperature) > 1500:
            self.add_poi("Tourist", f"Hot landable {type}", body_code)

    @plugin_error
    def synchronous_orbit(self, b):
        body_code = b.get("name").replace(self.system + " ", "")
        valid = (
            b.get("rotationalPeriod")
            and b.get("orbitalPeriod")
            and b.get("rotationalPeriodTidallyLocked")
        )
        earthlike = b.get("subType") and b.get("subType") in (
            "Earthlike body",
            "Earth-like world",
        )
        starchild = (
            b.get("parents")
            and len(b.get("parents")) > 0
            and list(b.get("parents")[0].keys())[0] == "Star"
        )

        if valid and round(float(b.get("rotationalPeriod")), 4) == round(
            float(b.get("orbitalPeriod")), 4
        ):
            if earthlike and starchild:
                self.add_poi("Tourist", f"Eyeball Earthlike", body_code)
            else:
                self.add_poi("Tourist", f"Synchronous Orbit", body_code)

    @plugin_error
    def shepherd_moon(self, body, bodies, body_code):

        if body.get("type") == "Barycentre":
            return

        def get_density(mass, inner, outer):
            a1 = math.pi * pow(inner, 2)
            a2 = math.pi * pow(outer, 2)
            a = a2 - a1

            # add a tiny number to force non zero
            if a > 0:
                density = mass / a
            else:
                density = 0
            return density

        body_code = body.get("name").replace(self.system + " ", "")
        if body.get("parents"):
            rings = None
            parent = body.get("parents")[0]
            if (
                parent.get("Planet")
                and bodies.get(parent.get("Planet"))
                and bodies.get(parent.get("Planet")).get("rings")
            ):
                rings = bodies.get(parent.get("Planet")).get("rings")
                bodytype = "Moon"
            if (
                parent.get("Star")
                and bodies.get(parent.get("Star"))
                and bodies.get(parent.get("Star")).get("rings")
            ):
                rings = bodies.get(parent.get("Star")).get("rings")
                bodytype = "Planet"

            if rings:
                # find the maximum extent of the ring system
                maxradius = 0
                for ring in rings:
                    if "Belt" not in ring.get("name"):
                        outerRadius = float(ring.get("outerRadius"))
                        if maxradius < outerRadius:
                            maxradius = outerRadius

                # if it was all belts maxradius wont be set
                if maxradius > 0:
                    # all measurements in meters
                    semiMajorAxis = float(body.get("semiMajorAxis")) * 149597870691
                    try:
                        bodyRadius = (
                            float(body.get("radius") or body.get("solarRadius")) * 1000
                        )
                    except:
                        raise
                    outerRadius = float(ring.get("outerRadius"))
                    innerRadius = float(ring.get("innerRadius"))

                    for ring in rings:
                        innerproximity = semiMajorAxis + bodyRadius < innerRadius
                        outerproximity = semiMajorAxis + bodyRadius > outerRadius
                        # is the body in the middle of the rings?
                        interloping = (
                            innerRadius <= semiMajorAxis + bodyRadius <= outerRadius
                        )
                        eccentric = (
                            body.get("orbitalEccentricity")
                            and body.get("orbitalEccentricity") > 0.8
                        )

                        if innerproximity:
                            separation = innerRadius - (semiMajorAxis + bodyRadius)
                        if outerproximity:
                            separation = (semiMajorAxis + bodyRadius) - outerRadius
                        if interloping:
                            separation = 0

                        # the body extends one radius past the semiMajorAxis
                        # so this means that for it to be an outer moon it must be
                        # a minimum of one radius past the max radius
                        outer = maxradius < semiMajorAxis + bodyRadius
                        if outer:
                            type = "Outer"
                        else:
                            type = "Inner"

                        proximity = ""

                        if separation < bodyRadius * 2:
                            proximity = "Close "

                        if interloping:
                            proximity = "Touching "

                        eccentriclabel = ""
                        if eccentric:
                            eccentriclabel = "Eccentric "

                        if separation < bodyRadius * 10 or interloping:
                            # add one radius for touching surface an another for the outer limit
                            if (
                                semiMajorAxis < maxradius + (bodyRadius * 2)
                                or interloping
                            ):
                                self.add_poi(
                                    "Tourist",
                                    f"{eccentriclabel}{proximity}{type} Shepherd {bodytype}",
                                    body_code,
                                )
                        else:
                            if semiMajorAxis + bodyRadius < maxradius:
                                # just going to call in inner moon otherwise its confusing
                                self.add_poi(
                                    "Tourist", f"{eccentriclabel}Inner Moon", body_code
                                )

    def radius_ly(self, body):
        if body.get("type") == "Star" and body.get("solarRadius"):
            return self.light_seconds("solarRadius", body.get("solarRadius"))
        if body.get("type") == "Planet" and body.get("radius"):
            return self.light_seconds("radius", body.get("radius"))
        return None

    @plugin_error
    def close_flypast(self, body, bodies, body_code):
        for sibling in bodies.values():
            p1 = body.get("parents")
            p2 = sibling.get("parents")

            valid_body = True
            valid_body = p2 and valid_body
            valid_body = p1 and valid_body
            valid_body = body.get("type") in ("Planet", "Star") and valid_body
            valid_body = sibling.get("type") in ("Planet", "Star") and valid_body
            valid_body = body.get("semiMajorAxis") is not None and valid_body
            valid_body = sibling.get("semiMajorAxis") is not None and valid_body
            valid_body = body.get("orbitalEccentricity") is not None and valid_body
            valid_body = sibling.get("orbitalEccentricity") is not None and valid_body
            valid_body = body.get("orbitalPeriod") is not None and valid_body
            valid_body = sibling.get("orbitalPeriod") is not None and valid_body
            not_self = body.get("bodyId") != sibling.get("bodyId")
            valid_body = not_self and valid_body

            # if we share teh same parent and not the same body
            if valid_body and str(p1[0]) == str(p2[0]):
                a1 = self.apoapsis(
                    "semiMajorAxis",
                    body.get("semiMajorAxis"),
                    body.get("orbitalEccentricity"),
                )
                a2 = self.apoapsis(
                    "semiMajorAxis",
                    sibling.get("semiMajorAxis"),
                    sibling.get("orbitalEccentricity"),
                )
                p1 = self.periapsis(
                    "semiMajorAxis",
                    body.get("semiMajorAxis"),
                    body.get("orbitalEccentricity"),
                )
                p2 = self.periapsis(
                    "semiMajorAxis",
                    sibling.get("semiMajorAxis"),
                    sibling.get("orbitalEccentricity"),
                )
                r1 = sibling.get("radius")
                r2 = body.get("radius")

                # we want this to be in km
                adistance = (abs(a1 - a2) * 299792.5436) - (r1 + r2)
                pdistance = (abs(p1 - a2) * 299792.5436) - (r1 + r2)
                # print("distance {}, radii = {}".format(distance,r1+r2))
                period = get_synodic_period(body, sibling)

                # its close if less than 100km
                collision = adistance < 0 or pdistance < 0
                close = adistance < 100 or pdistance < 100
                # only considering a 30 day period
                if collision and period < 40:
                    self.add_poi("Tourist", "Collision Flypast", body_code)
                elif close and period < 40:
                    self.add_poi("Tourist", "Close Flypast", body_code)

    @plugin_error
    def close_bodies(self, candidate, bodies, body_code):
        if candidate.get("type") == "Barycentre":
            return

        if (
            candidate.get("semiMajorAxis") is not None
            and candidate.get("orbitalEccentricity") is not None
        ):
            distance = None
            comparitor = None

            if isBinary(candidate) and candidate.get("semiMajorAxis") is not None:
                body = get_sibling(candidate, bodies)

                if body and body.get("semiMajorAxis") is not None:
                    # light seconds

                    d1 = self.apoapsis(
                        "semiMajorAxis",
                        candidate.get("semiMajorAxis"),
                        candidate.get("orbitalEccentricity"),
                    )
                    d2 = self.apoapsis(
                        "semiMajorAxis",
                        body.get("semiMajorAxis"),
                        body.get("orbitalEccentricity"),
                    )
                    # distance = (candidate.get("semiMajorAxis") + body.get("semiMajorAxis")) * 499.005
                    distance = d1 + d2

            if not isBinary(candidate):
                body = bodies.get(get_parent(candidate))
                distance = self.apoapsis(
                    "semiMajorAxis",
                    candidate.get("semiMajorAxis"),
                    candidate.get("orbitalEccentricity"),
                )

            if candidate and body:
                r1 = self.radius_ly(body)
                r2 = self.radius_ly(candidate)
                # to account for things like stars and gas giants
                if distance is not None and r1 is not None and r2 is not None:
                    comparitor = 2 * (r1 + r2)

                if (
                    distance is not None
                    and comparitor is not None
                    and distance < comparitor
                ):
                    if candidate.get("isLandable"):
                        self.add_poi("Tourist", "Close Orbit Landable", body_code)
                    else:
                        self.add_poi("Tourist", "Close Orbit", body_code)

    @plugin_error
    def close_rings(self, candidate, bodies, body_code):
        # need to modify this to look at barycentres too
        binary = False
        parent = bodies.get(get_parent(candidate))
        sibling = get_sibling(candidate, bodies)
        if sibling:
            binary = True
            parent = sibling

        if parent and parent.get("rings") and candidate.get("rings"):
            if candidate.get("semiMajorAxis"):
                apehelion = self.apoapsis(
                    "semiMajorAxis",
                    candidate.get("semiMajorAxis"),
                    candidate.get("orbitalEccentricity") or 0,
                )
                ring_span = get_outer_radius(candidate) + get_outer_radius(parent)

                if binary:
                    distance = (
                        (candidate.get("semiMajorAxis") + parent.get("semiMajorAxis"))
                        * 499.005
                    ) - ring_span
                else:
                    distance = apehelion - ring_span

                if distance < 2 and binary:
                    parent_code = parent.get("name").replace(self.system + " ", "")
                    self.add_poi("Tourist", "Close Ring Proximity", body_code)
                    self.add_poi("Tourist", "Close Ring Proximity", parent_code)

                if distance < 2 and not binary:
                    parent_code = parent.get("name").replace(self.system + " ", "")
                    self.add_poi("Tourist", "Close Ring Proximity", body_code)
                    self.add_poi("Tourist", "Close Ring Proximity", parent_code)

    @plugin_error
    def trojan(self, candidate, bodies):
        # https://forums.frontier.co.uk/threads/hunt-for-trojans.369380/page-7

        if candidate.get("argOfPeriapsis"):
            body_code = candidate.get("name").replace(self.system + " ", "")
            for body in bodies.values():
                # set up some booleans
                if body.get("argOfPeriapsis") and candidate.get("argOfPeriapsis"):
                    not_self = body.get("bodyId") != candidate.get("bodyId")
                    sibling = get_parent(body) == get_parent(candidate)
                    axis_match = body.get("semiMajorAxis") == candidate.get(
                        "semiMajorAxis"
                    )
                    eccentricity_match = body.get(
                        "orbitalEccentricity"
                    ) == candidate.get("orbitalEccentricity")
                    inclination_match = body.get("orbitalInclination") == candidate.get(
                        "orbitalInclination"
                    )
                    period_match = body.get("orbitalPeriod") == candidate.get(
                        "orbitalPeriod"
                    )
                    non_binary = 180 != round(
                        abs(
                            float(body.get("argOfPeriapsis"))
                            - float(candidate.get("argOfPeriapsis"))
                        )
                    )
                    attribute_match = (
                        axis_match
                        and eccentricity_match
                        and inclination_match
                        and period_match
                    )

                    if candidate.get("rings"):
                        ringo = "Ringed "
                    else:
                        ringo = ""

                    if not_self and sibling and attribute_match and non_binary:
                        if candidate.get("subType") in CodexTypes.hv_body_types.keys():
                            self.add_poi(
                                "Tourist",
                                "{}Trojan {}".format(
                                    ringo,
                                    CodexTypes.hv_body_types.get(
                                        candidate.get("subType")
                                    ),
                                ),
                                body_code,
                            )
                        else:
                            self.add_poi(
                                "Tourist",
                                "{}Trojan {}".format(ringo, candidate.get("type")),
                                body_code,
                            )

    @plugin_error
    def ringed_star(self, candidate):
        hasRings = False
        body_code = candidate.get("name").replace(self.system + " ", "")

        if candidate.get("rings") and candidate.get("type") == "Star":
            for ring in candidate.get("rings"):
                if "Ring" in ring.get("name"):
                    hasRings = True

        if hasRings and candidate.get("subType") not in DWARFS:
            self.add_poi("Tourist", "Ringed Star", body_code)

    def has_bio(self, body):
        for category in self.poidata:
            for subcategory in self.poidata[category]:
                for poibody in self.poidata[category][subcategory]:
                    if category == "Biology" and poibody == body:
                        return True
        return False

    def has_oddbio(self, body):
        odyssey_bio = {
            "Aleoida Arcus": {"atmosphere": ["Thin"]},
            "Aleoida Coronamus": {"atmosphere": ["Thin"]},
            "Aleoida Gravis": {"atmosphere": ["Thin"]},
            "Aleoida Laminiae": {"atmosphere": ["Thin"]},
            "Aleoida Spica": {"atmosphere": ["Thin"]},
            "Bacterium Acies": {"atmosphere": ["Neon"]},
            "Bacterium Alcyoneum": {"atmosphere": ["Ammonia"]},
            "Bacterium Aurasus": {"atmosphere": ["CarbonDioxide"]},
            "Bacterium Bullaris": {"atmosphere": ["Methane"]},
            "Bacterium Cerbrus": {"atmosphere": ["SulfurDioxide"]},
            "Bacterium Informem": {"atmosphere": ["Nitrogen"]},
            "Bacterium Nebulus": {"atmosphere": ["Helium"]},
            "Bacterium Omentum": {"atmosphere": ["Thin"], "volcanism": ["Nitrogen"]},
            "Bacterium Scopulum": {"atmosphere": ["Thin"], "volcanism": ["Carbon"]},
            "Bacterium Tela": {
                "atmosphere": ["Thin"],
                "volcanism": ["Helium", "Iron", "Silicate"],
            },
            "Bacterium Verrata": {"atmosphere": ["Thin"], "volcanism": ["Water"]},
            "Bacterium Vesicula": {"atmosphere": ["Argon"]},
            "Bacterium Volu": {"atmosphere": ["Oxygen"]},
            "Cactoida Cortexum": {"atmosphere": ["Thin"]},
            "Cactoida Lapis": {"atmosphere": ["Thin"]},
            "Cactoida Peperatis": {"atmosphere": ["Thin"]},
            "Cactoida Pullulanta": {"atmosphere": ["Thin"]},
            "Cactoida Vermis": {"atmosphere": ["Thin"]},
            "Clypeus Lacrimam": {"atmosphere": ["Thin"]},
            "Clypeus Margaritus": {"atmosphere": ["Thin"]},
            "Clypeus Speculumi": {"atmosphere": ["Thin"], "semiMajorAxis": [">2500"]},
            "Concha Aureolas": {"atmosphere": ["Nitrogen"]},
            "Concha Biconcavis": {"atmosphere": ["Thin"]},
            "Concha Labiata": {"atmosphere": ["CarbonDioxide"]},
            "Concha Renibus": {"atmosphere": ["Thin"]},
            "Electricae Pluma": {
                "atmosphere": ["Helium", "Neon", "Argon"],
                "planet": "Icy Body",
            },
            "Electricae Radialem": {
                "atmosphere": ["Helium", "Neon", "Argon"],
                "planet": "Icy Body",
            },
        }

    def remove_jumponium(self):
        for category in self.poidata.copy():
            if category in ("Jumponium", "GreenSystem"):
                del self.poidata[category]

    """

    This will calculate the maximum value of the Planet and will display it if it is
    higher than 1 million

    Using Matt G's formula https://forums.frontier.co.uk/threads/exploration-value-formulae.232000/

    Ideally we should check if it is first discovered or first mapped but that might not be practical


    """

    @plugin_error
    def high_value(self, body, body_code):
        # no point in displaying stars as they are honked
        subtype = CodexTypes.body_types.get(body.get("subType"))
        if not body.get("type") == "Planet":
            return
        if subtype == "Unknown":
            return

        terraform = body.get("terraformingState") in ("Terraformable", "Terraforming")

        basek = 300
        k = 300
        if subtype in ("Metal Rich Body"):
            basek = 21790
            k = basek
        if subtype in ("Ammonia World"):
            basek = 96932
            k = basek
        if subtype in ("Earthlike World", "Water World"):
            basek = 64831
            k = basek
            if terraform:
                k += 116295

        if subtype in ("Class I Gas Giant"):
            basek = 1656
            k = basek

        if subtype in ("Class II Gas Giant", "High Metal Content World"):
            basek = 9654
            k = basek
            if terraform:
                k += 100677

        if basek == 300 and terraform:
            k = basek + 93328

        def GetBodyValue(
            k,
            mass,
            isFirstDiscoverer=True,
            isMapped=True,
            isFirstMapped=True,
            withEfficiencyBonus=True,
            isOdyssey=True,
            isFleetCarrierSale=False,
        ):
            q = 0.56591828
            mappingMultiplier = 1

            if isMapped:
                if isFirstDiscoverer and isFirstMapped:
                    mappingMultiplier = 3.699622554
                elif isFirstMapped:
                    mappingMultiplier = 8.0956
                else:
                    mappingMultiplier = 3.3333333333

            value = (k + k * q * pow(mass, 0.2)) * mappingMultiplier

            if isMapped:
                if isOdyssey:
                    value += value * 0.3 if value * 0.3 > 555 else 555
                if withEfficiencyBonus:
                    value *= 1.25

            value = max(500, value)
            value *= 2.6 if isFirstDiscoverer else 1
            value *= 0.75 if isFleetCarrierSale else 1

            return round(value)

        # Example usage
        result = GetBodyValue(k, body.get("earthMasses"))
        Debug.logger.debug(f"{body.get('subType')} {body.get('earthMasses')} ${result}")

        if result >= 1000000:
            if terraform:
                self.add_poi(
                    "Planets", f"{body.get('terraformingState')} {subtype}", body_code
                )
            else:
                self.add_poi("Planets", f"{subtype}", body_code)

        return

    @plugin_error
    def satellite_star(self, body, body_code):
        # excluding brown dwarfs
        # if the star is designated a name ending in a digit it is a planet
        # if the star is designated a name ending in a lower case char it is a planet
        name = body.get("name")
        if body.get("type") == "Star" and body.get("subType") not in DWARFS:
            if name[-1].islower() and name[-1].isalpha() and name[-2] == " ":
                self.add_poi("Tourist", "Star as Moon", body_code)
            if name[-1].isdigit() and name[-2] == " ":
                self.add_poi("Tourist", "Star as Planet", body_code)

    @plugin_error
    def deeply_nested(self, body, body_code):
        # true moon moon moons have parents that are planets
        # we are going to count parents that are planets
        # ignore barycenters
        mooncubed = False
        nested = False
        moons = 0
        if body.get("parents") and body.get("type") == "Planet":
            for parent in body.get("parents"):
                if parent.get("Planet"):
                    moons += 1
                if parent.get("Star"):
                    break
            if moons >= 3:
                mooncubed = True

        # The game treats some stars as planets so we want to be able to count those too
        # In this case teh last three digits of the name will be lower case
        # eg. HR 999 1 a b c
        name = body.get("name")
        if len(name) > 6:
            if (
                name[-6:][1::2].isalpha() & name[-6:][1::2].islower()
                and name[-6:][0::2] == "   "
            ):
                nested = True

        if mooncubed:
            self.add_poi("Tourist", "Moon Moon Moon", body_code)

        if nested and not mooncubed:
            self.add_poi("Tourist", "Deeply Nested", body_code)

    @plugin_error
    def green_system(self, bodies):
        mats = [
            "Carbon",
            "Vanadium",
            "Germanium",
            "Cadmium",
            "Niobium",
            "Arsenic",
            "Yttrium",
            "Polonium",
        ]

        jclass = "GreenSystem"

        sysmats = {}
        for body in bodies.values():
            materials = body.get("materials")
            if materials:
                for mat in materials.keys():
                    sysmats[mat] = mat

        if sysmats:
            for target in mats:
                if not sysmats.get(target):
                    jclass = "Jumponium"

        if jclass == "GreenSystem":
            # we will remove jumponium because we will be displaying green
            self.remove_jumponium()

        for body in bodies.values():
            body_code = body.get("name").replace(self.system + " ", "")
            self.jumponium(body, body_code, jclass)

    @plugin_error
    def jumponium(self, body, body_code, jclass):
        materials = body.get("materials")
        basic = False
        standard = False
        premium = False

        volcanism = (
            body.get("volcanismType") and body.get("volcanismType") != "No volcanism"
        )

        hasAtmos = (
            body.get("atmosphereType") and body.get("atmosphereType") != "No atmosphere"
        )
        noAtmos = not hasAtmos

        biology = self.has_bio(body)

        modifier = ""
        if volcanism:
            modifier = "+v"
        if biology and noAtmos:
            modifier = f"{modifier}+b"

        mats = [
            "Carbon",
            "Vanadium",
            "Germanium",
            "Cadmium",
            "Niobium",
            "Arsenic",
            "Yttrium",
            "Polonium",
        ]

        if materials:
            for target in mats:
                if CodexTypes.raw_mats is not None and CodexTypes.raw_mats.get(
                    target.lower()
                ):
                    quantity = CodexTypes.raw_mats.get(target.lower())
                else:
                    quantity = 0
                if materials.get(target) and int(quantity) < 150:
                    self.add_poi(jclass, f"{target}{modifier}", body_code)
                    self.add_ppoi(body_code, "Jumponium", f"{target}{modifier}")

            basic = (
                materials.get("Carbon")
                and materials.get("Vanadium")
                and materials.get("Germanium")
            )
            standard = basic and materials.get("Cadmium") and materials.get("Niobium")
            premium = (
                materials.get("Carbon")
                and materials.get("Germanium")
                and materials.get("Arsenic")
                and materials.get("Niobium")
                and materials.get("Yttrium")
                and materials.get("Polonium")
            )
        if premium:
            self.add_poi(jclass, f"$BoostFSD:Premium{modifier}", body_code)
            return
        if standard:
            self.add_poi(jclass, f"$BoostFSD:Standard{modifier}", body_code)
            return
        if basic:
            self.add_poi(jclass, f"$BoostFSD:Basic{modifier}", body_code)
            return

    @plugin_error
    def rings(self, candidate, body_name):
        body_code = body_name.replace(self.system + " ", "")
        if candidate.get("rings") and not self.bodymismatch(self.system, body_name):
            for ring in candidate.get("rings"):
                ringname = ring.get("name")
                bodymsimatch = self.bodymismatch(self.system, ringname)
                bodymatch = not bodymsimatch
                if bodymatch:
                    if ring.get("name")[-4:] == "Ring":
                        ring_code = ring.get("name").replace(self.system + " ", "")
                        if candidate.get("reserveLevel") and candidate.get(
                            "reserveLevel"
                        ) in ("Pristine", "PristineResources"):
                            self.add_poi(
                                "Ring",
                                "$Rings:"
                                + "Pristine {} Rings".format(ring.get("type")),
                                ring_code,
                            )
                        else:
                            self.add_poi(
                                "Ring",
                                "$Rings:" + "{} Rings".format(ring.get("type")),
                                ring_code,
                            )
                        if ring_code not in self.saadata:
                            self.add_poi("MissingData", "$Rings:Need DSS", ring_code)

                    area = get_area(ring.get("innerRadius"), ring.get("outerRadius"))
                    density = get_density(
                        ring.get("mass"),
                        ring.get("innerRadius"),
                        ring.get("outerRadius"),
                    )

                    if "Ring" in ring.get("name").replace(self.system + " ", ""):
                        if ring.get("outerRadius") > 1000000:
                            self.add_poi("Tourist", "Large Radius Rings", body_code)
                        elif ring.get("innerRadius") < (
                            45935299.69736346 - (1 * 190463268.57872835)
                        ):
                            self.add_poi("Tourist", "Small Radius Rings", body_code)
                        # elif ring.get("outerRadius") - ring.get("innerRadius") < 3500:
                        #    self.add_poi(
                        #        "Tourist", "Thin Rings", body_code)
                        elif density < 0.001:
                            self.add_poi("Tourist", "Low Density Rings", body_code)
                        elif density > 1000:
                            self.add_poi("Tourist", "High Density Rings", body_code)

    def light_seconds(self, tag, value):
        if tag in ("distanceToArrival", "DistanceFromArrivalLS"):
            return value

        # Things measured in meters
        if tag in ("Radius", "SemiMajorAxis"):
            # from journal metres
            return value * 299792000

        # Things measure in kilometres
        if tag == "radius":
            # from journal metres
            return value / 299792

        # Things measure in astronomical units
        if tag == "semiMajorAxis":
            return value * 499.005

        # Things measured in solar radii
        if tag == "solarRadius":
            return value * 2.32061

    def semi_minor_axis(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        minor = sqrt(pow(a, 2) * (1 - pow(e, 2)))
        return minor

    # The focus is the closest point of the orbit
    # return value is in light seconds
    def perihelion(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        focus = a * (1 - e)
        return focus

    def apoapsis(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        return a * (1 + e)

    def periapsis(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        return a * (1 - e)

    def surface_distance(self, d, r1, r2):
        return d - (r1 + r2)

    """
        Standard, Standard+b, Standard+v Standard+v+b
        The longers gets precedence
    """

    def compare_jumponioum(self, v1, v2):
        if len(v1) > len(v2):
            # Debug.logging.debug(f"{v1} vs {v2} = {v1}")
            return v1
        else:
            # Debug.logging.debug(f"{v1} vs {v2} = {v2}")
            return v2

    def fake_biology(self, cmdr, system, x, y, z, planet, count, client):
        bodyname = f"{system} {planet}"

        signal = {
            "timestamp": "2020-07-13T22:37:34Z",
            "event": "SAASignalsFound",
            "BodyName": bodyname,
            "Signals": [
                {
                    "Type": "$SAA_SignalType_Biological;",
                    "Type_Localised": "Biological",
                    "Count": count,
                }
            ],
        }

        self.journal_entry(
            cmdr,
            None,
            system,
            None,
            signal,
            None,
            x,
            y,
            z,
            bodyname,
            None,
            None,
            client,
        )

    """
    This gets called with dashboard updates it is intended to detect when
    we get into the sphere of influence I think but self.system is not always set 
    so we may not be able to switch/
    """

    def updatePlanetData(self, body, latitude, longitude, temperature, gravity):
        self.event = "DashBoard"
        if (body is None) or (latitude is None) or (longitude is None):
            self.body = None
            self.latitude = None
            self.longitude = None
            self.temperature = None
            self.gravity = None
            if self.planetlist_auto:
                if self.planetlist_show:
                    for category in self.lockPlanet.copy():
                        self.switchPlanet(category)
                        if "MissingData" not in self.lock:
                            self.switchPOI(category)
                    self.planetlist_show = False
                    self.visualisePOIData()
                    self.visualisePlanetData()
        else:
            self.body = body
            self.latitude = latitude
            self.longitude = longitude
            self.temperature = temperature
            self.gravity = gravity
            if self.planetlist_auto:
                # don't attempt to switch if self.system is not set.
                if (self.system and not self.planetlist_show) or (
                    self.system
                    and self.planetlist_body != body.replace(self.system + " ", "")
                ):
                    for category in self.lock.copy():
                        if category == "MissingData":
                            continue
                        self.switchPOI(category)
                        self.switchPlanet(category)
                    self.planetlist_show = True
                    self.planetlist_body = body.replace(self.system + " ", "")
                    self.visualisePlanetData()

    #                planetTypes(self.system, body, cmdr, self.getPlanetData).start()

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
        if not self.hidecodex:
            self.journal_entry_wrap(
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
            )

    def journal_entry_wrap(
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
        self.client = client
        self.odyssey = state.get("Odyssey")
        self.event = entry.get("event")
        if state.get("Raw"):
            CodexTypes.raw_mats = state.get("Raw")
        try:
            bodycode = body.replace(system + " ", "")
        except:
            bodycode = "?"

        if entry.get("event") == "Embark":
            if entry.get("Taxi"):
                self.intaxi = True

        if entry.get("event") == "Disembark":
            self.intaxi = False
        # if entry.get("event") == "Docked" and self.intaxi:
        #    self.intaxi = False

        # if entry.get("event") == "SendText" and entry.get("Message"):
        #    ma = entry.get("Message").split(' ')
        #    if len(ma) == 4 and ma[0] == "fake" and ma[1] == "bio":
        #
        #        self.fake_biology(cmdr, system, x, y, z, ma[2], ma[3], client)

        if (
            (entry.get("event") in ("Location", "StartUp", "CarrierJump"))
            or (
                entry.get("event") == "StartJump"
                and entry.get("JumpType") == "Hyperspace"
            )
            or (entry.get("event") == "FSDTarget" and self.intaxi)
            or (
                self.intaxi
                and entry.get("event") == "FSDJump"
                and self.system != system
            )
        ):
            self.system = system
            self.system64 = entry.get("SystemAddress")
            if not self.system64:
                Debug.logger.error("no id64")
                Debug.logger.error(entry)
            if (
                (
                    entry.get("event") == "StartJump"
                    and entry.get("JumpType") == "Hyperspace"
                )
                or (entry.get("event") == "CarrierJump")
                or (entry.get("event") == "FSDJump")
            ):
                self.system = entry.get("StarSystem")
            elif entry.get("event") == "FSDTarget" and self.intaxi:
                self.system = entry.get("Name")
            self.bodies = None
            CodexTypes.fsscount = None
            CodexTypes.bodycount = None
            self.stationdata = {}
            self.settlementdata = {}
            self.poidata = {}
            self.ppoidata = {}
            self.scandata = {}
            self.saadata = {}
            self.fssdata = {}
            self.nfss = 0
            self.fccount = 0
            # Debug.logger.debug("Calling PoiTypes")
            self.allowed = True
            self.logq.clear()
            self.logqueue = True
            self.systemprogress["text"] = ""
            self.systemprogress["fg"] = None
            theme.update(self.systemprogress)

            self.systemprogress.grid_remove()
            poiTypes(self.system, self.system64, cmdr, self.getPOIdata).start()

        if self.system64 != entry.get("SystemAddress"):
            # return if not load in the right system (avoid taxi issue)
            return

        if self.logqueue:
            self.logq.put(
                (
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
                )
            )
            return

        if entry.get("event") in ("Location", "StartUp", "FSDJump", "CarrierJump"):
            # if entry.get("event") in ("FSDJump", "CarrierJump"):
            self.system = system
            if entry.get("SystemAllegiance") in ("Thargoid", "Guardian"):
                self.add_poi(
                    entry.get("SystemAllegiance"),
                    "{} Controlled".format(entry.get("SystemAllegiance")),
                    "",
                )
            self.allowed = True
            self.refreshPOIData(None)

        if (
            entry.get("event") in ("CodexEntry", "ScanOrganic")
            and not entry.get("Category") == "$Codex_Category_StellarBodies;"
        ):
            # Make Organic Scan Look Like a Codex Entry
            if entry.get("event") == "ScanOrganic":
                entry["EntryID"] = CodexTypes.variety_ref.get(entry.get("Variant")).get(
                    "entryid"
                )
                entry["Name_Localised"] = entry.get("Variant_Localised")
                entry["Name"] = entry.get("Variant")
            # really we need to identify the codex types
            self.system = system
            entry_id = entry.get("EntryID")
            codex_name_ref = CodexTypes.name_ref[str(entry_id)]
            if codex_name_ref:
                hud_category = codex_name_ref.get("hud_category")
                english_name = codex_name_ref.get("english_name")
                if hud_category is not None and hud_category != "None":
                    if english_name is None or english_name == "None":
                        english_name = entry.get("Name_Localised")

                    # refresh system panel
                    if body:
                        if hud_category == "Geology":
                            subcat = "$Sites:" + english_name
                        else:
                            subcat = english_name
                            if self.odyssey:
                                if hud_category == "Biology":
                                    if english_name.split(" ")[0] in self.odyssey_bio:
                                        subcat = " ".join(english_name.split(" ")[0:2])
                                if (
                                    codex_name_ref.get("reward") is not None
                                    and int(codex_name_ref.get("reward") / 1000000) != 0
                                ):
                                    subcat = (
                                        "("
                                        + str(
                                            int(codex_name_ref.get("reward") / 1000000)
                                        )
                                        + "$) "
                                        + subcat
                                    )
                                    english_name = (
                                        "("
                                        + str(
                                            int(codex_name_ref.get("reward") / 1000000)
                                        )
                                        + "$) "
                                        + english_name
                                    )

                        self.add_poi(hud_category, subcat, bodycode)
                    else:
                        self.add_poi(hud_category, english_name, "?")

                    # refresh planet panel
                    if body:
                        if (hud_category == "Geology") or (hud_category == "Biology"):
                            if self.odyssey:
                                self.add_ppoi_wsaa(
                                    bodycode,
                                    hud_category,
                                    english_name,
                                    0,
                                    self.latitude,
                                    self.longitude,
                                    True,
                                )

                            else:
                                near_dest = entry.get("NearestDestination").split(":")
                                if near_dest[2].split("=")[0] == "#index":
                                    idx = int(near_dest[2].split("=")[1][:-1])
                                    self.add_ppoi_wsaa(
                                        bodycode,
                                        hud_category,
                                        english_name,
                                        idx,
                                        self.latitude,
                                        self.longitude,
                                        True,
                                    )

                            if hud_category == "Geology":
                                if "Unknown" in self.ppoidata[bodycode]["Geology"]:
                                    if (
                                        len(
                                            self.ppoidata[bodycode]["Geology"][
                                                "Unknown"
                                            ]
                                        )
                                        == 0
                                    ):
                                        self.remove_poi(
                                            "Geology", "$Sites:Unknown", bodycode
                                        )
                                        self.remove_poi(
                                            "MissingData", "$Geology:Unknown", bodycode
                                        )
                                    elif (
                                        len(
                                            self.ppoidata[bodycode]["Geology"][
                                                "Unknown"
                                            ]
                                        )
                                        > 0
                                    ):
                                        self.add_poi(
                                            "Geology", "$Sites:Unknown", bodycode
                                        )
                                        self.add_poi(
                                            "MissingData", "$Geology:Unknown", bodycode
                                        )
                            elif hud_category == "Biology":
                                if "Unknown" in self.ppoidata[bodycode]["Biology"]:
                                    if (
                                        len(
                                            self.ppoidata[bodycode]["Biology"][
                                                "Unknown"
                                            ]
                                        )
                                        == 0
                                    ):
                                        self.remove_poi("Biology", "Unknown", bodycode)
                                        self.remove_poi(
                                            "MissingData", "$Biology:Unknown", bodycode
                                        )
                                    elif (
                                        len(
                                            self.ppoidata[bodycode]["Biology"][
                                                "Unknown"
                                            ]
                                        )
                                        > 0
                                    ):
                                        self.add_poi("Biology", "Unknown", bodycode)
                                        self.add_poi(
                                            "MissingData", "$Biology:Unknown", bodycode
                                        )

                            if (
                                self.planetlist_auto
                                and hud_category not in self.lockPlanet
                            ):
                                self.lockPlanet.append(hud_category)
                            self.refreshPOIData(None)
                            # $SAA_Unknown_Signal:#type=$SAA_SignalType_Geological;:#index=16;
            else:
                self.add_poi("Other", entry.get("Name_Localised"), bodycode)

        if entry.get("event") == "Docked":
            if entry.get("StationType") != "FleetCarrier":
                if entry.get("StationType") in ("CraterOutpost", "CraterPort"):
                    stype = "Planetary Outpost"
                elif entry.get("StationType") in (
                    "Orbis",
                    "Coriolis",
                    "Ocellus",
                    "Outpost",
                    "AsteroidBase",
                ):
                    stype = "Space Station"
                else:
                    stype = None
                if stype is not None:
                    self.stationdata[entry.get("StationName")] = {
                        "type": stype,
                        "economy": self.economies[entry.get("StationEconomy")],
                    }
                    self.refreshPOIData(None)

        if entry.get("event") == "ApproachSettlement":
            self.settlementdata[entry.get("Name")] = {
                "body": entry.get("BodyName"),
                "coords": [entry.get("Latitude"), entry.get("Longitude")],
            }
            self.refreshPOIData(None)

        if entry.get("event") == "FSSDiscoveryScan":
            self.system = system
            CodexTypes.fsscount = entry.get("BodyCount")
            # if not CodexTypes.fsscount:
            #    CodexTypes.fsscount = 0

            self.allowed = True
            self.refreshPOIData(None)

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in (
            "$Fixed_Event_Life_Ring;",
            "$Fixed_Event_Life_Cloud;",
        ):
            if entry.get("SignalName") == "$Fixed_Event_Life_Cloud;":
                self.add_poi("Cloud", "Life Cloud", None)
            else:
                self.add_poi("Cloud", "Life Ring", None)
            self.allowed = True
            self.refreshPOIData(None)

        if (
            entry.get("event") == "FSSSignalDiscovered"
            and entry.get("SignalName") == "Guardian Beacon"
        ):
            self.add_poi("Guardian", "Guardian Beacon", "")
            self.allowed = True
            self.refreshPOIData(None)

        if entry.get("WasDiscovered"):
            self.systemprogress["fg"] = "#348939"

        if entry.get("event") == "FSSSignalDiscovered":
            dovis = False
            # if "NumberStation" in entry.get("SignalName"):
            # self.add_poi("Human", "Unregistered Comms Beacon", None)
            # dovis = True
            # elif "Megaship" in entry.get("SignalName"):
            # self.add_poi("Human", entry.get("SignalName"), None)
            # dovis = True
            # elif ("Class" in entry.get("SignalName")) and ("Vessel" in entry.get("SignalName")):
            # self.add_poi("Human", entry.get("SignalName"), None)
            # dovis = True
            # elif "ListeningPost" in entry.get("SignalName"):
            # self.add_poi("Human", "Listening Post", None)
            # dovis = True
            # elif "CAPSHIP" in entry.get("SignalName"):
            # self.add_poi("Human", "Capital Ship", None)
            # dovis = True
            # elif "Generation Ship" in entry.get("SignalName"):
            # self.add_poi("Human", entry.get("SignalName"), None)
            # dovis = True
            if entry.get("SignalName") in self.stationdata:
                dovis = False
            elif "MULTIPLAYER_SCENARIO" in entry.get("SignalName"):
                dovis = True
                if "MULTIPLAYER_SCENARIO42_TITLE" in entry.get("SignalName"):
                    self.add_poi("Human", "Navigation Beacon", None)
                elif "MULTIPLAYER_SCENARIO14_TITLE" in entry.get("SignalName"):
                    self.add_poi("Ring", "$ConflictZone:Resource Extraction Site", None)
                elif "MULTIPLAYER_SCENARIO77_TITLE" in entry.get("SignalName"):
                    self.add_poi(
                        "Ring", "$ConflictZone:Resource Extraction Site [Low]", None
                    )
                elif "MULTIPLAYER_SCENARIO78_TITLE" in entry.get("SignalName"):
                    self.add_poi(
                        "Ring", "$ConflictZone:Resource Extraction Site [High]", None
                    )
                elif "MULTIPLAYER_SCENARIO79_TITLE" in entry.get("SignalName"):
                    self.add_poi(
                        "Ring", "$ConflictZone:Resource Extraction Site [Danger]", None
                    )
                elif "MULTIPLAYER_SCENARIO80_TITLE" in entry.get("SignalName"):
                    self.add_poi("Ring", "Compromised Navigation Beacon", None)
                else:
                    self.add_poi(
                        "Human", "$ConflictZone:" + entry.get("SignalName"), None
                    )
                    dovis = False
            elif "Warzone_PointRace" in entry.get("SignalName"):
                self.nfss += 1
                dovis = False
            elif "Generation Ship" in entry.get("SignalName"):
                self.add_poi("Human", entry.get("SignalName"), None)
                dovis = True
            elif "ListeningPost" in entry.get("SignalName"):
                self.add_poi("Human", "Listening Post", None)
                dovis = True
            elif "Aftermath" in entry.get("SignalName"):
                self.add_poi("Human", "Distress Call", None)
                dovis = True
            elif "$" in entry.get("SignalName"):
                if self.hidehumandetailed:
                    dovis = False
                else:
                    # self.add_poi("Other", "$Warning:" +
                    #             entry.get("SignalName"), None)

                    dovis = False

            elif entry.get("IsStation"):
                if len(entry.get("SignalName")) > 8:
                    FleetCarrier = (
                        entry.get("SignalName")
                        and entry.get("SignalName")[-4] == "-"
                        and entry.get("SignalName")[-8] == " "
                    )
                elif len(entry.get("SignalName")) == 7:
                    FleetCarrier = (
                        entry.get("SignalName") and entry.get("SignalName")[-4] == "-"
                    )
                else:
                    FleetCarrier = False
                if FleetCarrier:
                    if self.fccount == 0:
                        dovis = True
                    self.remove_poi(
                        "Human", "Fleet Carrier [" + str(self.fccount) + "]", None
                    )
                    self.fccount += 1
                    # self.add_poi("Human", "$FleetCarrier:"+entry.get("SignalName"), None)
                    self.add_poi(
                        "Human", "Fleet Carrier [" + str(self.fccount) + "]", None
                    )
                else:
                    if self.hidehumandetailed:
                        self.add_poi("Human", "Station", None)
                    else:
                        self.add_poi(
                            "Human", "$Station:" + entry.get("SignalName"), None
                        )

                    dovis = True
            else:
                prog = re.compile(
                    "^"
                    + self.system
                    + "( [IVX]+ |[ ]).*$|^[A-Z][A-Z][A-Z][- ][0-9][0-9][0-9] .*$|^.* [A-Z][A-Z][A-Z][- ][0-9][0-9][0-9]$"
                )
                result = prog.match(entry.get("SignalName"))
                prog = re.compile(
                    "^.* [A-Za-z]+-class (Cropper|Hauler|Reformatory|Researcher|Surveyor|Tanker|Traveller)$"
                )
                result = result or prog.match(entry.get("SignalName"))
                if result:
                    Megaship = True
                else:
                    Megaship = False
                if Megaship:
                    if self.hidehumandetailed:
                        self.add_poi("Human", "Megaship", None)
                    else:
                        self.add_poi(
                            "Human", "$Megaship:" + entry.get("SignalName"), None
                        )
                else:
                    if self.hidehumandetailed:
                        self.add_poi("Human", "Installation", None)
                    else:
                        self.add_poi(
                            "Human", "$Installation:" + entry.get("SignalName"), None
                        )

                dovis = True
            self.allowed = True
            dovis = False
            # self.refreshPOIData(None)
            if dovis:
                self.refreshPOIData(None)

        if entry.get("event") == "FSSAllBodiesFound":
            self.system = system
            # CodexTypes.bodycount = CodexTypes.fsscount
            self.allowed = True
            self.refreshPOIData(None)

        if entry.get("event") == "Scan" and entry.get("ScanType") in (
            "Detailed",
            "AutoScan",
        ):
            self.system = system

            # fold the scan data into self.bodies
            if not self.bodies:
                self.bodies = {}
            # only if not a ring or belt
            if entry.get("PlanetClass") or entry.get("StarType"):
                bd = journal2edsm(entry)
                self.bodies[bd.get("bodyId")] = bd
                # Debug.logger.debug(json.dumps(self.bodies, indent=4))

            self.allowed = True
            self.refreshPOIData(None)

        if (
            entry.get("event") == "Scan"
            and entry.get("AutoScan")
            and entry.get("BodyID") == 1
        ):
            self.system = system
            # CodexTypes.parentRadius = self.light_seconds(
            #    "Radius", entry.get("Radius"))
            self.allowed = True

        if entry.get("event") in ("SAASignalsFound", "FSSBodySignals"):
            self.system = system
            # if we arent waiting for new data
            bodyName = entry.get("BodyName")
            bodyVal = bodyName.replace(self.system + " ", "")

            signals = entry.get("Signals")
            for i, v in enumerate(signals):
                found = False
                type = v.get("Type")
                english_name = (
                    type.replace("$SAA_SignalType_", "")
                    .replace("ical;", "y")
                    .replace(";", "")
                )
                if " Ring" in bodyName:
                    cat = "Ring"
                if "$SAA_SignalType_" in type:
                    cat = english_name

                saa_signal = {}
                saa_signal["body"] = entry.get("BodyName")
                saa_signal["hud_category"] = cat
                saa_signal["english_name"] = english_name
                saa_signal["count"] = int(v.get("Count"))
                self.saaq.put(saa_signal)

            if entry.get("Genuses"):
                Debug.logger.debug("Genuses in SAA")
                for genus in entry.get("Genuses"):
                    saa_signal = {}
                    saa_signal["body"] = entry.get("BodyName")
                    saa_signal["hud_category"] = "Biology"
                    saa_signal["english_name"] = CodexTypes.genus.get(
                        genus.get("Genus")
                    )
                    self.poiq.put(saa_signal)

            self.allowed = True
            self.refreshPOIData(None)
            # self.refreshPlanetData(None)

        if entry.get("event") == "SAAScanComplete":
            self.system = system
            saa_signal = {}
            saa_signal["SAAScanComplete"] = {}
            saa_signal["SAAScanComplete"][entry.get("BodyID")] = entry.get("BodyName")
            self.saaq.put(saa_signal)
            self.allowed = True
            self.refreshPOIData(None)

    @classmethod
    def get_codex_names(cls):
        name_ref = {}

        r = requests.get(
            "https://us-central1-canonn-api-236217.cloudfunctions.net/query/codex/ref"
        )

        if r.status_code == requests.codes.ok:
            # for entry in r.json():
            #    name_ref[entry.get("entryid")] = entry
            cls.name_ref = r.json()

            # create a variety lookup for scan_organic
            for entry in cls.name_ref.values():
                cls.variety_ref[entry.get("name")] = entry
        else:
            Debug.logger.error("error in get_codex_names")

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir
        cls.name_ref = {}
        cls.variety_ref = {}

        # we are going to load from the file initially
        file = os.path.join(cls.plugin_dir, "data", "codex_name_ref.json")
        # try:
        with open(file) as json_file:
            cls.name_ref = json.load(json_file)

        # create a variety lookup for scan_organic
        for entry in cls.name_ref.values():
            cls.variety_ref[entry.get("name")] = entry

        codexName(cls.get_codex_names).start()
        # except:
        #    Debug.logger.debug("no config file {}".format(file))

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.hidecodexbtn = tk.IntVar(value=config.get_int("CanonnHideCodex"))
        self.hidehumandetailedbtn = tk.IntVar(
            value=config.get_int("CanonnHideHumanDetailed")
        )
        self.hidemissingdatabtn = tk.IntVar(
            value=config.get_int("CanonnHideMissingData")
        )

        self.hidecodex = self.hidecodexbtn.get()
        self.hidehumandetailed = self.hidehumandetailedbtn.get()
        self.hidemissingdata = self.hidemissingdatabtn.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Label(frame, text="Codex Settings").grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Hide Codex Icons", variable=self.hidecodexbtn).grid(
            row=1, column=0, sticky="NW"
        )
        nb.Checkbutton(
            frame, text="Hide Human Detailed", variable=self.hidehumandetailedbtn
        ).grid(row=1, column=1, sticky="NW")
        nb.Checkbutton(
            frame, text="Hide Missing Data", variable=self.hidemissingdatabtn
        ).grid(row=1, column=2, sticky="NW")

        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set("CanonnHideCodex", self.hidecodexbtn.get())
        config.set("CanonnHideHumanDetailed", self.hidehumandetailedbtn.get())
        config.set("CanonnHideMissingData", self.hidemissingdatabtn.get())

        self.hidecodex = self.hidecodexbtn.get()
        self.hidehumandetailed = self.hidehumandetailedbtn.get()
        self.hidemissingdata = self.hidemissingdatabtn.get()

        # dont check the retval
        self.visualisePOIData()
        self.visualisePlanetData()

    def visible(self):
        noicons = self.hidecodex == 1

        if noicons:
            self.container.grid()
            self.container.grid_remove()
            self.isvisible = False
            return False
        else:
            self.container.grid()
            self.isvisible = True
            return True

        # experimental


class guardianSites:
    # this is no longer used but might come back
    gstypes = {
        "ancient_tiny_001": 2,
        "ancient_tiny_002": 3,
        "ancient_tiny_003": 4,
        "ancient_small_001": 5,
        "ancient_small_002": 6,
        "ancient_small_003": 7,
        "ancient_small_005": 8,
        "ancient_medium_001": 9,
        "ancient_medium_002": 10,
        "ancient_medium_003": 11,
    }

    def __init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):

        example = {
            "timestamp": "2019-10-10T10:23:32Z",
            "event": "ApproachSettlement",
            "Name": "$Ancient_Tiny_003:#index=1;",
            "Name_Localised": "Guardian Structure",
            "SystemAddress": 5079737705833,
            "BodyID": 25,
            "BodyName": "Synuefe LY-I b42-2 C 2",
            "Latitude": 52.681084,
            "Longitude": 115.240822,
        }

        example = {
            "timestamp": "2019-10-10T10:21:36Z",
            "event": "ApproachSettlement",
            "Name": "$Ancient:#index=2;",
            "Name_Localised": "Ancient Ruins (2)",
            "SystemAddress": 5079737705833,
            "BodyID": 25,
            "BodyName": "Synuefe LY-I b42-2 C 2",
            "Latitude": -10.090128,
            "Longitude": 114.505409,
        }

        example = {
            "Name": "$Codex_Ent_Guardian_Data_Logs_Name;",
            "event": "CodexEntry",
            "Region": "$Codex_RegionName_18;",
            "System": "Synuefe ZL-J d10-109",
            "EntryID": 3200200,
            "Category": "$Codex_Category_Civilisations;",
            "timestamp": "2019-10-15T09:19:51Z",
            "SubCategory": "$Codex_SubCategory_Guardian;",
            "SystemAddress": 3755873388891,
            "VoucherAmount": 2500,
            "Name_Localised": "Guardian-Codex",
            "Region_Localised": "Inner Orion Spur",
            "Category_Localised": "Xenologisch",
            "NearestDestination": "$Ancient:#index=2;",
            "SubCategory_Localised": "Guardian-Objekte",
            "NearestDestination_Localised": "Antike Ruinen (2)",
        }

        if entry.get("event") == "CodexEntry":
            siteName = entry.get("NearestDestination")
        else:
            siteName = entry.get("Name")
            self.lat = entry.get("Latitude")
            self.lon = entry.get("Longitude")
            self.body = entry.get("BodyName")

        self.modelreport = None

        if ":" in siteName:
            prefix, suffix = siteName.split(":")
            self.index = self.get_index(siteName)

            if prefix:
                prefix = prefix.lower()[1:]

                if prefix in guardianSites.gstypes:
                    # This is a guardian structure
                    # self.gstype = guardianSites.gstypes.get(prefix)
                    self.gstype = prefix

                    self.modelreport = "gsreports"
                if prefix == "ancient":
                    # this is s guardian ruin
                    # self.gstype = 1
                    self.gstype = "Unknown"
                    self.modelreport = "grreports"

    def get_index(self, value):
        a = []
        a = value.split("#")
        if len(a) == 2:
            dummy, c = value.split("#")
            dummy, index_id = c.split("=")
            index_id = index_id[:-1]
            return index_id


class codexEmitter:

    def __init__(
        self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client, state
    ):

        stellar_bodies = entry.get("Category") == "$Codex_Category_StellarBodies;"
        green_giant = stellar_bodies and "Green" in entry.get("Name")
        excluded = stellar_bodies

        included = not excluded or green_giant

        if included:

            canonn.emitter.post(
                "https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent",
                {
                    "gameState": {
                        "systemName": system,
                        "systemCoordinates": [x, y, z],
                        "bodyName": body,
                        "latitude": lat,
                        "longitude": lon,
                        "clientVersion": client,
                        "isBeta": is_beta,
                        "platform": "PC",
                        "odyssey": state.get("Odyssey"),
                    },
                    "rawEvent": entry,
                    "eventType": entry.get("event"),
                    "cmdrName": cmdr,
                },
            )


def test(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
    Debug.logger.debug("detected test request")

    testentry = {
        "timestamp": "2019-10-10T10:21:36Z",
        "event": "ApproachSettlement",
        "Name": "$Ancient:#index=2;",
        "Name_Localised": "Ancient Ruins (2)",
        "SystemAddress": 5079737705833,
        "BodyID": 25,
        "BodyName": "Synuefe LY-I b42-2 C 2",
        "Latitude": -10.090128,
        "Longitude": 114.505409,
    }

    submit(
        "TestUser",
        False,
        "Synuefe LY-I b42-2",
        814.71875,
        -222.78125,
        -151.15625,
        testentry,
        "Synuefe LY-I b42-2 C 2",
        -10.090128,
        114.505409,
        client,
    )

    testentry = {
        "timestamp": "2019-10-10T10:23:32Z",
        "event": "ApproachSettlement",
        "Name": "$Ancient_Tiny_003:#index=1;",
        "Name_Localised": "Guardian Structure",
        "SystemAddress": 5079737705833,
        "BodyID": 25,
        "BodyName": "Synuefe LY-I b42-2 C 2",
        "Latitude": 52.681084,
        "Longitude": 115.240822,
    }

    submit(
        "TestUser",
        False,
        "Synuefe LY-I b42-2",
        814.71875,
        -222.78125,
        -151.15625,
        testentry,
        "Synuefe LY-I b42-2 C 2",
        52.681084,
        115.240822,
        client,
    )

    testentry = {
        "Name": "$Codex_Ent_Guardian_Data_Logs_Name;",
        "event": "CodexEntry",
        "Region": "$Codex_RegionName_18;",
        "System": "Synuefe ZL-J d10-109",
        "EntryID": 3200200,
        "Category": "$Codex_Category_Civilisations;",
        "timestamp": "2019-10-15T09:19:51Z",
        "SubCategory": "$Codex_SubCategory_Guardian;",
        "SystemAddress": 3755873388891,
        "VoucherAmount": 2500,
        "Name_Localised": "Guardian-Codex",
        "Region_Localised": "Inner Orion Spur",
        "Category_Localised": "Xenologisch",
        "NearestDestination": "$Ancient:#index=2;",
        "SubCategory_Localised": "Guardian-Objekte",
        "NearestDestination_Localised": "Antike Ruinen (2)",
    }

    submit(
        "TestUser",
        False,
        "Synuefe ZL-J d10-109",
        852.65625,
        -51.125,
        -124.84375,
        testentry,
        "Synuefe ZL-J d10-109 E 3",
        -27,
        -148,
        client,
    )

    testentry = {
        "Name": "$Codex_Ent_Guardian_Sentinel_Name;",
        "event": "CodexEntry",
        "Region": "$Codex_RegionName_18;",
        "System": "Synuefe CE-R c21-6",
        "EntryID": 3200600,
        "Category": "$Codex_Category_Civilisations;",
        "timestamp": "2020-04-26T17:28:51Z",
        "SubCategory": "$Codex_SubCategory_Guardian;",
        "SystemAddress": 1734529192634,
        "Name_Localised": "Часовой Стражей",
        "Region_Localised": "Inner Orion Spur",
        "Category_Localised": "Ксенологичские находки",
        "NearestDestination": "$Ancient_Small_001:#index=1;",
        "SubCategory_Localised": "Объекты Стражей",
        "NearestDestination_Localised": "Конструкция Стражей",
    }

    submit(
        "TestUser",
        False,
        "Synuefe CE-R c21-6",
        828.1875,
        -78,
        -105.1875,
        testentry,
        "Synuefe CE-R c21-6 C 1",
        42,
        73,
        client,
    )


def submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client, state):
    codex_entry = entry.get("event") == "CodexEntry"
    approach_settlement = entry.get("event") == "ApproachSettlement"
    guardian_codices = entry.get("EntryID") in [
        3200200,
        3200300,
        3200400,
        3200500,
        3200600,
    ]
    guardian_event = codex_entry and guardian_codices

    if codex_entry:
        codexEmitter(
            cmdr,
            is_beta,
            entry.get("System"),
            x,
            y,
            z,
            entry,
            body,
            lat,
            lon,
            client,
            state,
        )

    if approach_settlement or guardian_event:
        canonn.emitter.post(
            "https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent",
            {
                "gameState": {
                    "systemName": system,
                    "systemCoordinates": [x, y, z],
                    "bodyName": body,
                    "latitude": lat,
                    "longitude": lon,
                    "clientVersion": client,
                    "isBeta": is_beta,
                    "platform": "PC",
                    "odyssey": state.get("Odyssey"),
                },
                "rawEvent": entry,
                "eventType": entry.get("event"),
                "cmdrName": cmdr,
            },
        )

    if entry.get("event") == "SendText" and entry.get("Message") == "codextest":
        test(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)

    gnosis_station = (
        entry.get("StationName") and entry.get("StationName") == "The Gnosis"
    )
    gnosis_fss = (
        entry.get("FSSSignalDiscovered") and entry.get("SignalName") == "The Gnosis"
    )

    if gnosis_station or gnosis_fss:
        Debug.logger.debug("Hey it's The Gnosis!")
        canonn.emitter.post(
            "https://us-central1-canonn-api-236217.cloudfunctions.net/postGnosis",
            {
                "cmdr": cmdr,
                "beta": is_beta,
                "system": system,
                "x": x,
                "y": y,
                "z": z,
                "entry": entry,
                "body": body,
                "lat": lat,
                "lon": lon,
                "client": client,
            },
        )
