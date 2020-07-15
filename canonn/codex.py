# Try python3 before 2.7
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
import sys
import threading
import webbrowser
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.emitter import Emitter
from config import config
from math import sqrt, pow

nvl = lambda a, b: a or b


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
    debug("Ring radius {}km = {}ls".format(outer, result))
    return result


# This function will return a body in edsm format
def journal2edsm(j):
    # debug(json.dumps(j, indent=4))

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
            e["atmosphereComposition"] = convertAtmosphere(j.get("AtmosphereComposition"))
        if j.get("Atmosphere") != "":
            e["atmosphereType"] = j.get("Atmosphere")
        else:
            e["atmosphereType"] = "No atmosphere"
        if j.get("TerraformState") == "Terraformable":
            e["terraformingState"] = 'Candidate for terraforming'
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
    debug(json.dumps(e, indent=4))
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


class poiTypes(threading.Thread):
    def __init__(self, system, callback):
        # debug("initialise POITYpes Thread")
        threading.Thread.__init__(self)
        self.system = system
        self.callback = callback

    def run(self):
        # debug("running poitypes")
        self.callback(self.system)
        # debug("poitypes Callback Complete")


class saaScan():

    def __init__(self):
        debug("We only use class methods here")

    @classmethod
    def journal_entry(cls, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        if entry.get("event") == "SAASignalsFound":
            canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postSAA",
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
                                    "client": client
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
        "Tourist": "Tourist Informatiom"
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
        self.hidecodexbtn = tk.IntVar(value=config.getint("Canonn:HideCodex"))
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
                           "None", "Other", "Planets", "Tourist"
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
        # self.progress.grid_remove()

    # wrap visualise so we can call from time
    def tvisualise(self):
        self.evisualise(None)

    def sheperd_moon(self, body, bodies):

        def get_density(mass, inner, outer):
            a1 = math.pi * pow(inner, 2)
            a2 = math.pi * pow(outer, 2)
            a = a2 - a1
            debug("{} {} {}".format(mass, inner, outer))
            # add a tiny number to force non zero
            if a > 0:
                density = mass / a
                debug(density)
            else:
                density = 0
            return density

        body_code = body.get("name").replace(self.system, '')
        if body.get("parents"):
            parent = body.get("parents")[0]
            if parent.get("Planet") and bodies.get(parent.get("Planet")) and bodies.get(parent.get("Planet")).get(
                    "rings"):
                debug("Parent has rings")
                # If the parent body has a ring
                for ring in bodies.get(parent.get("Planet")).get("rings"):
                    if 'Belt' not in ring.get("name"):
                        density = get_density(ring.get("mass"), ring.get("innerRadius"), ring.get("outerRadius"))

                        r1 = float(ring.get("outerRadius")) * 1000  # m
                        # convert au to km
                        r2 = float(body.get("semiMajorAxis")) * 149597870691
                        r3 = float(body.get("radius") or body.get("solarRadius")) * 1000
                        # and the orbit of the body is close to the outer radius

                        if r2 - r3 < r1 + 15000000:
                            self.merge_poi("Tourist", 'Shepherd Moon', body_code)
                            debug("Shepherd Moon {} {} {} {} {}".format(r1, r2, r3, body.get("axialTilt"),
                                                                        bodies.get(parent.get("Planet")).get(
                                                                            "axialTilt")))
            # gah i need to refector this to avoid duplication
            if parent.get("Star") and bodies.get(parent.get("Star")) and bodies.get(parent.get("Star")).get("rings"):
                debug("Parent has rings")
                # If the parent body has a ring
                for ring in bodies.get(parent.get("Star")).get("rings"):
                    if 'Belt' not in ring.get("name"):
                        density = get_density(ring.get("mass"), ring.get("innerRadius"), ring.get("outerRadius"))

                        r1 = float(ring.get("outerRadius")) * 1000  # m
                        # convert au to km
                        r2 = float(body.get("semiMajorAxis")) * 149597870691
                        r3 = float(body.get("radius") or body.get("solarRadius")) * 1000
                        # and the orbit of the body is close to the outer radius
                        debug("Shep {} {} {}".format(r1, r2, r3))
                        if r2 - r3 < r1 + 15000000:
                            self.merge_poi("Tourist", 'Shepherd Planet', body_code)
                            debug("Shepherd Planet {} {} {}".format(r1, r2, r3))
                            debug((r2 - r1) - r3)

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
            valid_body = (sibling.get("semiMajorAxis") is not None and valid_body)
            valid_body = (body.get("orbitalEccentricity") is not None and valid_body)
            valid_body = (sibling.get("orbitalEccentricity") is not None and valid_body)
            valid_body = (body.get("orbitalPeriod") is not None and valid_body)
            valid_body = (sibling.get("orbitalPeriod") is not None and valid_body)
            not_self = (body.get("bodyId") != sibling.get("bodyId"))
            valid_body = (not_self and valid_body)

            # if we share teh same parent and not the same body
            if valid_body and str(p1[0]) == str(p2[0]):
                a1 = self.aphelion("semiMajorAxis", body.get("semiMajorAxis"), body.get("orbitalEccentricity"))
                a2 = self.aphelion("semiMajorAxis", sibling.get("semiMajorAxis"), sibling.get("orbitalEccentricity"))
                r1 = sibling.get("radius") / 299792.5436
                r2 = body.get("radius") / 299792.5436

                distance = abs(a1 - a2)
                # print("distance {}, radii = {}".format(distance,r1+r2))
                period = get_synodic_period(body, sibling)
                debug("flypast: {} distance = {} avgdiameter = {} synodic = {} ".format(body_code, distance, r1 + r2,
                                                                                        period))
                # average diameter and 4 days synodic period
                if distance < 2 * (r1 + r2) and period < 30:
                    self.merge_poi("Tourist", 'Close Flypast', body_code)

    def close_bodies(self, candidate, bodies, body_code):
        if candidate.get("semiMajorAxis") is not None and candidate.get("orbitalEccentricity") is not None:
            distance = None

            if isBinary(candidate) and candidate.get("semiMajorAxis") is not None:
                body = get_sibling(candidate, bodies)
                debug("binary")

                if body and body.get("semiMajorAxis") is not None:
                    # light seconds

                    d1 = self.aphelion("semiMajorAxis", candidate.get("semiMajorAxis"),
                                       candidate.get("orbitalEccentricity"))
                    d2 = self.aphelion("semiMajorAxis", body.get("semiMajorAxis"),
                                       body.get("orbitalEccentricity"))
                    # distance = (candidate.get("semiMajorAxis") + body.get("semiMajorAxis")) * 499.005
                    distance = d1 + d2

            if not isBinary(candidate):
                debug("non-binary")

                body = bodies.get(get_parent(candidate))
                distance = self.aphelion("semiMajorAxis", candidate.get("semiMajorAxis"),
                                         candidate.get("orbitalEccentricity"))

            if candidate and body:
                r1 = self.radius_ly(body)
                r2 = self.radius_ly(candidate)
                # to account for things like stars and gas giants
                if distance is not None and r1 is not None and r2 is not None:
                    comparitor = 2 * (r1 + r2)

                if distance is not None and distance < comparitor:
                    debug("{} distance: {} comparitor {}".format(body_code, distance, comparitor))
                    if candidate.get("isLandable"):
                        self.merge_poi("Tourist", 'Close Orbit Landable', body_code)
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
            debug("Ring ring {} {}".format(candidate.get("semiMajorAxis"), candidate.get("orbitalEccentricity")))
            if candidate.get("semiMajorAxis"):
                debug("Calculating ring distance")
                apehelion = self.aphelion("semiMajorAxis", candidate.get("semiMajorAxis"),
                                          candidate.get("orbitalEccentricity") or 0)
                ring_span = get_outer_radius(candidate) + get_outer_radius(parent)
                debug("Ring Span: {}".format(ring_span))
                if binary:
                    distance = ((candidate.get("semiMajorAxis") + parent.get("semiMajorAxis")) * 499.005) - ring_span
                else:
                    distance = apehelion - ring_span

                if distance < 2 and binary:
                    parent_code = parent.get("name").replace(self.system, '')
                    self.merge_poi("Tourist", "Close Ring Proximity", body_code)
                    self.merge_poi("Tourist", "Close Ring Proximity", parent_code)

                if distance < 2 and not binary:
                    parent_code = parent.get("name").replace(self.system, '')
                    self.merge_poi("Tourist", "Close Ring Proximity", body_code)
                    self.merge_poi("Tourist", "Close Ring Proximity", parent_code)

    def trojan(self, candidate, bodies):
        # https://forums.frontier.co.uk/threads/hunt-for-trojans.369380/page-7

        if candidate.get("argOfPeriapsis"):
            body_code = candidate.get("name").replace(self.system, '')
            for body in bodies.values():
                # set up some booleans
                if body.get("argOfPeriapsis") and candidate.get("argOfPeriapsis"):
                    not_self = (body.get("bodyId") != candidate.get("bodyId"))
                    sibling = (get_parent(body) == get_parent(candidate))
                    axis_match = (body.get("semiMajorAxis") == candidate.get("semiMajorAxis"))
                    eccentricity_match = (body.get("orbitalEccentricity") == candidate.get("orbitalEccentricity"))
                    inclination_match = (body.get("orbitalInclination") == candidate.get("orbitalInclination"))
                    period_match = (body.get("orbitalPeriod") == candidate.get("orbitalPeriod"))
                    non_binary = (
                            180 != abs(float(body.get("argOfPeriapsis")) - float(candidate.get("argOfPeriapsis"))))
                    attribute_match = (axis_match and eccentricity_match and inclination_match and period_match)

                    if candidate.get("rings"):
                        ringo = "Ringed "
                    else:
                        ringo = ""

                    if not_self and sibling and attribute_match and non_binary:
                        if candidate.get('subType') in CodexTypes.body_types.keys():
                            self.merge_poi("Tourist", "{}Trojan {}".format(ringo, CodexTypes.body_types.get(
                                candidate.get('subType'))), body_code)
                        else:
                            self.merge_poi("Tourist", "{}Trojan {}".format(ringo, candidate.get("type")), body_code)
        else:
            debug("Arg of periapsis is None {} {} {}".format(candidate.get("name"), candidate.get("type"),
                                                             candidate.get("bodyId")))

    def ringed_star(self, candidate):
        hasRings = False
        body_code = candidate.get("name").replace(self.system, '')

        if candidate.get("rings") and candidate.get('type') == 'Star':
            for ring in candidate.get("rings"):
                if "Ring" in ring.get("name"):
                    hasRings = True

        if hasRings:
            self.merge_poi("Tourist", "Ringed Star", body_code)

    def rings(self, candidate, body_code):
        if candidate.get("rings"):
            for ring in candidate.get("rings"):
                if ring.get("name")[-4:] == "Ring":
                    if candidate.get("reserveLevel") and candidate.get("reserveLevel") in (
                            "Pristine", "PristineResources"):
                        self.merge_poi("Ring", "Pristine {} Rings".format(ring.get("type")), body_code)
                    else:
                        self.merge_poi("Ring", "{} Rings".format(ring.get("type")), body_code)
                area = get_area(ring.get("innerRadius"), ring.get("outerRadius"))
                density = get_density(ring.get("mass"), ring.get("innerRadius"), ring.get("outerRadius"))

                if "Ring" in ring.get("name").replace(self.system, ''):
                    if area > 7.604221648984754e+17 + (2 * 2.91663339734517e+19):
                        self.merge_poi("Tourist", "High Area Rings", body_code)
                    elif ring.get("outerRadius") > (99395267.84341194 + (2 * 520150745.3976549)):
                        self.merge_poi("Tourist", "Large Radius Rings", body_code)
                    elif ring.get("innerRadius") < (45935299.69736346 - (2 * 190463268.57872835)):
                        self.merge_poi("Tourist", "Small Radius Rings", body_code)
                    elif area < 7.604221648984754e+17 - (2 * 2.91663339734517e+19):
                        self.merge_poi("Tourist", "Low Area Rings", body_code)
                    elif density < 4.917372037815108 - (2 * 297.7768008954368):
                        self.merge_poi("Tourist", "Low Density Rings", body_code)
                    elif density < 4.917372037815108 - (2 * 297.7768008954368):
                        self.merge_poi("Tourist", "Low Density Rings", body_code)
                    elif density > 4.917372037815108 + (2 * 297.7768008954368):
                        self.merge_poi("Tourist", "High Density Rings", body_code)

    def evisualise(self, event):
        try:
            debug("evisualise")
            self.poidata = []
            debug("self.poidata = []")
            usystem = unquote(self.system)

            if self.temp_poidata:
                for r in self.temp_poidata:
                    self.merge_poi(r.get("hud_category"), r.get("english_name"), r.get("body"))

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
                        debug("addimg body: {}".format(b.get("name")))
                        self.bodies[b.get("bodyId")] = b

            if len(self.bodies) > 0:
                debug("We have bodies")
                # bodies = self.temp_edsmdata.json().get("bodies")
                bodies = self.bodies
                if bodies:
                    CodexTypes.bodycount = len(bodies)
                    if not CodexTypes.fsscount:
                        CodexTypes.fsscount = 0
                    debug("body reconciliation: {} {}".format(CodexTypes.fsscount, nvl(CodexTypes.bodycount, 0)))
                    if nvl(CodexTypes.fsscount, 0) > nvl(CodexTypes.bodycount, 0):
                        # self.merge_poi("Planets", "Unexplored Bodies", "")
                        if CodexTypes.fsscount > 0:
                            self.progress.grid()
                            # self.progress["text"]="{}%".format(round((float(CodexTypes.bodycount)/float(CodexTypes.fsscount))*100,1))
                            self.progress["text"] = "{}/{}".format(CodexTypes.bodycount, CodexTypes.fsscount)
                    else:
                        # self.remove_poi("Planets", "Unexplored Bodies")
                        self.progress.grid_remove()

                    debug("bodycount: {}".format(CodexTypes.bodycount))

                    for k in bodies.keys():
                        if bodies.get(k).get("name") == self.system and bodies.get(k).get("type") == "Star":
                            CodexTypes.parentRadius = self.light_seconds("solarRadius",
                                                                         bodies.get(k).get("solarRadius"))

                        # lets normalise radius between planets and stars
                        if bodies.get(k).get("solarRadius") is not None:
                            bodies[k]["radius"] = bodies.get(k).get("solarRadius")

                    for k in bodies.keys():
                        b = bodies.get(k)
                        # debug(json.dumps(b,indent=4))
                        body_code = b.get("name").replace(self.system, '')
                        body_name = b.get("name")

                        self.sheperd_moon(b, bodies)
                        self.trojan(b, bodies)
                        self.ringed_star(b)
                        self.close_rings(b, bodies, body_code)
                        self.close_bodies(b, bodies, body_code)
                        self.close_flypast(b, bodies, body_code)
                        self.rings(b, body_code)
                        if moon_moon_moon(b):
                            self.merge_poi("Tourist", "Moon Moon Moon", body_code)

                        # Terraforming
                        if b.get('terraformingState') == 'Candidate for terraforming':
                            if b.get('isLandable'):
                                if not b.get("rings"):
                                    self.merge_poi("Planets", "Landable Terraformable", body_code)
                                else:
                                    self.merge_poi("Planets", "Landable Ringed Terraformable", body_code)
                            else:
                                self.merge_poi("Planets", "Terraformable", body_code)
                        else:
                            if b.get("rings") and b.get('isLandable'):
                                self.merge_poi("Tourist", "Landable Ringed Body", body_code)

                        # Landable Volcanism
                        if b.get('type') == 'Planet' and b.get('volcanismType') and b.get(
                                'volcanismType') != 'No volcanism' and b.get(
                            'isLandable'):
                            self.merge_poi("Geology", b.get('volcanismType').replace(" volcanism", ""), body_code)

                        # water ammonia etc
                        if b.get('subType') in CodexTypes.body_types.keys():
                            debug(b.get('subType'))
                            self.merge_poi("Planets", CodexTypes.body_types.get(b.get('subType')), body_code)

                        # fast orbits
                        if b.get('orbitalPeriod'):
                            if abs(float(b.get('orbitalPeriod'))) <= 0.042:
                                self.merge_poi("Tourist", 'Fast Orbital Period', body_code)

                        # Ringed ELW etc
                        if b.get('subType') in ('Earthlike body', 'Earth-like world', 'Water world', 'Ammonia world'):
                            if b.get("rings"):
                                self.merge_poi("Tourist",
                                               'Ringed {}'.format(CodexTypes.body_types.get(b.get('subType'))),
                                               body_code)
                            if b.get("parents")[0].get("Planet"):
                                self.merge_poi("Tourist",
                                               '{} Moon'.format(CodexTypes.body_types.get(b.get('subType'))),
                                               body_code)
                        if b.get('subType') in ('Earthlike body', 'Earth-like world') and b.get(
                                'rotationalPeriodTidallyLocked'):
                            self.merge_poi("Tourist", 'Tidal Locked Earthlike Word',
                                           body_code)

                        #    Landable high-g (>3g)
                        if b.get('type') == 'Planet' and b.get('gravity') > 3 and b.get('isLandable'):
                            self.merge_poi("Tourist", 'High Gravity', body_code)

                        #    Landable large (>18000km radius)
                        if b.get('type') == 'Planet' and b.get('radius') > 18000 and b.get('isLandable'):
                            self.merge_poi("Tourist", 'Large Radius Landable', body_code)

                        #    Moons of moons

                        #    Tiny objects (<300km radius)
                        if b.get('type') == 'Planet' and b.get('radius') < 300 and b.get('isLandable'):
                            self.merge_poi("Tourist", 'Tiny Radius Landable', body_code)

                        #    Fast and non-locked rotation
                        if b.get('type') == 'Planet' and abs(float(b.get('rotationalPeriod'))) < 1 / 24 and not b.get(
                                "rotationalPeriodTidallyLocked"):
                            self.merge_poi("Tourist", 'Fast unlocked rotation', body_code)

                        #    High eccentricity
                        if float(b.get("orbitalEccentricity") or 0) > CodexTypes.eccentricity:
                            self.merge_poi("Tourist", 'Highly Eccentric Orbit', body_code)

                        #    Good jumponium availability (5/6 materials on a single body)
                        #    Full jumponium availability within a single system
                        #    Full jumponium availability on a single body

            else:
                CodexTypes.bodycount = 0
                debug("bodycount: {}".format(CodexTypes.bodycount))
        except:
            if Debug.debugswitch == 1:
                self.merge_poi("Other", 'Plugin Error', None)
                self.visualise()
            raise
        self.visualise()

    def getdata(self, system):
        # debug("Getting POI data in thread")
        CodexTypes.waiting = True
        # debug("CodexTypes.waiting = True")

        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/poiListSignals?system={}".format(
            quote_plus(system.encode('utf8')))
        # debug(url)
        r = requests.get(url)
        r.encoding = 'utf-8'
        if r.status_code == requests.codes.ok:
            # debug("got POI Data")
            self.temp_poidata = r.json()

        edsm = "https://www.edsm.net/api-system-v1/bodies?systemName={}".format(quote_plus(system.encode('utf8')))
        # debug(edsm)
        r = requests.get(edsm)
        r.encoding = 'utf-8'
        if r.status_code == requests.codes.ok:
            # debug("got EDSM Data")
            self.temp_edsmdata = r.json()

        CodexTypes.waiting = False
        # debug("event_generate")
        self.frame.event_generate('<<POIData>>', when='head')
        # debug("Finished getting POI data in thread")

    def enter(self, event):

        type = event.widget["text"]
        # clear it if it exists
        for col in self.tooltipcol1:
            col["text"] = ""
            try:
                col.grid()
                col.grid_remove()
            except:
                error("Col1 grid_remove error")
        for col in self.tooltipcol2:
            col["text"] = ""
            try:
                col.grid()
                col.grid_remove()
            except:
                error("Col2 grid_remove error")

        poicount = 0

        # need to initialise if not exists
        if len(self.tooltipcol1) == 0:
            self.tooltipcol1.append(tk.Label(self.tooltiplist, text=""))
            self.tooltipcol2.append(tk.Label(self.tooltiplist, text=""))

        for poi in self.poidata:
            if poi.get("hud_category") == type:
                ## add a new label if it dont exist
                if len(self.tooltipcol1) == poicount:
                    self.tooltipcol1.append(tk.Label(self.tooltiplist, text=poi.get("english_name")))
                    self.tooltipcol2.append(tk.Label(self.tooltiplist, text=poi.get("body")))
                else:  ## just set the label
                    self.tooltipcol1[poicount]["text"] = poi.get("english_name")
                    self.tooltipcol2[poicount]["text"] = poi.get("body")

                # remember to grid them
                self.tooltipcol1[poicount].grid(row=poicount, column=0, columnspan=1, sticky="NSEW")
                self.tooltipcol2[poicount].grid(row=poicount, column=1, sticky="NSEW")
                poicount = poicount + 1

        if poicount == 0:
            self.tooltipcol1[poicount]["text"] = CodexTypes.tooltips.get(type)
            self.tooltipcol1[poicount].grid(row=poicount, column=0, columnspan=2)
            self.tooltipcol2[poicount].grid_remove()

        # self.tooltip.grid(sticky="NSEW")
        self.tooltiplist.grid(sticky="NSEW")

        ##self.tooltip["text"]=CodexTypes.tooltips.get(event.widget["text"])

    def leave(self, event):
        # self.tooltip.grid_remove()

        self.tooltiplist.grid()
        self.tooltiplist.grid_remove()

    def click_icon(self, name):
        debug("clicked on icon {} ".format(name))
        webbrowser.open("https://tools.canonn.tech/Signals?system={}".format(quote_plus(self.system)))

    def addimage(self, name, col):

        grey = "{}_grey".format(name)
        self.images[name] = tk.PhotoImage(file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(name)))
        self.images[grey] = tk.PhotoImage(file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(grey)))
        self.labels[name] = tk.Label(self.container, image=self.images.get(grey), text=name)
        self.labels[name].grid(row=0, column=col + 1)

        self.labels[name].bind("<Enter>", self.enter)
        self.labels[name].bind("<Leave>", self.leave)
        self.labels[name].bind("<ButtonPress>", lambda event, x=name: self.click_icon(x))
        self.labels[name]["image"] = self.images[name]

    def set_image(self, name, enabled):
        if name == None:
            error("set_image: name is None")
            return
        if name not in self.imagetypes:
            error("set_image: name {} is not allowed")

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
        debug("Merge POI")
        found = False
        signals = self.poidata
        for i, v in enumerate(signals):
            # hud category andname match so we will see if teh body is in teh list
            if signals[i].get("english_name") == english_name and signals[i].get("hud_category") == hud_category:
                tmpb = signals[i].get("body")
                debug("tmpb {} {} {}".format(tmpb,hud_category,english_name))
                if not body in tmpb.split():
                    self.poidata[i]["body"] = ",".join([tmpb, body])
                found = True

        if not found:
            self.poidata.append({"hud_category": hud_category, "english_name": english_name, "body": body})

    def remove_poi(self, hud_category, english_name):
        debug("Remove POI")
        signals = self.poidata
        for i, v in enumerate(signals):
            if signals[i].get("english_name") == english_name and signals[i].get("hud_category") == hud_category:
                del self.poidata[i]

    def light_seconds(self, tag, value):
        debug("light seconds {} {}".format(tag, value))
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
        debug("focus  {}ls".format(a))

        return focus

    def aphelion(self, tag, major, eccentricity):
        a = float(self.light_seconds(tag, major))
        e = float(eccentricity or 0)
        focus = a * (1 + e)
        debug("Apehelion  {}ls".format(a))

        return focus

    def surface_distance(self, d, r1, r2):
        return d - (r1 + r2);

    def visualise(self):

        unscanned = nvl(CodexTypes.fsscount, 0) > nvl(CodexTypes.bodycount, 0)

        debug("Codex visualise")
        # we may want to try again if the data hasn't been fetched yet
        if CodexTypes.waiting or not self.allowed:
            debug("Still waiting")
        else:
            debug("setting images")
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

            if self.poidata or unscanned:
                debug("Codex Grid")
                self.frame.grid()
                self.visible()
                for r in self.poidata:
                    debug(r)
                    self.set_image(r.get("hud_category"), True)
            else:
                self.frame.grid()
                self.frame.grid_remove()

    def fake_biology(self,cmdr,system,x,y,z,planet,count,client):
         bodyname=f"{system} {planet}"

         signal={
             "timestamp": "2020-07-13T22:37:34Z",
             "event": "SAASignalsFound",
             "BodyName": bodyname,
             "Signals": [
                 {"Type": "$SAA_SignalType_Biological;",
                  "Type_Localised": "Biological",
                  "Count": count}]
        }

         self.journal_entry(cmdr, None, system, None, signal, None,x , y, z, bodyname, None, None, client)


    def journal_entry(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        if not self.hidecodex:
            self.journal_entry_wrap(cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client)

    def journal_entry_wrap(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        self.system = system
        debug("Codex {}".format(entry.get("event")))


        if entry.get("event") == "SendText" and entry.get("Message"):
            ma =  entry.get("Message").split(' ')
            if len(ma) == 4 and ma[0] == "fake" and ma[1] == "bio":
                debug("faking a bio signal")
                self.fake_biology(cmdr, system, x, y, z, ma[2], ma[3],client)

        if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            # go fetch some data.It will
            CodexTypes.fsscount = None
            CodexTypes.bodycount = None
            self.bodies = None
            poiTypes(entry.get("StarSystem"), self.getdata).start()
            self.frame.grid()
            self.frame.grid_remove()
            self.allowed = False

            # self.visualise()

        if entry.get("event") in ("Location", "StartUp", "CarrierJump"):
            debug("{} Looking for POI data in {}".format(entry.get("event"), system))
            self.bodies = None
            poiTypes(system, self.getdata).start()

            self.allowed = True
            # we can't wait for another event so give it 5 seconds
            # then ten seconds later for good measure
            self.frame.after(5000, self.tvisualise)
            self.frame.after(10000, self.tvisualise)

        if entry.get("event") in ("Location", "StartUp", "FSDJump", "CarrierJump"):
            if entry.get("SystemAllegiance") in ("Thargoid", "Guardian"):
                self.merge_poi(entry.get("SystemAllegiance"), "{} Controlled".format(entry.get("SystemAllegiance")), "")
            self.allowed = True
            self.visualise()

        if entry.get("event") == "FSSDiscoveryScan":
            debug("setting fsscount {} ".format(entry.get("BodyCount")))
            # debug(entry)
            CodexTypes.fsscount = entry.get("BodyCount")
            # if not CodexTypes.fsscount:
            #    CodexTypes.fsscount = 0

            self.allowed = True
            self.evisualise(None)

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in (
                '$Fixed_Event_Life_Ring;', '$Fixed_Event_Life_Cloud;'):
            if entry.get("SignalName") == '$Fixed_Event_Life_Cloud;':
                self.merge_poi("Cloud", "Life Cloud", "")
            else:
                self.merge_poi("Cloud", "Life Ring", "")
            self.allowed = True
            self.evisualise(None)

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in ('Guardian Beacon'):
            self.merge_poi("Guardian", "Guardian Beacon", "")
            self.allowed = True
            self.evisualise(None)

        if entry.get("event") == "FSSSignalDiscovered":
            if "NumberStation" in entry.get("SignalName"):
                self.merge_poi("Human", "Unregistered Comms Beacon", body)
            if "Megaship" in entry.get("SignalName"):
                self.merge_poi("Human", "Megaship", body)
            if "ListeningPost" in entry.get("SignalName"):
                self.merge_poi("Human", "Listening Post", body)
            if "CAPSHIP" in entry.get("SignalName"):
                self.merge_poi("Human", "Capital Ship", body)
            if "Generation Ship" in entry.get("SignalName"):
                self.merge_poi("Human", entry.get("SignalName"), body)
            self.allowed = True
            self.evisualise(None)

        if entry.get("event") == "FSSAllBodiesFound":
            # self.remove_poi("Planets", "Unexplored Bodies")
            # CodexTypes.bodycount = CodexTypes.fsscount
            self.allowed = True
            self.visualise()

        if entry.get("event") == "Scan" and entry.get("ScanType") in ("Detailed", "AutoScan"):
            # debug(json.dumps(entry,indent=4))

            # fold the scan data into self.bodies
            if not self.bodies:
                self.bodies = {}
            # only if not a ring or belt
            if entry.get("PlanetClass") or entry.get("StarType"):
                debug("Adding body to self.bodies")
                bd = journal2edsm(entry)
                self.bodies[bd.get("bodyId")] = bd
                # debug(json.dumps(self.bodies, indent=4))
                self.evisualise(None)

            self.allowed = True
            self.visualise()

        if entry.get("event") == "Scan" and entry.get("AutoScan") and entry.get("BodyID") == 1:
            CodexTypes.parentRadius = self.light_seconds("Radius", entry.get("Radius"))
            self.allowed = True

        if entry.get("event") == "SAASignalsFound":
            # if we arent waiting for new data
            bodyName = entry.get("BodyName")
            bodyVal = bodyName.replace(self.system, '')

            debug(f"SAASignalsFound {bodyName}")

            signals = entry.get("Signals")
            for i, v in enumerate(signals):
                found = False
                type = signals[i].get("Type")
                english_name = type.replace("$SAA_SignalType_", "").replace("ical;", "y").replace(";", '')
                if " Ring" in bodyName:
                    cat = "Ring"
                if "$SAA_SignalType_" in type:
                    cat = english_name

                self.merge_poi(cat, english_name, bodyVal)

            self.visualise()
            self.allowed = True

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.hidecodexbtn = tk.IntVar(value=config.getint("Canonn:HideCodex"))

        self.hidecodex = self.hidecodexbtn.get()

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")

        nb.Label(frame, text="Codex Settings").grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Hide Codex Icons", variable=self.hidecodexbtn).grid(row=1, column=0, sticky="NW")

        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('Canonn:HideCodex', self.hidecodexbtn.get())

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


# submitting to a google cloud function
class gSubmitCodex(threading.Thread):
    def __init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):

        threading.Thread.__init__(self)
        # debug("gSubmitCodex({},{},{},{},{},{},{},{},{},{},{})".format((self,cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client)))
        self.cmdr = quote_plus(cmdr.encode('utf8'))
        self.system = quote_plus(system.encode('utf8'))
        self.x = x
        self.y = y
        self.z = z
        self.body = ""
        self.lat = ""
        self.lon = ""
        if body:
            self.body = quote_plus(body.encode('utf8'))
        if lat:
            self.lat = lat
            self.lon = lon

        if is_beta:
            self.is_beta = 'Y'
        else:
            self.is_beta = 'N'

        self.entry = entry

    def run(self):

        debug("sending gSubmitCodex")
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/submitCodex?cmdrName={}".format(self.cmdr)
        url = url + "&system={}".format(self.system)
        url = url + "&body={}".format(self.body)
        url = url + "&x={}".format(self.x)
        url = url + "&y={}".format(self.y)
        url = url + "&z={}".format(self.z)
        url = url + "&latitude={}".format(self.lat)
        url = url + "&longitude={}".format(self.lon)
        url = url + "&entryid={}".format(self.entry.get("EntryID"))
        url = url + "&name={}".format(self.entry.get("Name").encode('utf8'))
        url = url + "&name_localised={}".format(self.entry.get("Name_Localised").encode('utf8'))
        url = url + "&category={}".format(self.entry.get("Category").encode('utf8'))
        url = url + "&category_localised={}".format(self.entry.get("Category_Localised").encode('utf8'))
        url = url + "&sub_category={}".format(self.entry.get("SubCategory").encode('utf8'))
        url = url + "&sub_category_localised={}".format(self.entry.get("SubCategory_Localised").encode('utf8'))
        url = url + "&region_name={}".format(self.entry.get("Region").encode('utf8'))
        url = url + "&region_name_localised={}".format(self.entry.get("Region_Localised").encode('utf8'))
        url = url + "&is_beta={}".format(self.is_beta)

        debug(url)

        r = requests.get(url)

        if not r.status_code == requests.codes.ok:
            error("gSubmitCodex {} ".format(url))
            error(r.status_code)
            error(r.json())


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

        Emitter.__init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)

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
                debug("prefix {}".format(prefix))
                if prefix in guardianSites.gstypes:
                    # This is a guardian structure
                    # self.gstype = guardianSites.gstypes.get(prefix)
                    self.gstype = prefix
                    debug("gstype {} {}".format(prefix, self.gstype))
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
            debug(payload)

            debug(url)
            self.send(payload, url)
        else:
            debug("not a Guardian Settlement")

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

    def __init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
        Emitter.__init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
        self.modelreport = "xxreports"
        self.modeltype = "xxtypes"

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
        debug("signal {} index {}".format(signal_type, index_id))
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
            signal_type, index = self.split_nearest_destination(nearest_destination)
            payload["frontierID"] = index

        return payload

    def getCodexPayload(self):
        payload = self.getBodyPayload(self.entry.get("Name"))
        payload["entryId"] = self.entry.get("EntryID")
        payload["codexName"] = self.entry.get("Name")
        payload["codexNameLocalised"] = self.entry.get("Name_Localised")
        payload["subCategory"] = self.entry.get("SubCategory")
        payload["subCategoryLocalised"] = self.entry.get("SubCategory_Localised")
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
            url = "{}/reporttypes?journalID={}&_limit=1000".format(self.getUrl(), id)
            debug(url)
            r = requests.get("{}/reporttypes?journalID={}&_limit=1000".format(self.getUrl(), id))
            if r.status_code == requests.codes.ok:

                for exc in r.json():
                    codexEmitter.reporttypes["{}".format(exc["journalID"])] = {"endpoint": exc["endpoint"],
                                                                               "location": exc["location"],
                                                                               "type": exc["type"]}

            else:
                error("error in getReportTypes")

    def getExcluded(self):
        if not codexEmitter.excludecodices:
            tempexclude = {}
            r = requests.get("{}/excludecodices?_limit=1000".format(self.getUrl()))
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    tempexclude["${}_name;".format(exc["codexName"])] = True

                codexEmitter.excludecodices = tempexclude

    def run(self):

        self.getExcluded()

        # is this a code entry and do we want to record it?
        if not codexEmitter.excludecodices.get(self.entry.get("Name").lower()) and not self.entry.get(
                "Category") == '$Codex_Category_StellarBodies;':
            self.getReportTypes(self.entry.get("EntryID"))
            url = self.getUrl()

            canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postCodex",
                                {
                                    "cmdr": self.cmdr,
                                    "beta": self.is_beta,
                                    "system": self.system,
                                    "x": self.x,
                                    "y": self.y,
                                    "z": self.z,
                                    "entry": self.entry,
                                    "body": self.body,
                                    "lat": self.lat,
                                    "lon": self.lon,
                                    "client": self.client}
                                )

            jid = self.entry.get("EntryID")
            reportType = codexEmitter.reporttypes.get(str(jid))

            if reportType:
                debug(reportType)
                if reportType.get("location") == "body":
                    payload = self.getBodyPayload(reportType.get("type"))
                    self.modelreport = reportType.get("endpoint")
                else:
                    payload = self.getSystemPayload(reportType.get("type"))
                    self.modelreport = reportType.get("endpoint")
            else:
                payload = self.getCodexPayload()
                self.modelreport = "reportcodices"

            debug("Send Reports {}/{}".format(url, self.modelreport))

            self.send(payload, url)


def test(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
    debug("detected test request")
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

    submit("TestUser", False, "Synuefe CE-R c21-6", 828.1875 , -78 , -105.1875, testentry,
           "Synuefe CE-R c21-6 C 1", 42	, 73, client)

def submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
    codex_entry = (entry.get("event") == "CodexEntry")
    approach_settlement = (entry.get("event") == "ApproachSettlement")
    guardian_codices = (entry.get("EntryID") in [3200200, 3200300, 3200400, 3200500, 3200600])
    guardian_event = (codex_entry and guardian_codices)

    if codex_entry:
        codexEmitter(cmdr, is_beta, entry.get("System"), x, y, z, entry, body, lat, lon, client).start()

    if approach_settlement or guardian_event:
        guardianSites(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client).start()

    if entry.get("event") == "SendText" and entry.get("Message") == "codextest":
        test(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)

    gnosis_station = entry.get("StationName") and entry.get("StationName") == "The Gnosis"
    gnosis_fss = entry.get("FSSSignalDiscovered") and entry.get("SignalName") == "The Gnosis"

    if gnosis_station or gnosis_fss:
        debug("Hey it's The Gnosis!")
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
