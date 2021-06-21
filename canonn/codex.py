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
from canonn.emitter import Emitter
from config import config
from canonn.tooltip import CreateToolTip
from ttkHyperlinkLabel import HyperlinkLabel

import plug
from math import sqrt, pow
import queue


class Queue(queue.Queue):
    '''
    A custom queue subclass that provides a :meth:`clear` method.
    '''

    def clear(self):
        '''
        Clears all items from the queue.
        '''

        with self.mutex:
            unfinished = self.unfinished_tasks - len(self.queue)
            if unfinished <= 0:
                if unfinished < 0:
                    raise ValueError('task_done() called too many times')
                self.all_tasks_done.notify_all()
            self.unfinished_tasks = unfinished
            self.queue.clear()
            self.not_full.notify_all()


def nvl(a, b): return a or b


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


def moon_moon_moon(body):
    # we are going to count parents that are planets
    # ignore barycenters
    moons = 0
    if body.get("parents") and body.get("type") == 'Planet':
        for parent in body.get("parents"):
            if parent.get("Planet"):
                moons += 1
            if parent.get("Star"):
                break
        if moons >= 3:
            return True

    return False


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
        if not p2 == None and p2 == p1 and body.get("bodyId") != candidate.get("bodyId"):
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
            if 'Belt' not in ring.get("name"):
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
        if not outer or 'Belt' not in ring.get("name"):
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
        e["spectralClass"] = "{}{}".format(
            j.get("StarType"), j.get("Subclass"))
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
                j.get("AtmosphereComposition"))
        if j.get("Atmosphere") != "":
            e["atmosphereType"] = j.get("Atmosphere").title()
        else:
            e["atmosphereType"] = "No atmosphere"
        if j.get("TerraformState") == "Terraformable":
            e["terraformingState"] = 'Candidate for terraforming'
        elif j.get("TerraformState") == "Terraforming":
            e["terraformingState"] = 'Terraforming'
        else:
            e["terraformingState"] = 'Not terraformable'
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
    e["rotationalPeriodTidallyLocked"] = (j.get("TidalLock") or False)
    e["name"] = j.get("BodyName")
    if j.get("Rings"):
        e["rings"] = []
        for ring in j.get("Rings"):
            e["rings"].append(
                {"name": ring.get("Name"),
                 "type": ring.get("RingClass").replace("eRingClass_", "").replace("MetalRich", "Metal Rich"),
                 "mass": float(ring.get("MassMT")),
                 "innerRadius": float(ring.get("InnerRad")) / 1000,
                 "outerRadius": float(ring.get("OuterRad")) / 1000
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
    if (T1 == T2):
        return 9999999999
    Tsyn = 1 / abs((1 / T1) - (1 / T2))
    return Tsyn


class codexName(threading.Thread):
    def __init__(self,  callback):
        Debug.logger.debug("initialise codexName Thread")
        threading.Thread.__init__(self)
        self.callback = callback

    def run(self):
        Debug.logger.debug("running codexName")
        self.callback()
        Debug.logger.debug("codexName Callback Complete")


class poiTypes(threading.Thread):
    def __init__(self, system, cmdr, callback):
        # debug("initialise POITYpes Thread")
        threading.Thread.__init__(self)
        self.system = system
        self.cmdr = cmdr
        self.callback = callback

    def run(self):
        # debug("running poitypes")
        self.callback(self.system, self.cmdr)
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


class saaScan():

    def __init__(self):
        Debug.logger.debug("We only use class methods here")

    @classmethod
    def journal_entry(cls, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        if entry.get("event") == "SAASignalsFound":

            canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent", {
                "gameState": {
                    "systemName": system,
                    "systemCoordinates": [x, y, z],
                    "bodyName": body,
                    "clientVersion": client,
                    "isBeta": is_beta,
                    "platform": "PC",
                    "odyssey": state.get("Odyssey")
                },
                "rawEvent": entry,
                "eventType": entry.get("event"),
                "cmdrName": cmdr
            })


class organicScan():

    def __init__(self):
        debug("We only use class methods here")

    @classmethod
    def journal_entry(cls, cmdr, is_beta, system, station, entry, state, x, y, z, body, latitude, longitude, temperature, gravity, client):
        if entry.get("event") in ("ScanOrganic", "SellOrganicData"):

            canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent", {
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
                "cmdrName": cmdr
            })


class CodexTypes():
    tooltips = {
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
        "GreenSystem": "Jumponium Planets"
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

    body_types = {
        'Metal-rich body': 'Metal-Rich Body',
        'Metal rich body': 'Metal-Rich Body',
        'Earth-like world': 'Earthlike World',
        'Earthlike body': 'Earthlike World',
        'Water world': 'Water World',
        'Ammonia world': 'Ammonia World'
    }

    economies = {
        '$economy_None;': 'None',
        '$economy_Agri;': 'Agriculture',
        '$economy_Refinery;': 'Refinery',
        '$economy_Industrial;': 'Industrial',
        '$economy_Colony;': 'Colony',
        '$economy_Extraction;': 'Extraction',
        '$economy_HighTech;': 'High Tech',
        '$economy_Military;': 'Military',
        '$economy_Terraforming;': 'Terraforming',
        '$economy_Service;': 'Service',
        '$economy_Tourism;': 'Tourism',
        '$economy_Undefined;': 'Undefined',
        '$economy_Damaged;': 'Damaged',
        '$economy_Repair;': 'Repair'
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
        "Tussock"
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

    edsm_bodyq = Queue()
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
        self.humandetailedbtn = tk.IntVar(
            value=config.get_int("CanonnHumanDetailed"))
        self.humandetailed = self.humandetailedbtn.get()

        self.frame = Frame(parent)
        theme.update(self.frame)
        self.frame.columnconfigure(0, weight=1)
        self.frame.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)
        self.frame.bind('<<refreshPOIData>>', self.refreshPOIData)
        #self.frame.bind('<<refreshPlanetData>>', self.refreshPlanetData)

        self.container = Frame(self.frame, highlightthickness=1)
        self.container.grid(row=0, column=0, sticky="NSEW")
        self.container.grid_remove()

        self.titlepanel = Frame(self.container)
        self.titlepanel.grid(row=1, column=0, sticky="NSEW")

        self.systempanel = Frame(self.container)
        self.systempanel.grid(row=2, column=0, sticky="NSEW")
        self.systempanel.grid_remove()

        self.systemtitle = Frame(self.titlepanel)
        self.systemtitle.grid(row=0, column=0, sticky="NSEW")
        self.systemtitle.grid_remove()
        self.systemtitle_name = tk.Label(
            self.container, text="?")  # moved to container
        self.systemtitle_name.grid(row=0, column=0, sticky="W")
        self.systemprogress = tk.Label(self.systemtitle, text="?")
        self.systemprogress.grid(
            row=0, column=2, sticky="NSEW")  # moved to next row
        self.systemprogress.grid_remove()

        self.planetpanel = Frame(self.container)
        self.planetpanel.grid(row=3, column=0, sticky="NSEW")
        self.planetpanel.grid_remove()

        self.planettitle = Frame(self.titlepanel)
        self.planettitle.grid(row=1, column=0, sticky="NSEW")
        self.planettitle.grid_remove()

        self.images_prev = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "left_arrow.gif"))
        self.planettitle_prev = tk.Label(
            self.planettitle, image=self.images_prev, cursor="hand2")
        self.planettitle_prev.grid(row=0, column=0, sticky="NSEW")
        self.planettitle_prev.bind(
            '<Button-1>', lambda event, x=-1: self.changeBodyFocus(event, x))
        self.images_next = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "right_arrow.gif"))
        self.planettitle_next = tk.Label(
            self.planettitle, image=self.images_next, cursor="hand2")
        self.planettitle_next.grid(row=0, column=1, sticky="NSEW")
        self.planettitle_next.bind(
            '<Button-1>', lambda event, x=1: self.changeBodyFocus(event, x))
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
        #self.stationPlanetData = {}

        self.temp_poidata = None
        self.temp_edsmdata = None

        #self.cmdrData = {}

        self.images_body = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "planet.gif"))
        self.images_body_auto = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "system_planet.gif"))
        self.images_body_grey = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "system.gif"))
        self.icon_body = tk.Label(
            self.systemtitle, image=self.images_body_auto, text="Body_auto")
        self.icon_body.grid(row=0, column=1)
        self.icon_body.bind("<Button-1>", self.nextBodyMode)
        # self.icon_body.grid_remove()

        self.types = ("Geology", "Cloud", "Anomaly", "Thargoid",
                      "Biology", "Guardian", "Human", "Ring",
                      "None", "Other", "Personal", "Planets",
                      "Tourist", "Jumponium", "GreenSystem")
        k = 0
        for category in self.types:
            self.addimage(category, k+3)
            self.systemlist[category] = Frame(self.systempanel)
            self.systemlist[category].grid(row=k+1, column=0, sticky="W")
            self.systemlist[category].grid_remove()
            k += 1

        self.typesPlanet = ("Geology", "Thargoid", "Biology", "Guardian",
                            "Human", "Other", "Personal", "Tourist",
                            "Jumponium", "GreenSystem")
        k = 0
        for category in self.typesPlanet:
            self.addimage_planet(category, k+4)
            self.planetlist[category] = Frame(self.planetpanel)
            self.planetlist[category].grid(row=k+1, column=0, sticky="W")
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
        Debug.logger.debug(f"nextBodyMode {self.event}")
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
        Debug.logger.debug(f"switchBodyMode {mode}")
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
            if k_selected-1 < 0:
                self.planetlist_body = body_list[len(body_list)-1]
            else:
                self.planetlist_body = body_list[k_selected-1]
        elif inext == 1:
            if k_selected+1 > len(body_list)-1:
                self.planetlist_body = body_list[0]
            else:
                self.planetlist_body = body_list[k_selected+1]

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
                self.labels[category]["image"] = self.images["{}_grey".format(
                    category)]
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
                self.labels[category +
                            "_planet"]["image"] = self.images["{}_grey_planet".format(category)]
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
                self.labels[category +
                            "_planet"]["image"] = self.images[category+"_planet"]
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
        if name[len(name)-7:] == "_planet":
            name = name[:len(name)-7]
            if name not in self.lockPlanet:
                self.labels[name +
                            "_planet"]["image"] = self.images[name+"_planet"]
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
        if name[len(name)-7:] == "_planet":
            name = name[:len(name)-7]
            if name not in self.lockPlanet:
                self.labels[name +
                            "_planet"]["image"] = self.images["{}_grey_planet".format(name)]
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
                self.labels[name]["image"] = self.images["{}_grey".format(
                    name)]
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
        self.images[name] = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "{}.gif".format(name)))
        self.images[grey] = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "{}.gif".format(grey)))
        self.labels[name] = tk.Label(
            self.systemtitle, image=self.images.get(grey), text=name)
        self.labels[name].grid(row=0, column=col)
        self.labels[name].grid_remove()
        self.labels[name].bind("<Enter>", self.enter)
        self.labels[name].bind("<Leave>", self.leave)
        self.labels[name].bind("<Button-1>", lambda event,
                               x=name: self.lockPOIData(x))
        self.labels[name]["image"] = self.images[name]

    def addimage_planet(self, name, col):
        grey = "{}_grey".format(name)
        self.images[name+"_planet"] = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "{}.gif".format(name)))
        self.images[grey+"_planet"] = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "{}.gif".format(grey)))
        self.labels[name+"_planet"] = tk.Label(
            self.planettitle, image=self.images.get(grey+"_planet"), text=name+"_planet")
        self.labels[name+"_planet"].grid(row=0, column=col)
        self.labels[name+"_planet"].grid_remove()
        self.labels[name+"_planet"].bind("<Enter>", self.enter)
        self.labels[name+"_planet"].bind("<Leave>", self.leave)
        self.labels[name+"_planet"].bind("<Button-1>",
                                         lambda event, x=name: self.lockPlanetData(x))
        self.labels[name+"_planet"]["image"] = self.images[name+"_planet"]

    def set_image(self, name, enabled):

        if name not in self.labels:
            return

        forplanet = False
        lock = self.lock
        types = self.types
        if name[len(name)-7:] == "_planet":
            name = name[:len(name)-7]
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
            setting = setting+"_planet"
            name = name+"_planet"

        if enabled and self.labels.get(name):
            self.labels[name]["image"] = self.images[setting]
            self.labels[name].grid()
        else:
            self.labels[name].grid()
            self.labels[name].grid_remove()

    # this seems horribly confused
    def refreshPOIData(self, event):

        Debug.logger.debug(f"refreshPOIData {self.event} {self.waitingPOI}")

        if self.waitingPOI:
            return

        try:
            while not self.edsm_bodyq.empty():
                # only expecting to go around once
                self.temp_edsmdata = self.edsm_bodyq.get()

            while not self.poiq.empty():
                r = self.poiq.get()
                codex_name_ref = CodexTypes.name_ref[str(r.get("entryid"))]
                hud_category = codex_name_ref.get("hud_category")
                english_name = codex_name_ref.get("english_name")
                
                body = r.get("body")
                if body is None:
                    continue
                body_code = body.replace(self.system+" ", '')
                
                if hud_category == "Geology":
                    subcat = "$Sites:"+english_name
                else:
                    subcat = english_name
                    if self.odyssey:
                        if hud_category == "Biology":
                            if english_name.split(" ")[0] in self.odyssey_bio:
                                subcat = " ".join(english_name.split(" ")[0:2])
                        if codex_name_ref.get("reward") is not None:
                            if codex_name_ref.get("reward") > 700000:
                                subcat = "($$$) " + subcat
                                english_name = "($$$) " + english_name
                            elif codex_name_ref.get("reward") > 400000:
                                subcat = "($$) " + subcat
                                english_name = "($$) " + english_name
                            elif codex_name_ref.get("reward") > 200000:
                                subcat = "($) " + subcat
                                english_name = "($) " + english_name
                self.add_poi(hud_category, subcat, body_code)

                if (r.get("latitude") is None) or (r.get("longitude") is None):
                    latlon = None
                else:
                    latlon = "("+str(round(float(r.get("latitude")), 2)) + \
                        "," + str(round(float(r.get("longitude")), 2)) + ")"

                if (r.get("index_id") is None):
                    index = None
                else:
                    index = "#"+str(r.get("index_id"))

                if body_code not in self.ppoidata:
                    self.ppoidata[body_code] = {}
                if hud_category not in self.ppoidata[body_code]:
                    self.ppoidata[body_code][hud_category] = {}
                if english_name not in self.ppoidata[body_code][hud_category]:
                    self.ppoidata[body_code][hud_category][english_name] = []

                if hud_category in ("Geology", "Biology"):
                    if body_code not in self.scandata:
                        self.scandata[body_code] = {}
                    if hud_category not in self.scandata[body_code]:
                        self.scandata[body_code][hud_category] = {}
                    if english_name not in self.scandata[body_code][hud_category]:
                        self.scandata[body_code][hud_category][english_name] = False
                    if (r.get("scanned") == "true"):
                        self.scandata[body_code][hud_category][english_name] = True
                
                    if hud_category == "Biology":
                        k=0
                        if english_name.split(" ")[0] in ("($$$)", "($$)", "($)"):
                            k=1
                        if english_name.split(" ")[k] in self.odyssey_bio:
                            subcat = " ".join(english_name.split(" ")[0:k+2])
                            if subcat not in self.scandata[body_code][hud_category]:
                                self.scandata[body_code][hud_category][subcat] = False
                            if (r.get("scanned") == "true"):
                                self.scandata[body_code][hud_category][subcat] = True
                
                if self.odyssey:
                    if hud_category == "Geology" or hud_category == "Biology":
                        # if index == None:
                        index = "#" + \
                            str(len(self.ppoidata[body_code][hud_category][english_name])+1)
                
                if [None, latlon] in self.ppoidata[body_code][hud_category][english_name]:
                    self.ppoidata[body_code][hud_category][english_name].remove([None, latlon])
                
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
                            self.ppoidata[body_code][hud_category][english_name].remove([index, None])
                            self.ppoidata[body_code][hud_category][english_name].append([index, latlon])
                        continue
                
                if hud_category == "Thargoid" or hud_category == "Guardian":
                    if index == None:
                        continue
                
                self.ppoidata[body_code][hud_category][english_name].append([index, latlon])

            while not self.saaq.empty():
                r = self.saaq.get()
                body = r.get("body")
                body_code = body.replace(self.system+" ", '')

                if body_code not in self.saadata:
                    self.saadata[body_code] = {}
                self.saadata[body_code][r.get("hud_category")] = r.get("count")
                self.remove_poi("Geology", "$Sites:Need SAA", body_code)
                self.remove_poi("Biology", "$Species:Need SAA", body_code)
                self.remove_poi("MissingData", "$Geology:Need SAA", body_code)
                self.remove_poi("MissingData", "$Biology:Need SAA", body_code)
                self.remove_poi("MissingData", "$Rings:Need SAA", body_code)

                if r.get("hud_category") == "Ring":
                    self.add_poi(r.get("hud_category"),
                                 "$Hotspots:"+r.get("english_name"), body_code)
                elif r.get("hud_category") == "Geology":
                    nsites = 0
                    if body_code in self.ppoidata:
                        if "Geology" in self.ppoidata[body_code]:
                            for type in self.ppoidata[body_code]["Geology"]:
                                if self.odyssey:
                                    nsites += len(self.ppoidata[body_code]
                                                  ["Geology"])
                                else:
                                    nsites += len(self.ppoidata[body_code]
                                                  ["Geology"][type])
                    if nsites < r.get("count"):
                        self.add_poi("Geology", "$Sites:Unknown", body_code)
                        self.add_poi(
                            "MissingData", "$Geology:Unknown", body_code)
                        if body_code not in self.ppoidata:
                            self.ppoidata[body_code] = {}
                elif r.get("hud_category") == "Biology":
                    nsites = 0
                    if body_code in self.ppoidata:
                        if "Biology" in self.ppoidata[body_code]:
                            for type in self.ppoidata[body_code]["Biology"]:
                                if self.odyssey:
                                    nsites += len(self.ppoidata[body_code]
                                                  ["Biology"])
                                else:
                                    nsites += len(self.ppoidata[body_code]
                                                  ["Biology"][type])
                    if nsites < r.get("count"):
                        self.add_poi("Biology", "Unknown", body_code)
                        self.add_poi(
                            "MissingData", "$Biology:Unknown", body_code)
                        if body_code not in self.ppoidata:
                            self.ppoidata[body_code] = {}
                self.update_unknown_ppoi(body_code)

            while not self.cmdrq.empty():
                # only expecting to go around once
                temp_cmdrdata = self.cmdrq.get()
                body = temp_cmdrdata.get("body")
                body_code = body.replace(self.system+" ", '')

                if temp_cmdrdata["comment"] is None:
                    name = temp_cmdrdata["category"]
                    index = temp_cmdrdata["index_id"]
                else:
                    name = temp_cmdrdata["comment"]
                    index = None
                latlon = "("+str(round(float(temp_cmdrdata["latitude"]), 2))+","+str(
                    round(float(temp_cmdrdata["longitude"]), 2))+")"
                self.add_poi("Personal", name, body_code)

                if body_code not in self.ppoidata:
                    self.ppoidata[body_code] = {}
                if "Personal" not in self.ppoidata[body_code]:
                    self.ppoidata[body_code]["Personal"] = {}
                if name not in self.ppoidata[body_code]["Personal"]:
                    self.ppoidata[body_code]["Personal"][name] = []
                if [index, latlon] not in self.ppoidata[body_code]["Personal"][name]:
                    self.ppoidata[body_code]["Personal"][name].append(
                        [index, latlon])

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
                                if ("latitude" in s["body"]) and ("longitude" in s["body"]):
                                    latlon = [s["body"].get(
                                        "latitude"), s["body"].get("longitude")]
                                else:
                                    latlon = None
                            else:
                                bodyname = None
                                latlon = None

                            if (s["type"] == "Planetary Outpost"):
                                stype = "Planetary Outpost"
                            elif (s["type"] == None or s["type"] == "Odyssey Settlement"):
                                stype = "Settlement"
                            else:
                                stype = "Space Station"

                            self.stationdata[s["name"]] = {
                                "type": stype, "economy": s["economy"]}
                            if bodyname is not None:
                                self.settlementdata[s["name"]] = {
                                    "body": bodyname, "coords": latlon}

            for station in self.stationdata:
                stype = self.stationdata[station]["type"]
                ecotype = " [" + self.stationdata[station]["economy"] + "]"

                if station in self.settlementdata:
                    bodycode = self.settlementdata[station]["body"].replace(
                        self.system+" ", "")
                    latlon = None
                    if self.settlementdata[station]["coords"] is not None:
                        latlon = "("+str(round(float(self.settlementdata[station]["coords"][0]), 2)) + "," + str(
                            round(float(self.settlementdata[station]["coords"][1]), 2)) + ")"
                    if self.humandetailed:
                        self.add_poi(
                            "Human", "$"+stype+":"+self.stationdata[station]["economy"], bodycode)
                    else:
                        self.add_poi("Human", stype, bodycode)
                    if bodycode is not None:
                        if bodycode not in self.ppoidata:
                            self.ppoidata[bodycode] = {}
                        if "Human" not in self.ppoidata[bodycode]:
                            self.ppoidata[bodycode]["Human"] = {}
                        if station+ecotype not in self.ppoidata[bodycode]["Human"]:
                            self.ppoidata[bodycode]["Human"][station +
                                                             ecotype] = [[None, latlon]]
                else:
                    if self.humandetailed:
                        self.add_poi("Human", "$"+stype+":" +
                                     self.stationdata[station]["economy"], None)
                    else:
                        self.add_poi("Human", stype, None)

            # if self.temp_edsmdata:
            if not self.bodies:
                self.bodies = {}
            # restructure the EDSM data
            if self.temp_edsmdata:
                edsm_bodies = self.temp_edsmdata.get("bodies")
            else:
                edsm_bodies = {}
            if edsm_bodies:
                for b in edsm_bodies:
                    if not "Belt Cluster" in b.get("name"):
                        self.bodies[b.get("bodyId")] = b

            # Debug.logger.debug("self.bodies")
            # Debug.logger.debug(self.bodies)

            if len(self.bodies) > 0:
                # bodies = self.temp_edsmdata.json().get("bodies")
                bodies = self.bodies
                if bodies:
                    CodexTypes.bodycount = len(bodies)
                    if not CodexTypes.fsscount:
                        CodexTypes.fsscount = 0

                    if nvl(CodexTypes.fsscount, 0) > nvl(CodexTypes.bodycount, 0):
                        # self.add_poi("Planets", "Unexplored Bodies", "")
                        if CodexTypes.fsscount > 0:
                            self.systemprogress.grid()
                            # self.systemprogress["text"]="{}%".format(round((float(CodexTypes.bodycount)/float(CodexTypes.fsscount))*100,1))
                            self.systemprogress["text"] = "{}/{}".format(
                                CodexTypes.bodycount, CodexTypes.fsscount)
                    else:

                        self.systemprogress.grid()
                        self.systemprogress.grid_remove()

                    for k in bodies.keys():
                        if bodies.get(k).get("name") == self.system and bodies.get(k).get("type") == "Star":
                            CodexTypes.parentRadius = self.light_seconds(
                                "solarRadius", bodies.get(k).get("solarRadius"))

                        # lets normalise radius between planets and stars
                        if bodies.get(k).get("solarRadius") is not None:
                            bodies[k]["radius"] = bodies.get(
                                k).get("solarRadius")

                    for k in bodies.keys():
                        b = bodies.get(k)
                        # debug(json.dumps(b,indent=4))
                        body_code = b.get("name").replace(self.system+" ", '')
                        body_name = b.get("name")

                        self.sheperd_moon(b, bodies)
                        self.trojan(b, bodies)
                        self.ringed_star(b)
                        self.close_rings(b, bodies, body_code)
                        self.close_bodies(b, bodies, body_code)
                        self.close_flypast(b, bodies, body_code)
                        self.rings(b, body_code)
                        self.green_system(bodies)
                        if moon_moon_moon(b):
                            self.add_poi(
                                "Tourist", "Moon Moon Moon", body_code)

                        # Terraforming
                        if b.get('terraformingState') == 'Candidate for terraforming':
                            if b.get('isLandable'):
                                if not b.get("rings"):
                                    self.add_poi(
                                        "Planets", "Landable Terraformable", body_code)
                                else:
                                    self.add_poi(
                                        "Planets", "Landable Ringed Terraformable", body_code)
                            else:
                                self.add_poi(
                                    "Planets", "Terraformable", body_code)
                        elif b.get('terraformingState') == 'Terraforming':
                            if b.get('isLandable'):
                                if not b.get("rings"):
                                    self.add_poi(
                                        "Planets", "Landable Terraforming", body_code)
                                else:
                                    self.add_poi(
                                        "Planets", "Landable Ringed Terraforming", body_code)
                            else:
                                self.add_poi(
                                    "Planets", "Terraforming", body_code)
                        else:
                            if b.get("rings") and b.get('isLandable'):
                                self.add_poi(
                                    "Tourist", "Landable Ringed Body", body_code)

                        # Landable Volcanism
                        if b.get('type') == 'Planet' and b.get('volcanismType') and b.get('volcanismType') != 'No volcanism' and b.get('isLandable'):
                            self.add_poi(
                                "Geology", "$Volcanism:"+b.get('volcanismType').replace(" Volcanism", ""), body_code)
                            # check SAA signals
                            if body_code not in self.ppoidata:
                                self.add_poi(
                                    "Geology", "$Sites:Need SAA", body_code)
                                self.add_poi(
                                    "MissingData", "$Geology:Need SAA", body_code)
                                self.ppoidata[body_code] = {}
                            else:
                                if "Geology" not in self.ppoidata[body_code]:
                                    self.add_poi(
                                        "Geology", "$Sites:Need SAA", body_code)
                                    self.add_poi(
                                        "MissingData", "$Geology:Need SAA", body_code)

                        # Landable Atmosphere
                        # if b.get('type') == 'Planet' and b.get('atmosphereType') != "No atmosphere" and b.get('isLandable'):
                            # if body_code not in self.ppoidata:
                                # self.add_poi(
                                    # "Biology", "$Species:Need SAA", body_code)
                                # self.add_poi(
                                    # "MissingData", "$Biology:Need SAA", body_code)
                                # self.ppoidata[body_code] = {}
                            # else:
                                # if "Biology" not in self.ppoidata[body_code]:
                                    # self.add_poi(
                                        # "Biology", "$Species:Need SAA", body_code)
                                    # self.add_poi(
                                        # "MissingData", "$Biology:Need SAA", body_code)

                        # water ammonia etc
                        if b.get('subType') in CodexTypes.body_types.keys():
                            self.add_poi("Planets", CodexTypes.body_types.get(
                                b.get('subType')), body_code)

                        # fast orbits
                        if b.get('orbitalPeriod'):
                            if abs(float(b.get('orbitalPeriod'))) <= 0.042:
                                self.add_poi(
                                    "Tourist", 'Fast Orbital Period', body_code)

                        # Ringed ELW etc
                        if b.get('subType') in ('Earthlike body', 'Earth-like world', 'Water world', 'Ammonia world'):
                            if b.get("rings"):
                                self.add_poi("Tourist", 'Ringed {}'.format(
                                    CodexTypes.body_types.get(b.get('subType'))), body_code)
                            if b.get("parents") and b.get("parents")[0] and b.get("parents")[0].get("Planet"):
                                self.add_poi("Tourist", '{} Moon'.format(
                                    CodexTypes.body_types.get(b.get('subType'))), body_code)
                        if b.get('subType') in ('Earthlike body', 'Earth-like world') and b.get('rotationalPeriodTidallyLocked'):
                            self.add_poi(
                                "Tourist", 'Tidal Locked Earthlike Word', body_code)

                        #    Landable high-g (>3g)
                        if b.get('type') == 'Planet' and b.get('gravity') > 3 and b.get('isLandable'):
                            self.add_poi("Tourist", 'High Gravity', body_code)

                        #    Landable large (>18000km radius)
                        if b.get('type') == 'Planet' and b.get('radius') > 18000 and b.get('isLandable'):
                            self.add_poi(
                                "Tourist", 'Large Radius Landable', body_code)

                        #    Moons of moons

                        #    Tiny objects (<300km radius)
                        if b.get('type') == 'Planet' and b.get('radius') < 300 and b.get('isLandable'):
                            self.add_poi(
                                "Tourist", 'Tiny Radius Landable', body_code)

                        #    Fast and non-locked rotation
                        if b.get('type') == 'Planet' and abs(float(b.get('rotationalPeriod'))) < 1 / 24 and not b.get("rotationalPeriodTidallyLocked"):
                            self.add_poi(
                                "Tourist", 'Fast unlocked rotation', body_code)

                        #    High eccentricity
                        if float(b.get("orbitalEccentricity") or 0) > CodexTypes.eccentricity:
                            self.add_poi(
                                "Tourist", 'Highly Eccentric Orbit', body_code)

            else:
                CodexTypes.bodycount = 0

            self.logqueue = False
            while not self.logq.empty():
                (tmpcmdr, tmpis_beta, tmpsystem, tmpstation, tmpentry, tmpstate, tmpx,
                 tmpy, tmpz, tmpbody, tmplat, tmplon, tmpclient) = self.logq.get()
                self.journal_entry(tmpcmdr, tmpis_beta, tmpsystem, tmpstation, tmpentry,
                                   tmpstate, tmpx, tmpy, tmpz, tmpbody, tmplat, tmplon, tmpclient)

        except Exception as e:
            #line = sys.exc_info()[-1].tb_lineno
            self.add_poi("Other", 'Plugin Error', None)
            Debug.logger.error("Plugin Error")
            Debug.logger.exception("Message")

        Debug.logger.debug(f"refreshPOIData end {self.event}")

        self.visualisePOIData()
        self.visualisePlanetData()

    def update_unknown_ppoi(self, body):
        """
        get the maximum index in Geology and Biology category
        and generate unknown for missing index
        """

        Debug.logger.debug(f"update_unknown_ppoi")

        if body not in self.ppoidata:
            return

        if self.odyssey:

            max_category = {}
            min_category = {}
            for category in self.ppoidata[body]:
                if (category == "Geology") or (category == "Biology"):
                    min_category[category] = 0
                    max_category[category] = 0
                    for type in self.ppoidata[body][category]:
                        if type != "Unknown":
                            min_category[category] += 1
                            max_category[category] += 1

            if body in self.saadata:
                for category in self.saadata[body]:
                    if category not in min_category:
                        min_category[category] = 0
                    max_category[category] = self.saadata[body][category]
                    if category not in self.ppoidata[body]:
                        self.ppoidata[body][category] = {}

            for category in max_category:
                if category in self.ppoidata[body]:
                    self.ppoidata[body][category]["Unknown"] = []
                    for i in range(min_category[category]+1, max_category[category]+1):
                        self.ppoidata[body][category]["Unknown"].append(
                            ["#"+str(i), None])
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
                for i in range(1, max_category[category]+1):
                    find_i = False
                    for type in self.ppoidata[body][category]:
                        for poi in self.ppoidata[body][category][type]:
                            if poi[0] == "#"+str(i):
                                find_i = True
                                break
                        if find_i:
                            break
                    if not find_i:
                        if "Unknown" not in self.ppoidata[body][category]:
                            self.ppoidata[body][category]["Unknown"] = []
                        self.ppoidata[body][category]["Unknown"].append(
                            ["#"+str(i), None])

    def remove_ppoi(self, body, hud_category, index):
        """
        remove the index in the hud_category
        and add it in the unknown list for this hud_category
        """

        Debug.logger.debug(f"remove_ppoi {hud_category} {index}")

        if body not in self.ppoidata:
            return

        find_i = False
        for type in self.ppoidata[body][hud_category]:
            if type != "Unknown":
                for i in range(len(self.ppoidata[body][hud_category][type])):
                    poi = self.ppoidata[body][hud_category][type][i]
                    if "#"+index == poi[0]:
                        del self.ppoidata[body][hud_category][type][i]
                        find_i = True
                    if find_i:
                        break
            if find_i:
                break
        if find_i:
            self.ppoidata[body][hud_category]["Unknown"].append(
                ["#"+str(index), None])

    def add_ppoi(self, body, hud_category, type, index, lat, lon, scanned):
        """
        add new index
        check if it exist in the unknown list and remove it
        """

        Debug.logger.debug(
            f"add_ppoi {body} {hud_category} {type} {index} {lat} {lon} {scanned}")

        if body not in self.ppoidata:
            self.ppoidata[body] = {}
        if hud_category not in self.ppoidata[body]:
            self.ppoidata[body][hud_category] = {}
        if "Unknown" not in self.ppoidata[body][hud_category]:
            self.ppoidata[body][hud_category]["Unknown"] = []
        if type not in self.ppoidata[body][hud_category]:
            self.ppoidata[body][hud_category][type] = []

        if body not in self.scandata:
            self.scandata[body] = {}
        if hud_category not in self.scandata[body]:
            self.scandata[body][hud_category] = {}
        if type not in self.scandata[body][hud_category]:
            self.scandata[body][hud_category][type] = False
        if scanned:
            self.scandata[body][hud_category][type] = True
        
        if hud_category == "Biology":
            k=0
            if type.split(" ")[0] in ("($$$)", "($$)", "($)"):
                k=1
            if type.split(" ")[k] in self.odyssey_bio:
                subcat = " ".join(type.split(" ")[0:k+2])
                if subcat not in self.scandata[body][hud_category]:
                    self.scandata[body][hud_category][subcat] = False
                if scanned:
                    self.scandata[body][hud_category][subcat] = True
        
        total_index = 0
        for t in self.ppoidata[body][hud_category]:
            total_index += len(self.ppoidata[body][hud_category][t])

        if self.odyssey:

            if index == 0:
                index = len(self.ppoidata[body][hud_category][type])+1

            self.ppoidata[body][hud_category][type].append(
                ["#"+str(index), "("+str(lat)+","+str(lon)+")"])
            self.update_unknown_ppoi(body)

        else:

            if index > total_index:
                self.ppoidata[body][hud_category][type].append(
                    ["#"+str(index), "("+str(lat)+","+str(lon)+")"])
                self.update_unknown_ppoi(body)
            else:
                find_i = False
                for i in range(len(self.ppoidata[body][hud_category]["Unknown"])):
                    poi = self.ppoidata[body][hud_category]["Unknown"][i]
                    if "#"+str(index) == poi[0]:
                        del self.ppoidata[body][hud_category]["Unknown"][i]
                        find_i = True
                    if find_i:
                        break
                if find_i:
                    self.ppoidata[body][hud_category][type].append(
                        ["#"+str(index), "("+str(lat)+","+str(lon)+")"])

    def getPOIdata(self, system, cmdr):

        if not config.shutting_down:

            Debug.logger.debug(
                f"Getting POI data in thread {self.event} - system = {system}")
            self.waitingPOI = True
            # debug("CodexTypes.waiting = True")
            # first we will clear the queues
            self.logq.clear()
            self.edsm_bodyq.clear()
            self.edsm_stationq.clear()
            self.poiq.clear()
            self.saaq.clear()
            self.cmdrq.clear()

            try:
                url = "https://www.edsm.net/api-system-v1/bodies?systemName={}".format(
                    quote_plus(system.encode('utf8')))

                # debug("request {}:  Active Threads {}".format(
                #    url, threading.activeCount()))

                r = requests.get(url, timeout=30)
                # debug("request complete")
                r.encoding = 'utf-8'
                if r.status_code == requests.codes.ok:
                    # debug("got EDSM Data")
                    temp_edsmdata = r.json()
                    # push edsm data only a queue
                    self.edsm_bodyq.put(temp_edsmdata)
                else:
                    Debug.logger.debug("EDSM Failed")
                    Debug.logger.error("EDSM Failed")
            except:
                Debug.logger.debug("Error getting EDSM data")

            try:
                url = "https://www.edsm.net/api-system-v1/stations?systemName={}".format(
                    quote_plus(system.encode('utf8')))

                # debug("request {}:  Active Threads {}".format(
                #    url, threading.activeCount()))

                r = requests.get(url, timeout=30)
                # debug("request complete")
                r.encoding = 'utf-8'
                if r.status_code == requests.codes.ok:
                    # debug("got EDSM Data")
                    temp_edsmdata = r.json()
                    # push edsm data only a queue
                    self.edsm_stationq.put(temp_edsmdata)
                else:
                    Debug.logger.debug("EDSM Failed")
                    Debug.logger.error("EDSM Failed")
            except:
                Debug.logger.debug("Error getting EDSM data")

            try:
                EDversion = "N"
                if self.odyssey:
                    EDversion = "Y"
                url = "https://us-central1-canonn-api-236217.cloudfunctions.net/query/getSystemPoi?system={}&odyssey={}&cmdr={}".format(
                    quote_plus(system.encode('utf8')), EDversion, cmdr)

                # debug(url)
                # debug("request {}:  Active Threads {}".format(
                #    url, threading.activeCount()))
                headers = {"Accept-Encoding": "gzip, deflate", }
                r = requests.get(url, headers=headers, timeout=30)
                # debug("request complete")
                r.encoding = 'utf-8'
                if r.status_code == requests.codes.ok:
                    # debug("got POI Data")
                    temp_poidata = r.json()

                # push the data ont a queue
                for v in temp_poidata["codex"]:
                    self.poiq.put(v)
                for v in temp_poidata["SAAsignals"]:
                    self.saaq.put(v)
            except:
                debug("Error getting POI data")

            try:
                url = "https://api.canonn.tech/systems?systemName={}".format(
                    quote_plus(system.encode('utf8')))

                r = requests.get(url, timeout=30)
                # debug("request complete")
                r.encoding = 'utf-8'
                if r.status_code == requests.codes.ok:
                    # push canonn data only a queue
                    # self.canonnq.put(r.json())
                    pass
                else:
                    Debug.logger.debug("Canonn Failed")
                    Debug.logger.error("Canonn Failed")
            except:
                Debug.logger.debug("Error getting Canonn data")

            try:
                url = "https://us-central1-canonn-api-236217.cloudfunctions.net/get_cmdr_status?cmdr={}".format(
                    quote_plus(cmdr.encode('utf8')))
                # debug(url)
                # debug("request {}:  Active Threads {}".format(
                #    url, threading.activeCount()))
                r = requests.get(url, timeout=30)
                # debug("request complete")
                r.encoding = 'utf-8'
                if r.status_code == requests.codes.ok:
                    # debug("got planet Data")
                    temp_cmdrdata = r.json()

                # push the data ont a queue
                for v in temp_cmdrdata:
                    if (v["system"] == self.system):
                        self.cmdrq.put(v)
            except:
                debug("Error getting cmdr data")

            self.waitingPOI = False
            Debug.logger.debug("Triggering Event")

            debug("getPOIdata frame.event_generate <<refreshPOIData>>")
            self.frame.event_generate('<<refreshPOIData>>', when='head')
            #self.frame.event_generate('<<refreshPlanetData>>', when='head')

            Debug.logger.debug("Finished getting POI data in thread")

        else:

            Debug.logger.debug("get POI data in shut sown")

        self.refreshPOIData(None)

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

    def visualisePOIData(self):
        # clear it if it exists
        self.cleanPOIPanel()
        self.systempanel.grid_remove()

        Debug.logger.debug(f"visualise POI Data event={self.event}")

        #unscanned = nvl(self.fsscount, 0) > nvl(self.bodycount, 0)

        # we have set an event type that can override waiting
        # if self.event:
        # Debug.logger.debug(f"Allowed event {self.event}")
        # self.waitingPOI = False
        # self.allowed = True
        # self.event = None
        # else:
        # Debug.logger.debug(f"Not allowed event")

        # we may want to try again if the data hasn't been fetched yet
        # if self.waitingPOI or not self.allowed:
        # Debug.logger.debug(f"Still waiting for POI data")
        # else:
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

        # if len(self.ppoidata)>0:
        #    self.icon_body.grid()
        # else:
        #    self.icon_body.grid_remove()

        # if self.poidata or unscanned:

        # self.frame.grid()
        # self.cleanup_poidata()

        nothing = True
        for category in self.poidata:
            self.set_image(category, True)
            nothing = False
        nothing = False
        # else:
        #    self.frame.grid()
        #    self.frame.grid_remove()

        # need to initialise if not exists
        self.systemtitle_name["text"] = self.system

        # print(theme.current)
        #print("THEME", config.get_int('theme'))

        openlist = False
        for category in self.types:
            self.systemlist[category].grid_remove()

            if category in self.poidata:

                self.systemcol1.append(
                    tk.Label(self.systemlist[category], text=category+":"))
                self.systemcol2.append(
                    tk.Label(self.systemlist[category], text=""))
                theme.update(self.systemcol1[-1])
                theme.update(self.systemcol2[-1])
                self.systemcol1[-1].grid(row=len(self.systemcol1),
                                         column=0, columnspan=1, sticky="NW")
                self.systemcol2[-1].grid(row=len(self.systemcol1),
                                         column=1, sticky="NW")

                self.poidata[category] = dict(
                    sorted(self.poidata[category].items()))

                prev_subcategory = "Others"
                isSubcategory = ""
                label = []
                for type in self.poidata[category]:
                    if len(self.poidata[category][type]) == 0:
                        continue

                    self.poidata[category][type] = sorted(
                        self.poidata[category][type])

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
                                n_fss = "WarZone ["+str(self.nfss)+"]"
                        self.systemcol1.append(
                            tk.Label(self.systemlist[category], text="   "+subcategory+":"))
                        self.systemcol2.append(
                            tk.Label(self.systemlist[category], text=n_fss))
                        theme.update(self.systemcol1[-1])
                        theme.update(self.systemcol2[-1])
                        self.systemcol1[-1].grid(row=len(self.systemcol1),
                                                 column=0, columnspan=1, sticky="NW")
                        self.systemcol2[-1].grid(row=len(self.systemcol1),
                                                 column=1, sticky="NW")

                    self.systemcol1.append(
                        tk.Label(self.systemlist[category], text="   "+isSubcategory+name))
                    self.systemcol2.append(tk.Frame(self.systemlist[category]))
                    theme.update(self.systemcol1[-1])
                    theme.update(self.systemcol2[-1])

                    i = 0
                    col = 0
                    for poibody in self.poidata[category][type]:
                        col = ((i % 5)+1)*4
                        row = int(i/5)
                        #row = 0
                        label.append(tk.Label(
                            self.systemcol2[-1], text=poibody))
                        if poibody in self.ppoidata:
                            if config.get_int('theme')==0:
                                label[-1]["fg"] = "blue"
                            if config.get_int('theme')==1:
                                label[-1]["fg"] = "white"
                            label[-1]["cursor"] = "hand2"
                            label[-1].bind('<Button-1>', lambda event,
                                       body=poibody: self.bodyFocus(body))
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
                                            #label.append(tk.Label(self.systemcol2[-1], text="(*)"))
                                            #theme.update(label[-1])
                                            #label[-1].grid(row=row, column=col, sticky="NW")
                                            #col += 1
                        if name == "Unknown":
                            nunk = len(
                                self.ppoidata[poibody][category]["Unknown"])
                            nsites = len(self.ppoidata[poibody][category])
                            if poibody in self.saadata:
                                if category in self.saadata[poibody]:
                                    nsites = self.saadata[poibody][category]
                            label.append(tk.Label(
                                self.systemcol2[-1], text="["+str(nsites-nunk)+"/"+str(nsites)+"]"))
                            theme.update(label[-1])
                            label[-1].grid(row=row, column=col, sticky="NW")
                            col += 1
                        if i < len(self.poidata[category][type]):
                            label.append(tk.Label(self.systemcol2[-1], text=","))
                            theme.update(label[-1])
                            label[-1].grid(row=row, column=col, sticky="N")
                            col += 1

                    self.systemcol1[-1].grid(row=len(self.systemcol1),
                                             column=0, columnspan=1, sticky="NW")
                    self.systemcol2[-1].grid(row=len(self.systemcol1),
                                             column=1, sticky="NW")

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

        self.cleanPlanetPanel()
        self.planettitle.grid_remove()
        self.planetpanel.grid_remove()

        Debug.logger.debug(
            f"visualise Planet Data event={self.event} body={self.planetlist_body}")

        if self.planetlist_body not in self.ppoidata:
            return
            #self.planetlist_body = None
            #self.planetlist_show = False

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

        # refresh ppoi for unknown list
        self.update_unknown_ppoi(self.planetlist_body)

        for category in self.ppoidata[self.planetlist_body]:
            self.set_image(category+"_planet", True)

        self.planettitle_name["text"] = self.planetlist_body

        for category in self.typesPlanet:
            self.planetlist[category].grid_remove()

            if category in self.ppoidata[self.planetlist_body]:

                self.ppoidata[self.planetlist_body][category] = dict(
                    sorted(self.ppoidata[self.planetlist_body][category].items()))
                    
                self.planetcol1.append(
                    tk.Label(self.planetlist[category], text=category+":"))
                self.planetcol2.append(
                    tk.Label(self.planetlist[category], text=""))
                theme.update(self.planetcol1[-1])
                theme.update(self.planetcol2[-1])
                self.planetcol1[-1].grid(row=len(self.planetcol1),
                                         column=0, columnspan=1, sticky="NW")
                self.planetcol2[-1].grid(row=len(self.planetcol1),
                                         column=1, sticky="NW")

                if self.odyssey:
                    if "Unknown" in self.ppoidata[self.planetlist_body][category]:
                        nunk = len(
                            self.ppoidata[self.planetlist_body][category]["Unknown"])
                        nsites = len(
                            self.ppoidata[self.planetlist_body][category])
                        if self.planetlist_body in self.saadata:
                            if category in self.saadata[self.planetlist_body]:
                                nsites = self.saadata[self.planetlist_body][category]
                        self.planetcol2[-1]['text'] = str(round(
                            (nsites-nunk)/nsites*100, 2))+"% [" + str(nsites-nunk) + "/" + str(nsites) + "]"

                label = []
                for type in self.ppoidata[self.planetlist_body][category]:

                    if self.odyssey and type == "Unknown":
                        continue
                    if len(self.ppoidata[self.planetlist_body][category][type]) == 0:
                        continue
                    self.planetcol1.append(
                        tk.Label(self.planetlist[category], text="   "+type))
                    self.planetcol2.append(tk.Frame(self.planetlist[category]))
                    theme.update(self.planetcol1[-1])
                    theme.update(self.planetcol2[-1])
                    if category in ("Geology", "Biology"):
                        if self.planetlist_body in self.scandata:
                            if category in self.scandata[self.planetlist_body]:
                                if type in self.scandata[self.planetlist_body][category]:
                                    if not self.scandata[self.planetlist_body][category][type]:
                                        #self.planetcol1[-1]['fg'] = "red"
                                        #self.planetcol1[-1]['text'] = "   (*) " + type
                                        self.planetcol1[-1]['text'] = "   *" + type

                    self.ppoidata[self.planetlist_body][category][type] = sorted(
                        self.ppoidata[self.planetlist_body][category][type], key=lambda poi: int(nvl(poi[0], "#0")[1:]))

                    i = 0
                    for poi in self.ppoidata[self.planetlist_body][category][type]:
                        col = (i % 10)+1
                        row = int(i/10)
                        if poi[0] is not None:
                            label.append(tk.Label(
                                self.planetcol2[-1], text=poi[0]))
                            if poi[1] is not None:
                                if config.get_int('theme')==0:
                                    label[-1]["fg"] = "blue"
                                if config.get_int('theme')==1:
                                    label[-1]["fg"] = "white"
                                label[-1]["cursor"] = "hand2"
                                label[-1].bind('<Button-1>', lambda event,
                                               latlon=poi[1]: self.activateDestination(latlon))
                            theme.update(label[-1])
                            label[-1].grid(row=row, column=col, sticky="NW")
                        if poi[1] is not None:
                            if poi[0] is None:
                                label.append(tk.Label(
                                    self.planetcol2[-1], text=poi[1]))
                                theme.update(label[-1])
                                label[-1].grid(row=row,
                                               column=col, sticky="NW")
                                if config.get_int('theme')==0:
                                    label[-1]["fg"] = "blue"
                                if config.get_int('theme')==1:
                                    label[-1]["fg"] = "white"
                                label[-1]["cursor"] = "hand2"
                                label[-1].bind('<Button-1>', lambda event,
                                               latlon=poi[1]: self.activateDestination(latlon))
                        i += 1
                    self.planetcol1[-1].grid(row=len(self.planetcol1),
                                             column=0, columnspan=1, sticky="NW")
                    self.planetcol2[-1].grid(row=len(self.planetcol1),
                                             column=1, sticky="NW")

                if self.odyssey:
                    if "Unknown" in self.ppoidata[self.planetlist_body][category]:
                        for iunk in range(nunk):
                            self.planetcol1.append(
                                tk.Label(self.planetlist[category], text="   Unknown"))
                            self.planetcol2.append(
                                tk.Frame(self.planetlist[category]))
                            theme.update(self.planetcol1[-1])
                            theme.update(self.planetcol2[-1])
                            self.planetcol1[-1].grid(row=len(self.planetcol1),
                                                     column=0, columnspan=1, sticky="NW")
                            self.planetcol2[-1].grid(row=len(self.planetcol1),
                                                     column=1, sticky="NW")

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

        #Debug.logger.debug(f"add_poi - {hud_category} {english_name} {body}")

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
        #else:
        #    Debug.logger.debug(f"add_poi - body already in poidata")

    def remove_poi(self, hud_category, english_name, body):

        Debug.logger.debug(
            f"remove_poi - {hud_category} {english_name} {body}")

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

    # def cleanup_poidata(self):
        # # if we have bio or geo then remove Bio Bio and Geo Geo
        # # if we have Jumponium+ and Jumponium then use the best value
        # # We can't simply loop because there is an order of precedence

        # bodies = {}
        # """ for poi in self.poidata:
            # if not bodies.get(poi.get("body")):
                # bodies[poi.get("body")] = {"name": poi.get("body")}
                # bodies[poi.get("body")][poi.get("hud_category")] = 0
            # if not bodies.get(poi.get("body")) and not bodies.get(poi.get("body")).get(poi.get("hud_category")):
                # bodies[poi.get("body")][poi.get("hud_category")] = 0

            # bodies[poi.get("body")][poi.get("hud_category")] += 1

            # if poi.get("hud_category") == "Jumponium":
                # if not bodies[poi.get("body")].get("Jumplevel"):
                # bodies[poi.get("body")]["Jumplevel"] = poi.get(
                # "english_name")
                # else:
                # bodies[poi.get("body")]["Jumplevel"] = self.compare_jumponioum(
                # poi.get("english_name"), bodies[poi.get("body")]["Jumplevel"]) """

        # for k in bodies.keys():
            # body = bodies.get(k)
            # bodyname = body.get("name")

            # for cat in ("Biology", "Geology", "Thargoid", "Guardian"):

                # if body.get(cat) and body.get(cat) > 1:
                # Debug.logging.debug(f"removing {cat}")
                # self.remove_poi(cat, cat, body.get("name"))

            # """ for jumplevel in ("Basic", "Standard", "Premium"):
                # for mod in ("+v", "+b", "+v+b", "+b+v"):
                # if body.get("Jumplevel") and not body.get("Jumplevel") == f"{jumplevel}{mod}":
                # Debug.logging.debug(f"removing {jumplevel}{mod}")
                # self.remove_poi(
                # Jumponium, f"{jumplevel}{mod}", body.get("name")) """

    # this is used to trigger display of merged data

    def sheperd_moon(self, body, bodies):

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

        body_code = body.get("name").replace(self.system+" ", '')
        if body.get("parents"):
            parent = body.get("parents")[0]
            if parent.get("Planet") and bodies.get(parent.get("Planet")) and bodies.get(parent.get("Planet")).get("rings"):

                # If the parent body has a ring
                for ring in bodies.get(parent.get("Planet")).get("rings"):
                    if 'Belt' not in ring.get("name"):
                        density = get_density(ring.get("mass"), ring.get(
                            "innerRadius"), ring.get("outerRadius"))

                        r1 = float(ring.get("outerRadius")) * 1000  # m
                        # convert au to km
                        r2 = float(body.get("semiMajorAxis")) * 149597870691
                        r3 = float(body.get("radius")
                                   or body.get("solarRadius")) * 1000
                        # and the orbit of the body is close to the outer radius

                        if r2 - r3 < r1 + 15000000:
                            self.add_poi("Tourist", 'Shepherd Moon', body_code)

            # gah i need to refector this to avoid duplication
            if parent.get("Star") and bodies.get(parent.get("Star")) and bodies.get(parent.get("Star")).get("rings"):

                # If the parent body has a ring
                for ring in bodies.get(parent.get("Star")).get("rings"):
                    if 'Belt' not in ring.get("name"):
                        density = get_density(ring.get("mass"), ring.get(
                            "innerRadius"), ring.get("outerRadius"))

                        r1 = float(ring.get("outerRadius")) * 1000  # m
                        # convert au to km
                        r2 = float(body.get("semiMajorAxis")) * 149597870691
                        r3 = float(body.get("radius")
                                   or body.get("solarRadius")) * 1000
                        # and the orbit of the body is close to the outer radius

                        if r2 - r3 < r1 + 15000000:
                            self.add_poi(
                                "Tourist", 'Shepherd Planet', body_code)

    def radius_ly(self, body):
        if body.get("type") == 'Star' and body.get("solarRadius"):
            return self.light_seconds('solarRadius', body.get("solarRadius"))
        if body.get("type") == 'Planet' and body.get("radius"):
            return self.light_seconds('radius', body.get("radius"))
        return None

    def close_flypast(self, body, bodies, body_code):
        for sibling in bodies.values():
            p1 = body.get("parents")
            p2 = sibling.get("parents")

            valid_body = True
            valid_body = (p2 and valid_body)
            valid_body = (p1 and valid_body)
            valid_body = (body.get("semiMajorAxis") is not None and valid_body)
            valid_body = (sibling.get("semiMajorAxis")
                          is not None and valid_body)
            valid_body = (body.get("orbitalEccentricity")
                          is not None and valid_body)
            valid_body = (sibling.get("orbitalEccentricity")
                          is not None and valid_body)
            valid_body = (body.get("orbitalPeriod") is not None and valid_body)
            valid_body = (sibling.get("orbitalPeriod")
                          is not None and valid_body)
            not_self = (body.get("bodyId") != sibling.get("bodyId"))
            valid_body = (not_self and valid_body)

            # if we share teh same parent and not the same body
            if valid_body and str(p1[0]) == str(p2[0]):
                a1 = self.apoapsis("semiMajorAxis", body.get(
                    "semiMajorAxis"), body.get("orbitalEccentricity"))
                a2 = self.apoapsis("semiMajorAxis", sibling.get(
                    "semiMajorAxis"), sibling.get("orbitalEccentricity"))
                p1 = self.periapsis("semiMajorAxis", body.get(
                    "semiMajorAxis"), body.get("orbitalEccentricity"))
                p2 = self.periapsis("semiMajorAxis", sibling.get(
                    "semiMajorAxis"), sibling.get("orbitalEccentricity"))
                r1 = sibling.get("radius")
                r2 = body.get("radius")

                # we want this to be in km
                adistance = (abs(a1 - a2) * 299792.5436) - (r1 + r2)
                pdistance = (abs(p1 - a2) * 299792.5436) - (r1 + r2)
                # print("distance {}, radii = {}".format(distance,r1+r2))
                period = get_synodic_period(body, sibling)

                debugval = {
                    "body": body,
                    "distance": {"apoapsis": adistance, "periapsis": pdistance},
                    "orbitalEccentricity": body.get("orbitalEccentricity"),
                    "orbitalInclination": body.get("orbitalEccentricity"),
                    "argOfPeriapsis": body.get("orbitalEccentricity"),
                    "synodicPeriod": period
                }

                # its close if less than 100km
                collision = (adistance < 0 or pdistance < 0)
                close = (adistance < 100 or pdistance < 100)
                # only considering a 30 day period
                if collision and period < 40:
                    self.add_poi("Tourist", 'Collision Flypast', body_code)

                elif close and period < 40:
                    self.add_poi("Tourist", 'Close Flypast', body_code)

    def close_bodies(self, candidate, bodies, body_code):
        if candidate.get("semiMajorAxis") is not None and candidate.get("orbitalEccentricity") is not None:
            distance = None

            if isBinary(candidate) and candidate.get("semiMajorAxis") is not None:
                body = get_sibling(candidate, bodies)

                if body and body.get("semiMajorAxis") is not None:
                    # light seconds

                    d1 = self.apoapsis("semiMajorAxis", candidate.get(
                        "semiMajorAxis"), candidate.get("orbitalEccentricity"))
                    d2 = self.apoapsis("semiMajorAxis", body.get(
                        "semiMajorAxis"), body.get("orbitalEccentricity"))
                    # distance = (candidate.get("semiMajorAxis") + body.get("semiMajorAxis")) * 499.005
                    distance = d1 + d2

            if not isBinary(candidate):
                body = bodies.get(get_parent(candidate))
                distance = self.apoapsis("semiMajorAxis", candidate.get(
                    "semiMajorAxis"), candidate.get("orbitalEccentricity"))

            if candidate and body:
                r1 = self.radius_ly(body)
                r2 = self.radius_ly(candidate)
                # to account for things like stars and gas giants
                if distance is not None and r1 is not None and r2 is not None:
                    comparitor = 2 * (r1 + r2)

                if distance is not None and distance < comparitor:

                    if candidate.get("isLandable"):
                        self.add_poi(
                            "Tourist", 'Close Orbit Landable', body_code)
                    else:
                        self.add_poi("Tourist", 'Close Orbit', body_code)

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

                apehelion = self.apoapsis("semiMajorAxis", candidate.get(
                    "semiMajorAxis"), candidate.get("orbitalEccentricity") or 0)
                ring_span = get_outer_radius(
                    candidate) + get_outer_radius(parent)

                if binary:
                    distance = ((candidate.get("semiMajorAxis") +
                                 parent.get("semiMajorAxis")) * 499.005) - ring_span
                else:
                    distance = apehelion - ring_span

                if distance < 2 and binary:
                    parent_code = parent.get(
                        "name").replace(self.system+" ", '')
                    self.add_poi("Tourist", "Close Ring Proximity", body_code)
                    self.add_poi(
                        "Tourist", "Close Ring Proximity", parent_code)

                if distance < 2 and not binary:
                    parent_code = parent.get(
                        "name").replace(self.system+" ", '')
                    self.add_poi("Tourist", "Close Ring Proximity", body_code)
                    self.add_poi(
                        "Tourist", "Close Ring Proximity", parent_code)

    def trojan(self, candidate, bodies):
        # https://forums.frontier.co.uk/threads/hunt-for-trojans.369380/page-7

        if candidate.get("argOfPeriapsis"):
            body_code = candidate.get("name").replace(self.system+" ", '')
            for body in bodies.values():
                # set up some booleans
                if body.get("argOfPeriapsis") and candidate.get("argOfPeriapsis"):
                    not_self = (body.get("bodyId") != candidate.get("bodyId"))
                    sibling = (get_parent(body) == get_parent(candidate))
                    axis_match = (body.get("semiMajorAxis") ==
                                  candidate.get("semiMajorAxis"))
                    eccentricity_match = (
                        body.get("orbitalEccentricity") == candidate.get("orbitalEccentricity"))
                    inclination_match = (
                        body.get("orbitalInclination") == candidate.get("orbitalInclination"))
                    period_match = (body.get("orbitalPeriod") ==
                                    candidate.get("orbitalPeriod"))
                    non_binary = (180 != abs(
                        float(body.get("argOfPeriapsis")) - float(candidate.get("argOfPeriapsis"))))
                    attribute_match = (
                        axis_match and eccentricity_match and inclination_match and period_match)

                    if candidate.get("rings"):
                        ringo = "Ringed "
                    else:
                        ringo = ""

                    if not_self and sibling and attribute_match and non_binary:
                        if candidate.get('subType') in CodexTypes.body_types.keys():
                            self.add_poi("Tourist", "{}Trojan {}".format(
                                ringo, CodexTypes.body_types.get(candidate.get('subType'))), body_code)
                        else:
                            self.add_poi("Tourist", "{}Trojan {}".format(
                                ringo, candidate.get("type")), body_code)

    def ringed_star(self, candidate):
        hasRings = False
        body_code = candidate.get("name").replace(self.system+" ", '')

        if candidate.get("rings") and candidate.get('type') == 'Star':
            for ring in candidate.get("rings"):
                if "Ring" in ring.get("name"):
                    hasRings = True

        if hasRings:
            self.add_poi("Tourist", "Ringed Star", body_code)

    def has_bio(self, body):
        for category in self.poidata:
            for subcategory in self.poidata[category]:
                for poibody in self.poidata[category][subcategory]:
                    if category == 'Biology' and poibody == body:
                        return True
        return False

    def remove_jumponium(self):
        for category in self.poidata.copy():
            if category in ('Jumponium', 'GreenSystem'):
                del self.poidata[category]

    def green_system(self, bodies):
        mats = [
            "Carbon",
            "Vanadium",
            "Germanium",
            "Cadmium",
            "Niobium",
            "Arsenic",
            "Yttrium",
            "Polonium"
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
            body_code = body.get("name").replace(self.system+" ", '')
            self.jumponium(body, body_code, jclass)

    def jumponium(self, body, body_code, jclass):

        materials = body.get("materials")
        basic = False
        standard = False
        premium = False

        volcanism = (body.get('volcanismType') and body.get(
            'volcanismType') != 'No volcanism')

        hasAtmos=(body.get("atmosphereType") and body.get("atmosphereType") != "No atmosphere")
        noAtmos=(not hasAtmos)

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
            "Polonium"
        ]

        if materials:
            for target in mats:
                if CodexTypes.raw_mats.get(target.lower()):
                    quantity = CodexTypes.raw_mats.get(target.lower())
                else:
                    quantity = 0
                if materials.get(target) and int(quantity) < 150:
                    self.add_poi(jclass, f"{target}{modifier}", body_code)

            basic = (materials.get("Carbon") and materials.get(
                "Vanadium") and materials.get("Germanium"))
            standard = (basic and materials.get("Cadmium")
                        and materials.get("Niobium"))
            premium = (materials.get("Carbon") and materials.get("Germanium") and materials.get(
                "Arsenic") and materials.get("Niobium") and materials.get("Yttrium") and materials.get("Polonium"))
        if premium:
            self.add_poi(jclass, f"$BoostFSD:Premium{modifier}", body_code)
            return
        if standard:
            self.add_poi(jclass, f"$BoostFSD:Standard{modifier}", body_code)
            return
        if basic:
            self.add_poi(jclass, f"$BoostFSD:Basic{modifier}", body_code)
            return

    def rings(self, candidate, body_code):
        if candidate.get("rings"):
            for ring in candidate.get("rings"):
                if ring.get("name")[-4:] == "Ring":
                    if candidate.get("reserveLevel") and candidate.get("reserveLevel") in ("Pristine", "PristineResources"):
                        self.add_poi(
                            "Ring", "$Rings:"+"Pristine {} Rings".format(ring.get("type")), body_code)
                    else:
                        self.add_poi(
                            "Ring", "$Rings:"+"{} Rings".format(ring.get("type")), body_code)
                    self.add_poi("MissingData", "$Rings:Need SAA", body_code)
                area = get_area(ring.get("innerRadius"),
                                ring.get("outerRadius"))
                density = get_density(ring.get("mass"), ring.get(
                    "innerRadius"), ring.get("outerRadius"))

                if "Ring" in ring.get("name").replace(self.system+" ", ''):
                    if ring.get("outerRadius") > 1000000:
                        self.add_poi(
                            "Tourist", "Large Radius Rings", body_code)
                    elif ring.get("innerRadius") < (45935299.69736346 - (1 * 190463268.57872835)):
                        self.add_poi(
                            "Tourist", "Small Radius Rings", body_code)
                    # elif ring.get("outerRadius") - ring.get("innerRadius") < 3500:
                    #    self.add_poi(
                    #        "Tourist", "Thin Rings", body_code)
                    elif density < 0.005:
                        self.add_poi("Tourist", "Low Density Rings", body_code)
                    elif density > 1000:
                        self.add_poi(
                            "Tourist", "High Density Rings", body_code)

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
            Debug.logging.debug(f"{v1} vs {v2} = {v1}")
            return v1
        else:
            Debug.logging.debug(f"{v1} vs {v2} = {v2}")
            return v2

    def fake_biology(self, cmdr, system, x, y, z, planet, count, client):
        bodyname = f"{system} {planet}"

        signal = {
            "timestamp": "2020-07-13T22:37:34Z",
            "event": "SAASignalsFound",
            "BodyName": bodyname,
            "Signals": [
                {"Type": "$SAA_SignalType_Biological;",
                 "Type_Localised": "Biological",
                 "Count": count}]
        }

        self.journal_entry(cmdr, None, system, None, signal,
                           None, x, y, z, bodyname, None, None, client)

    def updatePlanetData(self, body, latitude, longitude, temperature, gravity):
        self.event = "DashBoard"
        if ((body is None) or (latitude is None) or (longitude is None)):
            self.body = None
            self.latitude = None
            self.longitude = None
            self.temperature = None
            self.gravity = None
            if self.planetlist_auto:
                if self.planetlist_show:
                    tmplock = self.lockPlanet.copy()
                    for category in tmplock:
                        self.switchPlanet(category)
                        self.switchPOI(category)
                    self.planetlist_show = False
                    self.visualisePlanetData()
        else:
            self.body = body
            self.latitude = latitude
            self.longitude = longitude
            self.temperature = temperature
            self.gravity = gravity
            if self.planetlist_auto:
                if (not self.planetlist_show) or (self.planetlist_body != body.replace(self.system+" ", '')):
                    tmplock = self.lock.copy()
                    for category in tmplock:
                        self.switchPOI(category)
                        self.switchPlanet(category)
                    self.planetlist_show = True
                    self.planetlist_body = body.replace(self.system+" ", '')
                    self.visualisePlanetData()
#                planetTypes(self.system, body, cmdr, self.getPlanetData).start()

    def journal_entry(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        if not self.hidecodex:
            self.journal_entry_wrap(
                cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client)

    def journal_entry_wrap(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):

        self.odyssey = state.get("Odyssey")
        self.event = entry.get("event")
        if state.get("Raw"):
            CodexTypes.raw_mats = state.get("Raw")
        try:
            bodycode = body.replace(system+" ", '')
        except:
            bodycode = ""

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

        if (entry.get("event") in ("Location", "StartUp", "CarrierJump")) or (entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace") or (entry.get("event") == "FSDTarget" and self.intaxi):
            self.system = system
            self.system64 = entry.get("SystemAddress")
            if (entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace") or (entry.get("event") == "CarrierJump"):
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
            Debug.logger.debug("Calling PoiTypes")
            self.allowed = True
            self.logq.clear()
            self.logqueue = True
            poiTypes(self.system, cmdr, self.getPOIdata).start()

        if self.system64 != entry.get("SystemAddress"):
            # return if not load in the right system (avoid taxi issue)
            return

        if self.logqueue:
            self.logq.put((cmdr, is_beta, system, station, entry,
                           state, x, y, z, body, lat, lon, client))
            return

        if entry.get("event") in ("Location", "StartUp", "FSDJump", "CarrierJump"):
            # if entry.get("event") in ("FSDJump", "CarrierJump"):
            self.system = system
            if entry.get("SystemAllegiance") in ("Thargoid", "Guardian"):
                self.add_poi(entry.get("SystemAllegiance"), "{} Controlled".format(
                    entry.get("SystemAllegiance")), "")
            self.allowed = True
            self.refreshPOIData(None)

        if entry.get("event") == "CodexEntry" and not entry.get("Category") == '$Codex_Category_StellarBodies;':
            # really we need to identify the codex types
            self.system = system
            entry_id = entry.get("EntryID")
            codex_name_ref = CodexTypes.name_ref[str(entry_id)]
            if codex_name_ref:
                hud_category = codex_name_ref.get("hud_category")
                english_name = codex_name_ref.get("english_name")
                if hud_category is not None and hud_category != 'None':
                    if english_name is None or english_name == 'None':
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
                                if codex_name_ref.get("reward") is not None:
                                    if codex_name_ref.get("reward") > 700000:
                                        subcat = "($$$) " + subcat
                                        english_name = "($$$) " + english_name
                                    elif codex_name_ref.get("reward") > 400000:
                                        subcat = "($$) " + subcat
                                        english_name = "($$) " + english_name
                                    elif codex_name_ref.get("reward") > 200000:
                                        subcat = "($) " + subcat
                                        english_name = "($) " + english_name
                            
                        self.add_poi(hud_category, subcat, bodycode)
                    else:
                        self.add_poi(hud_category, english_name, "")

                    # refresh planet panel
                    if body:
                        if (hud_category == "Geology") or (hud_category == "Biology"):

                            if self.odyssey:
                                self.add_ppoi(bodycode, hud_category, english_name, 0, round(
                                    self.latitude, 2), round(self.longitude, 2), True)

                            else:
                                near_dest = entry.get(
                                    "NearestDestination").split(":")
                                if (near_dest[2].split("=")[0] == "#index"):
                                    idx = int(near_dest[2].split("=")[1][:-1])
                                    self.add_ppoi(bodycode, hud_category, english_name, idx, round(
                                        self.latitude, 2), round(self.longitude, 2), True)

                            if hud_category == "Geology":
                                if "Unknown" in self.ppoidata[bodycode]["Geology"]:
                                    if len(self.ppoidata[bodycode]["Geology"]["Unknown"]) == 0:
                                        self.remove_poi(
                                            "Geology", "$Sites:Unknown", bodycode)
                                        self.remove_poi(
                                            "MissingData", "$Geology:Unknown", bodycode)
                                    elif len(self.ppoidata[bodycode]["Geology"]["Unknown"]) > 0:
                                        self.add_poi(
                                            "Geology", "$Sites:Unknown", bodycode)
                                        self.add_poi(
                                            "MissingData", "$Geology:Unknown", bodycode)
                            elif hud_category == "Biology":
                                if "Unknown" in self.ppoidata[bodycode]["Biology"]:
                                    if len(self.ppoidata[bodycode]["Biology"]["Unknown"]) == 0:
                                        self.remove_poi(
                                            "Biology", "Unknown", bodycode)
                                        self.remove_poi(
                                            "MissingData", "$Biology:Unknown", bodycode)
                                    elif len(self.ppoidata[bodycode]["Biology"]["Unknown"]) > 0:
                                        self.add_poi(
                                            "Biology", "Unknown", bodycode)
                                        self.add_poi(
                                            "MissingData", "$Biology:Unknown", bodycode)

                            if self.planetlist_auto and hud_category not in self.lockPlanet:
                                self.lockPlanet.append(hud_category)
                            self.refreshPOIData(None)
                            # $SAA_Unknown_Signal:#type=$SAA_SignalType_Geological;:#index=16;
            else:
                self.add_poi('Other', entry.get("Name_Localised"), bodycode)

        if entry.get("event") == "Docked":
            if entry.get("StationType") != "FleetCarrier":
                if entry.get("StationType") in ("CraterOutpost", "CraterPort"):
                    stype = "Planetary Outpost"
                elif entry.get("StationType") in ("Orbis", "Coriolis", "Ocellus", "Outpost", "AsteroidBase"):
                    stype = "Space Station"
                else:
                    stype = None
                if stype is not None:
                    self.stationdata[entry.get("StationName")] = {
                        "type": stype, "economy": self.economies[entry.get("StationEconomy")]}
                    self.refreshPOIData(None)

        if entry.get("event") == "ApproachSettlement":
            self.settlementdata[entry.get("Name")] = {"body": entry.get(
                "BodyName"), "coords": [entry.get("Latitude"), entry.get("Longitude")]}
            self.refreshPOIData(None)

        if entry.get("event") == "FSSDiscoveryScan":
            self.system = system
            CodexTypes.fsscount = entry.get("BodyCount")
            # if not CodexTypes.fsscount:
            #    CodexTypes.fsscount = 0

            self.allowed = True
            self.refreshPOIData(None)

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in ('$Fixed_Event_Life_Ring;', '$Fixed_Event_Life_Cloud;'):
            if entry.get("SignalName") == '$Fixed_Event_Life_Cloud;':
                self.add_poi("Cloud", "Life Cloud", None)
            else:
                self.add_poi("Cloud", "Life Ring", None)
            self.allowed = True
            self.refreshPOIData(None)

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") == 'Guardian Beacon':
            self.add_poi("Guardian", "Guardian Beacon", "")
            self.allowed = True
            self.refreshPOIData(None)

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
                    self.add_poi("Ring", "$ConflictZone:Resource Extraction Site [Low]", None)
                elif "MULTIPLAYER_SCENARIO78_TITLE" in entry.get("SignalName"):
                    self.add_poi("Ring", "$ConflictZone:Resource Extraction Site [High]", None)
                elif "MULTIPLAYER_SCENARIO79_TITLE" in entry.get("SignalName"):
                    self.add_poi("Ring", "$ConflictZone:Resource Extraction Site [Danger]", None)
                elif "MULTIPLAYER_SCENARIO80_TITLE" in entry.get("SignalName"):
                    self.add_poi("Ring", "Compromised Navigation Beacon", None)
                else:
                    self.add_poi("Human", "$ConflictZone:" + entry.get("SignalName"), None)
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
                if self.humandetailed:
                    #self.add_poi("Other", "$Warning:" +
                    #             entry.get("SignalName"), None)
                    print("WARNING : ", entry)
                    dovis = False
                else:
                    dovis = False
            elif entry.get("IsStation"):
                if len(entry.get("SignalName")) > 8:
                    FleetCarrier = (entry.get("SignalName") and entry.get(
                        "SignalName")[-4] == '-' and entry.get("SignalName")[-8] == ' ')
                elif len(entry.get("SignalName")) == 7:
                    FleetCarrier = (entry.get("SignalName")
                                    and entry.get("SignalName")[-4] == '-')
                else:
                    FleetCarrier = False
                if FleetCarrier:
                    if self.fccount == 0:
                        dovis = True
                    self.remove_poi("Human", "Fleet Carrier ["+str(self.fccount)+"]", None)
                    self.fccount += 1
                    #self.add_poi("Human", "$FleetCarrier:"+entry.get("SignalName"), None)
                    self.add_poi("Human", "Fleet Carrier ["+str(self.fccount)+"]", None)
                else:
                    if self.humandetailed:
                        self.add_poi("Human", "$Station:" + entry.get("SignalName"), None)
                    else:
                        self.add_poi("Human", "Station", None)
                    dovis = True
            else:
                # ^HIP 454-4( [IVX]+ |[ ]).*$|^[A-Z][A-Z][A-Z][- ][0-9][0-9][0-9] .*$|^.* [A-Z][A-Z][A-Z][- ][0-9][0-9][0-9]$
                prog = re.compile(
                    "^"+self.system+"( [IVX]+ |[ ]).*$|^[A-Z][A-Z][A-Z][- ][0-9][0-9][0-9] .*$|^.* [A-Z][A-Z][A-Z][- ][0-9][0-9][0-9]$")
                result = prog.match(entry.get("SignalName"))
                prog = re.compile(
                    "^.* [A-Za-z]+-class (Cropper|Hauler|Reformatory|Researcher|Surveyor|Tanker|Traveller)$")
                result = result or prog.match(entry.get("SignalName"))
                if result:
                    Megaship = True
                else:
                    Megaship = False
                if Megaship:
                    if self.humandetailed:
                        self.add_poi("Human", "$Megaship:" +
                                     entry.get("SignalName"), None)
                    else:
                        self.add_poi("Human", "Megaship", None)
                else:
                    if self.humandetailed:
                        self.add_poi("Human", "$Installation:" +
                                     entry.get("SignalName"), None)
                    else:
                        self.add_poi("Human", "Installation", None)
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

        if entry.get("event") == "Scan" and entry.get("ScanType") in ("Detailed", "AutoScan"):
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

        if entry.get("event") == "Scan" and entry.get("AutoScan") and entry.get("BodyID") == 1:
            self.system = system
            CodexTypes.parentRadius = self.light_seconds(
                "Radius", entry.get("Radius"))
            self.allowed = True

        if entry.get("event") == "SAASignalsFound":
            self.system = system
            # if we arent waiting for new data
            bodyName = entry.get("BodyName")
            bodyVal = bodyName.replace(self.system+" ", '')

            signals = entry.get("Signals")
            for i, v in enumerate(signals):
                found = False
                type = v.get("Type")
                english_name = type.replace("$SAA_SignalType_", "").replace(
                    "ical;", "y").replace(";", "")
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

            self.refreshPOIData(None)
            # self.refreshPlanetData(None)
            self.allowed = True

    @classmethod
    def get_codex_names(cls):
        name_ref = {}

        r = requests.get(
            "https://us-central1-canonn-api-236217.cloudfunctions.net/query/codex/ref")

        if r.status_code == requests.codes.ok:
            #for entry in r.json():
            #    name_ref[entry.get("entryid")] = entry
            cls.name_ref = r.json()
        else:
            Debug.logger.error("error in get_codex_names")

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir
        cls.name_ref = {}

        file = os.path.join(cls.plugin_dir, 'data', 'codex_name_ref.json')
        # try:
        with open(file) as json_file:
            cls.name_ref = json.load(json_file)

        # make this a dict
        #for entry in name_ref_array:
        #    cls.name_ref[entry.get("entryid")] = entry

        codexName(cls.get_codex_names).start()
        # except:
        #    Debug.logger.debug("no config file {}".format(file))

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.hidecodexbtn = tk.IntVar(value=config.get_int("CanonnHideCodex"))

        self.hidecodex = self.hidecodexbtn.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Label(frame, text="Codex Settings").grid(
            row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Hide Codex Icons", variable=self.hidecodexbtn).grid(
            row=1, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Human Detailed", variable=self.humandetailedbtn).grid(
            row=1, column=1, sticky="NW")

        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('CanonnHideCodex', self.hidecodexbtn.get())
        config.set('CanonnHumanDetailed', self.humandetailedbtn.get())

        self.hidecodex = self.hidecodexbtn.get()
        self.humandetailed = self.humandetailedbtn.get()

        # dont check the retval
        self.visualisePOIData()
        self.visualisePlanetData()

    def visible(self):

        noicons = (self.hidecodex == 1)

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


class guardianSites(Emitter):
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
        "ancient_medium_003": 11
    }

    def __init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):

        Emitter.__init__(self, cmdr, is_beta, system, x, y,
                         z, entry, body, lat, lon, client)

        example = {"timestamp": "2019-10-10T10:23:32Z",
                   "event": "ApproachSettlement",
                   "Name": "$Ancient_Tiny_003:#index=1;", "Name_Localised": "Guardian Structure",
                   "SystemAddress": 5079737705833,
                   "BodyID": 25, "BodyName": "Synuefe LY-I b42-2 C 2",
                   "Latitude": 52.681084, "Longitude": 115.240822}

        example = {
            "timestamp": "2019-10-10T10:21:36Z",
            "event": "ApproachSettlement",
            "Name": "$Ancient:#index=2;", "Name_Localised": "Ancient Ruins (2)",
            "SystemAddress": 5079737705833,
            "BodyID": 25, "BodyName": "Synuefe LY-I b42-2 C 2",
            "Latitude": -10.090128, "Longitude": 114.505409}

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
            "NearestDestination_Localised": "Antike Ruinen (2)"
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
            prefix, suffix = siteName.split(':')
            self.index = self.get_index(siteName)

            if prefix:
                prefix = prefix.lower()[1:]

                if prefix in guardianSites.gstypes:
                    # This is a guardian structure
                    # self.gstype = guardianSites.gstypes.get(prefix)
                    self.gstype = prefix

                    self.modelreport = 'gsreports'
                if prefix == 'ancient':
                    # this is s guardian ruin
                    # self.gstype = 1
                    self.gstype = 'Unknown'
                    self.modelreport = 'grreports'

    def run(self):
        if self.modelreport and self.modelreport in ('grreports', 'gsreports') and self.system:
            payload = self.setPayload()
            payload["userType"] = 'pc'
            payload["reportType"] = 'new'
            payload["reportStatus"] = 'pending'
            payload["type"] = self.gstype
            payload["systemAddress"] = self.entry.get("SystemAddress")
            payload["bodyName"] = self.body
            payload["latitude"] = self.lat
            payload["longitude"] = self.lon
            payload["reportComment"] = json.dumps(self.entry, indent=4)
            payload["frontierID"] = self.index

            url = self.getUrl()
            Debug.logger.debug(payload)

            Debug.logger.debug(url)
            self.send(payload, url)

    def get_index(self, value):
        a = []
        a = value.split('#')
        if len(a) == 2:
            dummy, c = value.split('#')
            dummy, index_id = c.split("=")
            index_id = index_id[:-1]
            return index_id


class codexEmitter(Emitter):
    types = {}
    reporttypes = {}
    excludecodices = {}

    def split_region(self, region):
        if region:
            return region.replace("$Codex_RegionName_", "").replace(';', '')
        else:
            return None

    def __init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client, state):
        Emitter.__init__(self, cmdr, is_beta, system, x, y,
                         z, entry, body, lat, lon, client)
        self.modelreport = "xxreports"
        self.modeltype = "xxtypes"
        self.odyssey = state.get("Odyssey")

    def getSystemPayload(self, name):
        payload = self.setPayload()
        payload["userType"] = "pc"
        payload["reportType"] = "new"
        payload["type"] = name
        payload["reportStatus"] = "pending"
        payload["isBeta"] = self.is_beta
        payload["clientVersion"] = self.client
        payload["regionID"] = self.split_region(self.entry.get("Region"))

        return payload

    def split_nearest_destination(self, nearest_destination):

        # abort if no index
        if not "index" in nearest_destination:
            return None, None

        ndarray = []
        signal_type = None

        ndarray = nearest_destination.split('#')
        if len(ndarray) == 2:
            dummy, c = nearest_destination.split('#')
            dummy, index_id = c.split("=")
            index_id = index_id[:-1]
        else:
            dummy, b, c = ndarray
            dummy, signal_type = b.split("=")
            dummy, index_id = c.split("=")
            signal_type = signal_type[:-1]
            index_id = index_id[:-1]

        return signal_type, index_id

    def getBodyPayload(self, name):
        payload = self.getSystemPayload(name)
        payload["bodyName"] = self.body
        payload["coordX"] = self.x
        payload["coordY"] = self.y
        payload["coordZ"] = self.z
        payload["latitude"] = self.lat
        payload["longitude"] = self.lon
        payload["regionID"] = self.split_region(self.entry.get("Region"))

        nearest_destination = self.entry.get("NearestDestination")
        if nearest_destination:
            signal_type, index = self.split_nearest_destination(
                nearest_destination)
            payload["frontierID"] = index

        return payload

    def getCodexPayload(self):
        payload = self.getBodyPayload(self.entry.get("Name"))
        payload["entryId"] = self.entry.get("EntryID")
        payload["codexName"] = self.entry.get("Name")
        payload["codexNameLocalised"] = self.entry.get("Name_Localised")
        payload["subCategory"] = self.entry.get("SubCategory")
        payload["subCategoryLocalised"] = self.entry.get(
            "SubCategory_Localised")
        payload["category"] = self.entry.get("Category")
        payload["categoryLocalised"] = self.entry.get("Category_Localised")
        payload["regionName"] = self.entry.get("Region")
        payload["regionLocalised"] = self.entry.get("Region_Localised")
        payload["systemAddress"] = self.entry.get("SystemAddress")
        payload["voucherAmount"] = self.entry.get("VoucherAmount")
        payload["rawJson"] = self.entry

        del payload["type"]
        del payload["reportStatus"]
        del payload["userType"]
        del payload["reportType"]
        del payload["regionID"]

        return payload

    def getReportTypes(self, id):
        if not codexEmitter.reporttypes.get(id):
            url = "{}/reporttypes?journalID={}&_limit=1000".format(
                self.getUrl(), id)
            Debug.logger.debug(url)
            r = requests.get(
                "{}/reporttypes?journalID={}&_limit=1000".format(self.getUrl(), id))
            if r.status_code == requests.codes.ok:

                for exc in r.json():
                    codexEmitter.reporttypes["{}".format(exc["journalID"])] = {"endpoint": exc["endpoint"],
                                                                               "location": exc["location"],
                                                                               "type": exc["type"]}

            else:
                Debug.logger.error("error in getReportTypes")

    def getExcluded(self):
        if not codexEmitter.excludecodices:
            tempexclude = {}
            r = requests.get(
                "{}/excludecodices?_limit=1000".format(self.getUrl()))
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    tempexclude["${}_name;".format(exc["codexName"])] = True

                codexEmitter.excludecodices = tempexclude

    def run(self):

        self.getExcluded()

        # We don't want stellar bodies unless they are Green Giants

        stellar_bodies = (self.entry.get("Category") ==
                          '$Codex_Category_StellarBodies;')
        green_giant = (stellar_bodies and "Green" in self.entry.get("Name"))
        excluded = (codexEmitter.excludecodices.get(
            self.entry.get("Name").lower()) or stellar_bodies)

        included = (not excluded or green_giant)

        if included:
            self.getReportTypes(self.entry.get("EntryID"))
            url = self.getUrl()

            canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent",
                                {
                                    "gameState": {
                                        "systemName": self.system,
                                        "systemCoordinates": [self.x, self.y, self.z],
                                        "bodyName": self.body,
                                        "latitude": self.lat,
                                        "longitude": self.lon,
                                        "clientVersion": self.client,
                                        "isBeta": self.is_beta,
                                        "platform": "PC",
                                        "odyssey": self.odyssey
                                    },
                                    "rawEvent": self.entry,
                                    "eventType": self.entry.get("event"),
                                    "cmdrName": self.cmdr
                                }
                                )

            # CAPI doesnt want any stellar bodies so we will exclude them
            if not stellar_bodies:
                jid = self.entry.get("EntryID")
                reportType = codexEmitter.reporttypes.get(str(jid))

                if reportType:
                    if reportType.get("location") == "body":
                        payload = self.getBodyPayload(reportType.get("type"))
                        self.modelreport = reportType.get("endpoint")
                    else:
                        payload = self.getSystemPayload(reportType.get("type"))
                        self.modelreport = reportType.get("endpoint")
                else:
                    payload = self.getCodexPayload()
                    self.modelreport = "reportcodices"

                self.send(payload, url)


def test(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
    Debug.logger.debug("detected test request")
    # testentry = {
    #     "timestamp": "2019-09-12T09:01:35Z", "event": "CodexEntry", "EntryID": 2100101,
    #     "Name": "$Codex_Ent_Thargoid_Barnacle_01_Name;", "Name_Localised": "Common Thargoid Barnacle",
    #     "SubCategory": "$Codex_SubCategory_Organic_Structures;",
    #     "SubCategory_Localised": "Organic structures", "Category": "$Codex_Category_Biology;",
    #     "Category_Localised": "Biological and Geological", "Region": "$Codex_RegionName_18;",
    #     "Region_Localised": "Inner Orion Spur", "System": "Merope", "SystemAddress": 224644818084,
    #     "NearestDestination": "$SAA_Unknown_Signal:#type=$SAA_SignalType_Thargoid;:#index=1;",
    #     "NearestDestination_Localised": "Surface signal: Thargoid (1)"
    # }
    # submit("Factabulous Altimus", False, 'Merope', -78.59375, -149.625, -340.53125, testentry,
    #        'Merope 2 a', 2.656142, 143.024597, client)
    # testentry = {
    #     "timestamp": "2019-09-12T14:46:03Z", "event": "CodexEntry", "EntryID": 2205002,
    #     "Name": "$Codex_Ent_S_Seed_SdTp05_Bl_Name;", "Name_Localised": "Caeruleum Chalice Pod",
    #     "SubCategory": "$Codex_SubCategory_Organic_Structures;", "SubCategory_Localised": "Organic structures",
    #     "Category": "$Codex_Category_Biology;", "Category_Localised": "Biological and Geological",
    #     "Region": "$Codex_RegionName_23;", "Region_Localised": "Acheron", "System": "Pyra Dryoae ET-O d7-7",
    #     "SystemAddress": 252639699395, "IsNewEntry": True
    # }
    # submit(cmdr, False, "Pyra Dryoae ET-O d7-7", 7825.40625, -101.96875, 62316.9375, testentry,
    #        None, None, None, client)
    #
    # testentry = {
    #     "Name_Localised": "Purpureum Metallic Crystals",
    #     "SystemAddress": 355710669314,
    #     "Region_Localised": "Inner Orion Spur",
    #     "Name": "$Codex_Ent_L_Cry_MetCry_Pur_Name;",
    #     "EntryID": 2100802,
    #     "System": "Plaa Eurk MU-A c1",
    #     "SubCategory_Localised": "Organic structures",
    #     "Category_Localised": "Biological and Geological",
    #     "Region": "$Codex_RegionName_18;",
    #     "timestamp": "2019-09-12T15:28:19Z",
    #     "event": "CodexEntry",
    #     "Category": "$Codex_Category_Biology;",
    #     "SubCategory": "$Codex_SubCategory_Organic_Structures;"
    # }
    # submit("The_Martus", False, "Plaa Eurk MU-A c1", -1807.4375, 174.84375, -1058.5, testentry,
    #        None, None, None, client)
    #
    # testentry = {
    #     "Name_Localised": "Test Data",
    #     "SystemAddress": 355710669314,
    #     "Region_Localised": "Andromeda Wormhole",
    #     "Name": "$tet_test_test;",
    #     "EntryID": 9999999999,
    #     "System": "Raxxla",
    #     "SubCategory_Localised": "Imaginary structures",
    #     "Category_Localised": "Insanity",
    #     "Region": "$Codex_RegionName_00;",
    #     "timestamp": "2019-09-12T15:28:19Z",
    #     "event": "CodexEntry",
    #     "Category": "$Codex_Category_Insanity;",
    #     "SubCategory": "$Codex_SubCategory_Imaginary_Structures;"
    # }
    # submit("Test Date", False, "Raxxla", -1807.4375, 174.84375, -1058.5, testentry,
    #        None, None, None, client)

    testentry = {
        "timestamp": "2019-10-10T10:21:36Z",
        "event": "ApproachSettlement",
        "Name": "$Ancient:#index=2;", "Name_Localised": "Ancient Ruins (2)",
        "SystemAddress": 5079737705833,
        "BodyID": 25, "BodyName": "Synuefe LY-I b42-2 C 2",
        "Latitude": -10.090128, "Longitude": 114.505409
    }

    submit("TestUser", False, "Synuefe LY-I b42-2", 814.71875, -222.78125, -151.15625, testentry,
           "Synuefe LY-I b42-2 C 2", -10.090128, 114.505409, client)

    testentry = {"timestamp": "2019-10-10T10:23:32Z",
                 "event": "ApproachSettlement",
                 "Name": "$Ancient_Tiny_003:#index=1;", "Name_Localised": "Guardian Structure",
                 "SystemAddress": 5079737705833,
                 "BodyID": 25, "BodyName": "Synuefe LY-I b42-2 C 2",
                 "Latitude": 52.681084, "Longitude": 115.240822}

    submit("TestUser", False, "Synuefe LY-I b42-2", 814.71875, -222.78125, -151.15625, testentry,
           "Synuefe LY-I b42-2 C 2", 52.681084, 115.240822, client)

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
        "NearestDestination_Localised": "Antike Ruinen (2)"
    }

    submit("TestUser", False, "Synuefe ZL-J d10-109", 852.65625, -51.125, -124.84375, testentry,
           "Synuefe ZL-J d10-109 E 3", -27, -148, client)

    testentry = {"Name": "$Codex_Ent_Guardian_Sentinel_Name;", "event": "CodexEntry", "Region": "$Codex_RegionName_18;",
                 "System": "Synuefe CE-R c21-6", "EntryID": 3200600, "Category": "$Codex_Category_Civilisations;",
                 "timestamp": "2020-04-26T17:28:51Z", "SubCategory": "$Codex_SubCategory_Guardian;",
                 "SystemAddress": 1734529192634,
                 "Name_Localised": "Часовой Стражей", "Region_Localised": "Inner Orion Spur",
                 "Category_Localised": "Ксенологичские находки", "NearestDestination": "$Ancient_Small_001:#index=1;",
                 "SubCategory_Localised": "Объекты Стражей", "NearestDestination_Localised": "Конструкция Стражей"
                 }

    submit("TestUser", False, "Synuefe CE-R c21-6", 828.1875, -78, -105.1875, testentry,
           "Synuefe CE-R c21-6 C 1", 42, 73, client)


def submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client, state):
    codex_entry = (entry.get("event") == "CodexEntry")
    approach_settlement = (entry.get("event") == "ApproachSettlement")
    guardian_codices = (entry.get("EntryID") in [
                        3200200, 3200300, 3200400, 3200500, 3200600])
    guardian_event = (codex_entry and guardian_codices)

    if codex_entry:
        codexEmitter(cmdr, is_beta, entry.get("System"), x, y, z,
                     entry, body, lat, lon, client, state).start()

    if approach_settlement or guardian_event:
        guardianSites(cmdr, is_beta, system, x, y, z,
                      entry, body, lat, lon, client).start()

    if entry.get("event") == "SendText" and entry.get("Message") == "codextest":
        test(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)

    gnosis_station = entry.get("StationName") and entry.get(
        "StationName") == "The Gnosis"
    gnosis_fss = entry.get("FSSSignalDiscovered") and entry.get(
        "SignalName") == "The Gnosis"

    if gnosis_station or gnosis_fss:
        Debug.logger.debug("Hey it's The Gnosis!")
        canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postGnosis",
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
                                "client": client}
                            )
