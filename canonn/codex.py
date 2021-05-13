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
import requests
import threading
import webbrowser
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.emitter import Emitter
from config import config

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
            e["atmosphereType"] = j.get("Atmosphere")
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
            e["volcanismType"] = j.get("Volcanism")

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
    def __init__(self, system, callback):
        # Debug.logger.debug("initialise POITYpes Thread")
        threading.Thread.__init__(self)
        self.system = system
        self.callback = callback

    def run(self):
        # Debug.logger.debug("running poitypes")
        self.callback(self.system)
        # Debug.logger.debug("poitypes Callback Complete")


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
    def journal_entry(cls, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        if entry.get("event") == "ScanOrganic":

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
        "Planets": "Valuable Planets",
        "Tourist": "Tourist Informatiom",
        "Jumponium": "Jumponium Planets",
        "GreenSystem": "Jumponium Planets"
    }

    body_types = {
        'Metal-rich body': 'Metal-Rich Body',
        'Metal rich body': 'Metal-Rich Body',
        'Earth-like world': 'Earthlike World',
        'Earthlike body': 'Earthlike World',
        'Water world': 'Water World',
        'Ammonia world': 'Ammonia World'
    }

    bodycount = 0

    parentRadius = 0
    minPressure = 80

    close_orbit = 0.02
    eccentricity = 0.9

    waiting = True
    fsscount = 0

    edsmq = Queue()
    poiq = Queue()
    raw_mats = None

    def __init__(self, parent, gridrow):
        "Initialise the ``Patrol``."
        # Frame.__init__(
        #    self,
        #   parent
        # )

        self.frame = Frame(parent)
        self.parent = parent
        self.frame.bind('<<POIData>>', self.evisualise)
        self.frame.grid(sticky="W")
        self.frame.grid_remove()
        self.hidecodexbtn = tk.IntVar(value=config.get_int("CanonnHideCodex"))
        self.hidecodex = self.hidecodexbtn.get()

        self.container = Frame(self.frame)
        self.container.columnconfigure(1, weight=1)
        # self.tooltip=Frame(self)
        # self.tooltip.columnconfigure(1, weight=1)
        # self.tooltip.grid(row = 1, column = 0,sticky="NSEW")

        # self.tooltiplist=tk.Frame(self.tooltip)
        self.tooltiplist = tk.Frame(self.frame)

        self.images = {}
        self.labels = {}
        self.tooltipcol1 = []
        self.tooltipcol2 = []

        self.imagetypes = ("Geology", "Cloud", "Anomaly", "Thargoid",
                           "Biology", "Guardian", "Human", "Ring",
                           "None", "Other", "Planets", "Tourist", "Jumponium", "GreenSystem"
                           )
        self.temp_poidata = None
        self.temp_edsmdata = None
        self.addimage("Geology", 0)
        self.addimage("Cloud", 1)
        self.addimage("Anomaly", 2)
        self.addimage("Thargoid", 3)
        self.addimage("Biology", 4)
        self.addimage("Guardian", 5)
        self.addimage("Human", 6)
        self.addimage("Ring", 7)
        self.addimage("None", 8)
        self.addimage("Other", 9)
        self.addimage("Planets", 10)
        self.addimage("Tourist", 11)
        self.addimage("Jumponium", 12)
        self.addimage("GreenSystem", 13)

        # self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        self.frame.grid(row=gridrow, column=0)
        self.container.grid(row=0, column=0, sticky="W")
        self.poidata = []
        # self.tooltip.grid_remove()
        self.tooltiplist.grid()
        self.frame.grid()
        self.tooltiplist.grid_remove()
        self.frame.grid_remove()
        self.allowed = False
        self.bodies = None
        self.progress = tk.Label(self.container, text="?")
        self.progress.grid(row=0, column=0)
        self.progress.grid_remove()
        self.event = None
        # self.progress.grid_remove()

    # wrap visualise so we can call from time
    def tvisualise(self):
        if not config.shutting_down:
            Debug.logger.debug("frame.event_generate")
            # self.frame.event_generate('<<POIData>>', when='head')
            self.frame.event_generate('<<POIData>>')

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

        body_code = body.get("name").replace(self.system, '')
        if body.get("parents"):
            parent = body.get("parents")[0]
            if parent.get("Planet") and bodies.get(parent.get("Planet")) and bodies.get(parent.get("Planet")).get(
                    "rings"):

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
                            self.merge_poi(
                                "Tourist", 'Shepherd Moon', body_code)

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
                            self.merge_poi(
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
                    self.merge_poi("Tourist", 'Collision Flypast', body_code)

                elif close and period < 40:
                    self.merge_poi("Tourist", 'Close Flypast', body_code)

    def close_bodies(self, candidate, bodies, body_code):
        if candidate.get("semiMajorAxis") is not None and candidate.get("orbitalEccentricity") is not None:
            distance = None

            if isBinary(candidate) and candidate.get("semiMajorAxis") is not None:
                body = get_sibling(candidate, bodies)

                if body and body.get("semiMajorAxis") is not None:
                    # light seconds

                    d1 = self.apoapsis("semiMajorAxis", candidate.get("semiMajorAxis"),
                                       candidate.get("orbitalEccentricity"))
                    d2 = self.apoapsis("semiMajorAxis", body.get("semiMajorAxis"),
                                       body.get("orbitalEccentricity"))
                    # distance = (candidate.get("semiMajorAxis") + body.get("semiMajorAxis")) * 499.005
                    distance = d1 + d2

            if not isBinary(candidate):

                body = bodies.get(get_parent(candidate))
                distance = self.apoapsis("semiMajorAxis", candidate.get("semiMajorAxis"),
                                         candidate.get("orbitalEccentricity"))

            if candidate and body:
                r1 = self.radius_ly(body)
                r2 = self.radius_ly(candidate)
                # to account for things like stars and gas giants
                if distance is not None and r1 is not None and r2 is not None:
                    comparitor = 2 * (r1 + r2)

                if distance is not None and distance < comparitor:

                    if candidate.get("isLandable"):
                        self.merge_poi(
                            "Tourist", 'Close Orbit Landable', body_code)
                    else:
                        self.merge_poi("Tourist", 'Close Orbit', body_code)

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

                apehelion = self.apoapsis("semiMajorAxis", candidate.get("semiMajorAxis"),
                                          candidate.get("orbitalEccentricity") or 0)
                ring_span = get_outer_radius(
                    candidate) + get_outer_radius(parent)

                if binary:
                    distance = ((candidate.get("semiMajorAxis") +
                                 parent.get("semiMajorAxis")) * 499.005) - ring_span
                else:
                    distance = apehelion - ring_span

                if distance < 2 and binary:
                    parent_code = parent.get("name").replace(self.system, '')
                    self.merge_poi(
                        "Tourist", "Close Ring Proximity", body_code)
                    self.merge_poi(
                        "Tourist", "Close Ring Proximity", parent_code)

                if distance < 2 and not binary:
                    parent_code = parent.get("name").replace(self.system, '')
                    self.merge_poi(
                        "Tourist", "Close Ring Proximity", body_code)
                    self.merge_poi(
                        "Tourist", "Close Ring Proximity", parent_code)

    def trojan(self, candidate, bodies):
        # https://forums.frontier.co.uk/threads/hunt-for-trojans.369380/page-7

        if candidate.get("argOfPeriapsis"):
            body_code = candidate.get("name").replace(self.system, '')
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
                    non_binary = (
                        180 != abs(float(body.get("argOfPeriapsis")) - float(candidate.get("argOfPeriapsis"))))
                    attribute_match = (
                        axis_match and eccentricity_match and inclination_match and period_match)

                    if candidate.get("rings"):
                        ringo = "Ringed "
                    else:
                        ringo = ""

                    if not_self and sibling and attribute_match and non_binary:
                        if candidate.get('subType') in CodexTypes.body_types.keys():
                            self.merge_poi("Tourist", "{}Trojan {}".format(ringo, CodexTypes.body_types.get(
                                candidate.get('subType'))), body_code)
                        else:
                            self.merge_poi("Tourist", "{}Trojan {}".format(
                                ringo, candidate.get("type")), body_code)

    def ringed_star(self, candidate):
        hasRings = False
        body_code = candidate.get("name").replace(self.system, '')

        if candidate.get("rings") and candidate.get('type') == 'Star':
            for ring in candidate.get("rings"):
                if "Ring" in ring.get("name"):
                    hasRings = True

        if hasRings:
            self.merge_poi("Tourist", "Ringed Star", body_code)

    def has_bio(self, body):
        for entry in self.poidata:
            if entry.get("hud_category") == 'Biology' and entry.get("body") == body:
                return True
        return False

    def remove_jumponium(self):
        for entry in self.poidata:
            if entry.get("hud_category") in ('Jumponium', 'GreenSystem'):
                self.remove_poi(entry.get("hud_category"), entry.get(
                    "english_name"), entry.get("body"))

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
            body_code = body.get("name").replace(self.system, '')
            self.jumponium(body, body_code, jclass)

    def jumponium(self, body, body_code, jclass):

        materials = body.get("materials")
        basic = False
        standard = False
        premium = False

        volcanism = (body.get('volcanismType') and body.get(
            'volcanismType') != 'No volcanism')

        biology = self.has_bio(body)

        modifier = ""
        if volcanism:
            modifier = "+v"
        if biology:
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
                    self.merge_poi(
                        jclass, f"{target}{modifier}", body_code)

            basic = (materials.get("Carbon") and materials.get(
                "Vanadium") and materials.get("Germanium"))
            standard = (basic and materials.get("Cadmium")
                        and materials.get("Niobium"))
            premium = (materials.get("Carbon") and materials.get("Germanium") and materials.get(
                "Arsenic") and materials.get("Niobium") and materials.get("Yttrium") and materials.get("Polonium"))
        if premium:
            self.merge_poi(jclass, f"Premium{modifier}", body_code)
            return
        if standard:
            self.merge_poi(jclass, f"Standard{modifier}", body_code)
            return
        if basic:
            self.merge_poi(jclass, f"Basic{modifier}", body_code)
            return

    def rings(self, candidate, body_code):
        if candidate.get("rings"):
            for ring in candidate.get("rings"):
                if ring.get("name")[-4:] == "Ring":
                    if candidate.get("reserveLevel") and candidate.get("reserveLevel") in (
                            "Pristine", "PristineResources"):
                        self.merge_poi("Ring", "Pristine {} Rings".format(
                            ring.get("type")), body_code)
                    else:
                        self.merge_poi("Ring", "{} Rings".format(
                            ring.get("type")), body_code)
                area = get_area(ring.get("innerRadius"),
                                ring.get("outerRadius"))
                density = get_density(ring.get("mass"), ring.get(
                    "innerRadius"), ring.get("outerRadius"))

                if "Ring" in ring.get("name").replace(self.system, ''):

                    if ring.get("outerRadius") > 1000000:
                        self.merge_poi(
                            "Tourist", "Large Radius Rings", body_code)
                    elif ring.get("innerRadius") < (45935299.69736346 - (1 * 190463268.57872835)):
                        self.merge_poi(
                            "Tourist", "Small Radius Rings", body_code)
                    # elif ring.get("outerRadius") - ring.get("innerRadius") < 3500:
                    #    self.merge_poi(
                    #        "Tourist", "Thin Rings", body_code)
                    elif density < 0.005:
                        self.merge_poi(
                            "Tourist", "Low Density Rings", body_code)
                    elif density > 1000:
                        self.merge_poi(
                            "Tourist", "High Density Rings", body_code)

    # this seems horribly confused

    def evisualise(self, event):
        try:
            #Debug.logger.debug(f"evisualise {self.event}")

            while not self.edsmq.empty():
                # only expecting to go around once
                self.temp_edsmdata = self.edsmq.get()

            while not self.poiq.empty():
                r = self.poiq.get()
                self.merge_poi(r.get("hud_category"), r.get(
                    "english_name"), r.get("body"))

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
                        # self.merge_poi("Planets", "Unexplored Bodies", "")
                        if CodexTypes.fsscount > 0:
                            self.progress.grid()
                            # self.progress["text"]="{}%".format(round((float(CodexTypes.bodycount)/float(CodexTypes.fsscount))*100,1))
                            self.progress["text"] = "{}/{}".format(
                                CodexTypes.bodycount, CodexTypes.fsscount)
                    else:

                        self.progress.grid()
                        self.progress.grid_remove()

                    for k in bodies.keys():
                        if bodies.get(k).get("name") == self.system and bodies.get(k).get("type") == "Star":
                            CodexTypes.parentRadius = self.light_seconds("solarRadius",
                                                                         bodies.get(k).get("solarRadius"))

                        # lets normalise radius between planets and stars
                        if bodies.get(k).get("solarRadius") is not None:
                            bodies[k]["radius"] = bodies.get(
                                k).get("solarRadius")

                    for k in bodies.keys():
                        b = bodies.get(k)
                        # Debug.logger.debug(json.dumps(b,indent=4))
                        body_code = b.get("name").replace(self.system, '')
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
                            self.merge_poi(
                                "Tourist", "Moon Moon Moon", body_code)

                        # Terraforming
                        if b.get('terraformingState') == 'Candidate for terraforming':
                            if b.get('isLandable'):
                                if not b.get("rings"):
                                    self.merge_poi(
                                        "Planets", "Landable Terraformable", body_code)
                                else:
                                    self.merge_poi(
                                        "Planets", "Landable Ringed Terraformable", body_code)
                            else:
                                self.merge_poi(
                                    "Planets", "Terraformable", body_code)
                        elif b.get('terraformingState') == 'Terraforming':
                            if b.get('isLandable'):
                                if not b.get("rings"):
                                    self.merge_poi(
                                        "Planets", "Landable Terraforming", body_code)
                                else:
                                    self.merge_poi(
                                        "Planets", "Landable Ringed Terraforming", body_code)
                            else:
                                self.merge_poi(
                                    "Planets", "Terraforming", body_code)
                        else:
                            if b.get("rings") and b.get('isLandable'):
                                self.merge_poi(
                                    "Tourist", "Landable Ringed Body", body_code)

                        # Landable Volcanism
                        if b.get('type') == 'Planet' and b.get('volcanismType') and b.get(
                                'volcanismType') != 'No volcanism' and b.get(
                                'isLandable'):
                            self.merge_poi("Geology", b.get('volcanismType').replace(
                                " volcanism", ""), body_code)

                        # water ammonia etc
                        if b.get('subType') in CodexTypes.body_types.keys():

                            self.merge_poi("Planets", CodexTypes.body_types.get(
                                b.get('subType')), body_code)

                        # fast orbits
                        if b.get('orbitalPeriod'):
                            if abs(float(b.get('orbitalPeriod'))) <= 0.042:
                                self.merge_poi(
                                    "Tourist", 'Fast Orbital Period', body_code)

                        # Ringed ELW etc
                        if b.get('subType') in ('Earthlike body', 'Earth-like world', 'Water world', 'Ammonia world'):
                            if b.get("rings"):
                                self.merge_poi("Tourist",
                                               'Ringed {}'.format(
                                                   CodexTypes.body_types.get(b.get('subType'))),
                                               body_code)
                            if b.get("parents")[0].get("Planet"):
                                self.merge_poi("Tourist",
                                               '{} Moon'.format(
                                                   CodexTypes.body_types.get(b.get('subType'))),
                                               body_code)
                        if b.get('subType') in ('Earthlike body', 'Earth-like world') and b.get(
                                'rotationalPeriodTidallyLocked'):
                            self.merge_poi("Tourist", 'Tidal Locked Earthlike Word',
                                           body_code)

                        #    Landable high-g (>3g)
                        if b.get('type') == 'Planet' and b.get('gravity') > 3 and b.get('isLandable'):
                            self.merge_poi(
                                "Tourist", 'High Gravity', body_code)

                        #    Landable large (>18000km radius)
                        if b.get('type') == 'Planet' and b.get('radius') > 18000 and b.get('isLandable'):
                            self.merge_poi(
                                "Tourist", 'Large Radius Landable', body_code)

                        #    Moons of moons

                        #    Tiny objects (<300km radius)
                        if b.get('type') == 'Planet' and b.get('radius') < 300 and b.get('isLandable'):
                            self.merge_poi(
                                "Tourist", 'Tiny Radius Landable', body_code)

                        #    Fast and non-locked rotation
                        if b.get('type') == 'Planet' and abs(float(b.get('rotationalPeriod'))) < 1 / 24 and not b.get(
                                "rotationalPeriodTidallyLocked"):
                            self.merge_poi(
                                "Tourist", 'Fast unlocked rotation', body_code)

                        #    High eccentricity
                        if float(b.get("orbitalEccentricity") or 0) > CodexTypes.eccentricity:
                            self.merge_poi(
                                "Tourist", 'Highly Eccentric Orbit', body_code)

            else:
                CodexTypes.bodycount = 0

        except Exception as e:
            #line = sys.exc_info()[-1].tb_lineno
            self.merge_poi("Other", 'Plugin Error', None)
            Debug.logger.error("Plugin Error")

        #Debug.logger.debug(f"evisualise end {self.event}")
        self.visualise()

    def getdata(self, system):

        Debug.logger.debug(
            f"Getting POI data in thread {self.event} - system = {system}")
        CodexTypes.waiting = True
        # Debug.logger.debug("CodexTypes.waiting = True")

        # first we will clear the queues
        self.edsmq.clear()
        self.poiq.clear()
        try:
            url = "https://us-central1-canonn-api-236217.cloudfunctions.net/poiListSignals?system={}".format(
                quote_plus(system.encode('utf8')))

            # Debug.logger.debug(url)
            # Debug.logger.debug("request {}:  Active Threads {}".format(
            #    url, threading.activeCount()))
            r = requests.get(url, timeout=30)
            # Debug.logger.debug("request complete")
            r.encoding = 'utf-8'
            if r.status_code == requests.codes.ok:
                # Debug.logger.debug("got POI Data")
                temp_poidata = r.json()

            # push the data ont a queue
            for v in temp_poidata:
                self.poiq.put(v)
        except:
            Debug.logger.debug("Error getting POI data")

        try:
            url = "https://www.edsm.net/api-system-v1/bodies?systemName={}".format(
                quote_plus(system.encode('utf8')))

            # Debug.logger.debug("request {}:  Active Threads {}".format(
            #    url, threading.activeCount()))

            r = requests.get(url, timeout=30)
            # Debug.logger.debug("request complete")
            r.encoding = 'utf-8'
            if r.status_code == requests.codes.ok:
                # Debug.logger.debug("got EDSM Data")
                temp_edsmdata = r.json()
                # push edsm data only a queue
                self.edsmq.put(temp_edsmdata)
            else:
                Debug.logger.debug("EDSM Failed")
                Debug.logger.error("EDSM Failed")
        except:
            Debug.logger.debug("Error getting EDSM data")

        CodexTypes.waiting = False
        Debug.logger.debug("Triggering Event")
        self.tvisualise()
        Debug.logger.debug("Finished getting POI data in thread")

    def enter(self, event):

        type = event.widget["text"]
        # clear it if it exists
        for col in self.tooltipcol1:
            col["text"] = ""
            try:
                col.grid()
                col.grid_remove()
            except:
                Debug.logger.error("Col1 grid_remove error")
        for col in self.tooltipcol2:
            col["text"] = ""
            try:
                col.grid()
                col.grid_remove()
            except:
                Debug.logger.error("Col2 grid_remove error")

        poicount = 0

        # need to initialise if not exists
        if len(self.tooltipcol1) == 0:
            self.tooltipcol1.append(tk.Label(self.tooltiplist, text=""))
            self.tooltipcol2.append(tk.Label(self.tooltiplist, text=""))

        for poi in self.poidata:
            if poi.get("hud_category") == type:
                # add a new label if it dont exist
                if len(self.tooltipcol1) == poicount:
                    self.tooltipcol1.append(
                        tk.Label(self.tooltiplist, text=poi.get("english_name")))
                    self.tooltipcol2.append(
                        tk.Label(self.tooltiplist, text=poi.get("body")))
                else:  # just set the label
                    self.tooltipcol1[poicount]["text"] = poi.get(
                        "english_name")
                    self.tooltipcol2[poicount]["text"] = poi.get("body")

                # remember to grid them
                self.tooltipcol1[poicount].grid(
                    row=poicount, column=0, columnspan=1, sticky="NSEW")
                self.tooltipcol2[poicount].grid(
                    row=poicount, column=1, sticky="NSEW")
                poicount = poicount + 1

        if poicount == 0:
            self.tooltipcol1[poicount]["text"] = CodexTypes.tooltips.get(type)
            self.tooltipcol1[poicount].grid(
                row=poicount, column=0, columnspan=2)
            self.tooltipcol2[poicount].grid_remove()

        # self.tooltip.grid(sticky="NSEW")
        self.tooltiplist.grid(sticky="NSEW")

        # self.tooltip["text"]=CodexTypes.tooltips.get(event.widget["text"])

    def leave(self, event):
        # self.tooltip.grid_remove()

        self.tooltiplist.grid()
        self.tooltiplist.grid_remove()

    def click_icon(self, name):

        webbrowser.open(
            "https://tools.canonn.tech/Signals?system={}".format(quote_plus(self.system)))

    def addimage(self, name, col):

        grey = "{}_grey".format(name)
        self.images[name] = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "{}.gif".format(name)))
        self.images[grey] = tk.PhotoImage(file=os.path.join(
            CodexTypes.plugin_dir, "icons", "{}.gif".format(grey)))
        self.labels[name] = tk.Label(
            self.container, image=self.images.get(grey), text=name)
        self.labels[name].grid(row=0, column=col + 1)

        self.labels[name].bind("<Enter>", self.enter)
        self.labels[name].bind("<Leave>", self.leave)
        self.labels[name].bind(
            "<ButtonPress>", lambda event, x=name: self.click_icon(x))
        self.labels[name]["image"] = self.images[name]

    def set_image(self, name, enabled):
        if name == None:
            Debug.logger.error("set_image: name is None")
            return
        if name not in self.imagetypes:
            Debug.logger.error("set_image: name {} is not allowed")

        grey = "{}_grey".format(name)

        if enabled:
            setting = name
        else:
            setting = grey

        if enabled and self.labels.get(name):
            self.labels[name].grid()
        else:
            self.labels[name].grid()
            self.labels[name].grid_remove()

    def merge_poi(self, hud_category, english_name, body):

        # we could be passing in single body or a comma seperated list or nothing

        # we haven't found our bodies yet
        found = False
        signals = self.poidata

        for i, signal in enumerate(signals):
            # hud category and name match so we will see if the body is in the list
            if signal.get("english_name") == english_name and signal.get("hud_category") == hud_category:
                # some signals don't have a body so they are already found and we can skip
                if signal.get("body"):
                    # we might be be getting a list
                    pbodies = body.split(',')
                    # create an array from signals
                    sbodies = signal.get("body").split(',')

                    # join the two lists
                    sbodies.extend(pbodies)

                    # sort and make unique
                    bodies = sorted(list(set(list(map(str.strip, sbodies)))))
                    if self.system:
                        for index, value in enumerate(bodies):
                            bodies[index] = value.replace(
                                self.system, '').strip()

                    # convert back to a string
                    tmpb = ", ".join(bodies)

                    # update the poi
                    self.poidata[i]["body"] = tmpb
                found = True

        if not found:

            if body:
                body = body.strip()
            self.poidata.append(
                {"hud_category": hud_category, "english_name": english_name, "body": body})

    def remove_poi(self, hud_category, english_name, body):

        signals = self.poidata
        for i, v in enumerate(signals):
            if signals[i].get("english_name") == english_name and signals[i].get("hud_category") == hud_category and signals[i].get("body") == body:
                del self.poidata[i]

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

    def cleanup_poidata(self):
        # if we have bio or geo then remove Bio Bio and Geo Geo
        # if we have Jumponium+ and Jumponium then use the best value
        # We can't simply loop because there is an order of precedence

        bodies = {}
        """ for poi in self.poidata:
            if not bodies.get(poi.get("body")):
                bodies[poi.get("body")] = {"name": poi.get("body")}
                bodies[poi.get("body")][poi.get("hud_category")] = 0
            if not bodies.get(poi.get("body")) and not bodies.get(poi.get("body")).get(poi.get("hud_category")):
                bodies[poi.get("body")][poi.get("hud_category")] = 0

            bodies[poi.get("body")][poi.get("hud_category")] += 1

            if poi.get("hud_category") == "Jumponium":
                if not bodies[poi.get("body")].get("Jumplevel"):
                    bodies[poi.get("body")]["Jumplevel"] = poi.get(
                        "english_name")
                else:
                    bodies[poi.get("body")]["Jumplevel"] = self.compare_jumponioum(
                        poi.get("english_name"), bodies[poi.get("body")]["Jumplevel"]) """

        for k in bodies.keys():
            body = bodies.get(k)
            bodyname = body.get("name")

            for cat in ("Biology", "Geology", "Thargoid", "Guardian"):

                if body.get(cat) and body.get(cat) > 1:
                    Debug.logging.debug(f"removing {cat}")
                    self.remove_poi(cat, cat, body.get("name"))

            """ for jumplevel in ("Basic", "Standard", "Premium"):
                for mod in ("+v", "+b", "+v+b", "+b+v"):
                    if body.get("Jumplevel") and not body.get("Jumplevel") == f"{jumplevel}{mod}":
                        Debug.logging.debug(f"removing {jumplevel}{mod}")
                        self.remove_poi(
                            Jumponium, f"{jumplevel}{mod}", body.get("name")) """

    # this is used to trigger display of merged data

    def visualise(self):

        unscanned = nvl(CodexTypes.fsscount, 0) > nvl(CodexTypes.bodycount, 0)

        """ if not (threading.current_thread() is threading.main_thread()):
            Debug.logger.debug("We are not in the main thread")
        else:
            Debug.logger.debug("We are in the main thread") """

        # we have set an event type that can override waiting
        if self.event:
            Debug.logger.debug(f"Allowed event {self.event}")
            CodexTypes.waiting = False
            self.allowed = True
            self.event = None
        else:
            Debug.logger.debug(f"Not allowed event")

        # we may want to try again if the data hasn't been fetched yet
        if CodexTypes.waiting or not self.allowed:
            Debug.logger.debug("Still waiting")
        else:
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
            self.set_image("Planets", False)
            self.set_image("Tourist", False)
            self.set_image("Jumponium", False)
            self.set_image("GreenSystem", False)

            if self.poidata or unscanned:

                self.frame.grid()
                self.visible()
                self.cleanup_poidata()

                for r in self.poidata:
                    self.set_image(r.get("hud_category"), True)
            else:
                self.frame.grid()
                self.frame.grid_remove()

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

    def journal_entry(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        if not self.hidecodex:
            self.journal_entry_wrap(
                cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client)

    def journal_entry_wrap(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):

        if state.get("Raw"):
            CodexTypes.raw_mats = state.get("Raw")

        if body:
            bodycode = body.replace(system, '')
        else:
            bodycode = ""

        if entry.get("event") == "SendText" and entry.get("Message"):
            ma = entry.get("Message").split(' ')
            if len(ma) == 4 and ma[0] == "fake" and ma[1] == "bio":

                self.fake_biology(cmdr, system, x, y, z, ma[2], ma[3], client)

        if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            # go fetch some data.It will

            CodexTypes.fsscount = None
            CodexTypes.bodycount = None
            self.bodies = None
            self.poidata = []
            self.system = entry.get("StarSystem")
            Debug.logger.debug("Calling PoiTypes")
            poiTypes(entry.get("StarSystem"), self.getdata).start()

            self.frame.grid()
            self.frame.grid_remove()
            self.allowed = False

        if entry.get("event") == "CodexEntry" and not entry.get("Category") == '$Codex_Category_StellarBodies;':
            # really we need to identify the codex types
            self.system = system
            entry_id = entry.get("EntryID")
            codex_name_ref = CodexTypes.name_ref.get(entry_id)
            if codex_name_ref:
                hud_category = codex_name_ref.get("hud_category")
                if hud_category is not None and hud_category != 'None':
                    if body:
                        self.merge_poi(hud_category, entry.get(
                            "Name_Localised"), bodycode)
                    else:
                        self.merge_poi(hud_category, entry.get(
                            "Name_Localised"), "")
            else:
                self.merge_poi('Other', entry.get(
                    "Name_Localised"), bodycode)

        if entry.get("event") in ("Location", "StartUp"):
            self.system = system
            if entry.get("event") == "StartUp":
                system = entry.get("StarSystem")
            self.bodies = None
            self.allowed = True

            self.event = entry.get("event")
            Debug.logger.debug(f"setting allowed event {self.event}")
            poiTypes(system, self.getdata).start()

        if entry.get("event") in ("Location", "StartUp", "FSDJump", "CarrierJump"):
            # if entry.get("event") in ("FSDJump", "CarrierJump"):
            self.system = system
            if entry.get("SystemAllegiance") in ("Thargoid", "Guardian"):
                self.merge_poi(entry.get("SystemAllegiance"), "{} Controlled".format(
                    entry.get("SystemAllegiance")), "")
            self.allowed = True
            self.evisualise(None)

        if entry.get("event") == "FSSDiscoveryScan":
            self.system = system
            CodexTypes.fsscount = entry.get("BodyCount")
            # if not CodexTypes.fsscount:
            #    CodexTypes.fsscount = 0

            self.allowed = True
            self.evisualise(None)

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in ('$Fixed_Event_Life_Ring;', '$Fixed_Event_Life_Cloud;'):
            self.system = system

            if entry.get("SignalName") == '$Fixed_Event_Life_Cloud;':
                self.merge_poi("Cloud", "Life Cloud", "")
            else:
                self.merge_poi("Cloud", "Life Ring", "")
            self.allowed = True

            self.evisualise(None)

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in ('Guardian Beacon'):
            self.system = system
            self.merge_poi("Guardian", "Guardian Beacon", "")
            self.allowed = True

            self.evisualise(None)

        if entry.get("event") == "FSSSignalDiscovered":
            self.system = system
            dovis = False
            if "NumberStation" in entry.get("SignalName"):
                self.merge_poi("Human", "Unregistered Comms Beacon", bodycode)
                dovis = True
            elif "Megaship" in entry.get("SignalName"):
                self.merge_poi("Human", "Megaship", bodycode)
                dovis = True
            elif "ListeningPost" in entry.get("SignalName"):
                self.merge_poi("Human", "Listening Post", bodycode)
                dovis = True
            elif "CAPSHIP" in entry.get("SignalName"):
                self.merge_poi("Human", "Capital Ship", bodycode)
                dovis = True
            elif "Generation Ship" in entry.get("SignalName"):
                self.merge_poi("Human", entry.get("SignalName"), bodycode)
                dovis = True
            elif entry.get("IsStation"):
                FleetCarrier = (entry.get("SignalName") and entry.get(
                    "SignalName")[-4] == '-' and entry.get("SignalName")[-8] == ' ')
                if FleetCarrier:
                    self.merge_poi("Human", "Fleet Carrier", "")
                else:
                    self.merge_poi("Human", "Station", "")
                dovis = True
            self.allowed = True
            # self.evisualise(None)
            if dovis:
                self.evisualise(None)

        if entry.get("event") == "FSSAllBodiesFound":
            self.system = system
            # CodexTypes.bodycount = CodexTypes.fsscount
            self.allowed = True

            self.evisualise(None)

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

            self.evisualise(None)

        if entry.get("event") == "Scan" and entry.get("AutoScan") and entry.get("BodyID") == 1:
            self.system = system
            CodexTypes.parentRadius = self.light_seconds(
                "Radius", entry.get("Radius"))
            self.allowed = True

        if entry.get("event") == "SAASignalsFound":
            self.system = system
            # if we arent waiting for new data
            bodyName = entry.get("BodyName")
            bodyVal = bodyName.replace(self.system, '')

            signals = entry.get("Signals")
            for i, v in enumerate(signals):
                found = False
                type = v.get("Type")
                english_name = type.replace("$SAA_SignalType_", "").replace(
                    "ical;", "y").replace(";", '')
                if " Ring" in bodyName:
                    cat = "Ring"
                if "$SAA_SignalType_" in type:
                    cat = english_name

                self.merge_poi(cat, english_name, bodyVal)

            self.evisualise(None)
            self.allowed = True

    @classmethod
    def get_codex_names(cls):
        name_ref = {}

        r = requests.get(
            "https://us-central1-canonn-api-236217.cloudfunctions.net/codexNameRef")

        if r.status_code == requests.codes.ok:
            for entry in r.json():
                name_ref[entry.get("entryid")] = entry
            cls.name_ref = name_ref
        else:
            Debug.logger.error("error in get_codex_names")

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir
        cls.name_ref = {}

        file = os.path.join(cls.plugin_dir, 'data', 'codex_name_ref.json')
        # try:
        with open(file) as json_file:
            name_ref_array = json.load(json_file)

        # make this a dict
        for entry in name_ref_array:
            cls.name_ref[entry.get("entryid")] = entry

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

        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('CanonnHideCodex', self.hidecodexbtn.get())

        self.hidecodex = self.hidecodexbtn.get()

        # dont check the retval
        self.visualise()

    def visible(self):

        noicons = (self.hidecodex == 1)

        if noicons:
            self.frame.grid()
            self.frame.grid_remove()
            self.isvisible = False
            return False
        else:
            self.frame.grid()
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
        codexEmitter(cmdr, is_beta, entry.get("System"), x, y,
                     z, entry, body, lat, lon, client, state).start()

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
