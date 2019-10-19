import Tkinter as tk
import emitter
import json
import myNotebook as nb
import os
import requests
import sys
import threading
import urllib2
from Tkinter import Frame
from config import config
from debug import Debug
from debug import debug, error
from emitter import Emitter
from urllib import quote_plus


class poiTypes(threading.Thread):
    def __init__(self, system, callback):
        threading.Thread.__init__(self)
        self.system = system
        self.callback = callback

    def run(self):
        debug("running poitypes")
        self.callback(self.system)

    def recycle(self):
        print "Recycling Labels"

        for label in self.lt:
            label.grid_remove()
        for label in self.lp:
            label.grid_remove()

            # Frame.destroy(self)


class saaScan():

    def __init__(self):
        debug("We only use class methods here")

    @classmethod
    def journal_entry(cls, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        if entry.get("event") == "SAASignalsFound":
            emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postSAA",
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


class CodexTypes(Frame):
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

    def __init__(self, parent, gridrow):
        "Initialise the ``Patrol``."
        Frame.__init__(
            self,
            parent
        )

        self.waiting = True

        self.hidecodexbtn = tk.IntVar(value=config.getint("Canonn:HideCodex"))
        self.hidecodex = self.hidecodexbtn.get()

        self.container = Frame(self)
        self.container.columnconfigure(1, weight=1)
        # self.tooltip=Frame(self)
        # self.tooltip.columnconfigure(1, weight=1)
        # self.tooltip.grid(row = 1, column = 0,sticky="NSEW")

        # self.tooltiplist=tk.Frame(self.tooltip)
        self.tooltiplist = tk.Frame(self)

        self.images = {}
        self.labels = {}
        self.tooltipcol1 = []
        self.tooltipcol2 = []

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
        self.grid(row=gridrow, column=0)
        self.container.grid(row=0, column=0, sticky="W")
        self.poidata = []
        # self.tooltip.grid_remove()
        self.tooltiplist.grid_remove()
        self.grid_remove()

    def getdata(self, system):
        self.waiting = True
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/poiListSignals?system={}".format(
            quote_plus(system.encode('utf8')))
        debug(url)
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            self.poidata = r.json()

        bodytypes = {'Metal-rich body': [], 'Earth-like world': [], 'Water world': [], 'Ammonia world': []}

        tform = []

        usystem = urllib2.unquote(system)

        edsm = "https://www.edsm.net/api-system-v1/bodies?systemName={}".format(quote_plus(system.encode('utf8')))
        debug(edsm)
        r = requests.get(edsm)
        if r.status_code == requests.codes.ok:

            bodies = r.json().get("bodies")
            if bodies:
                CodexTypes.bodycount = len(bodies)
                debug("bodycount: {}".format(CodexTypes.bodycount))
                for b in bodies:
                    debug(b.get("subType"))

                    if b.get("subType") in bodytypes.keys():
                        debug(" NAME {}".format(b.get("name")))
                        debug(usystem)
                        debug(b.get("name").replace(usystem, ''))
                        bodytypes[b.get("subType")].append(b.get("name").replace(usystem, ''))

                    if b.get('terraformingState') == 'Candidate for terraforming':
                        self.merge_poi("Planets", "Terraformable", b.get("name").replace(usystem, ''))

                    if b.get('type') == 'Planet' and b.get('volcanismType') != 'No volcanism':
                        self.merge_poi("Geology", b.get('volcanismType'), b.get("name").replace(usystem, ''))

                    # water ammonia etc
                    if b.get('subType') in CodexTypes.body_types.keys():
                        self.merge_poi("Planets", CodexTypes.body_types.get(b.get('subType')),
                                       b.get("name").replace(usystem, ''))
                    debug("Orbit {} {}".format(b.get('orbitalPeriod'),b.get("name")))
                    if b.get('orbitalPeriod'):
                        if float(b.get('orbitalPeriod')) <= 0.042:
                            self.merge_poi("Tourist", 'Fast Orbital Period', b.get("name").replace(usystem, ''))


        else:
            CodexTypes.bodycount = 0
            debug("bodycount: {}".format(CodexTypes.bodycount))

        self.waiting = False

    def enter(self, event):

        type = event.widget["text"]
        # clear it if it exists
        for col in self.tooltipcol1:
            col["text"] = ""
            col.grid_remove()
        for col in self.tooltipcol2:
            col["text"] = ""
            col.grid_remove()

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
        self.tooltiplist.grid_remove()

    def addimage(self, name, col):

        grey = "{}_grey".format(name)
        self.images[name] = tk.PhotoImage(file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(name)))
        self.images[grey] = tk.PhotoImage(file=os.path.join(CodexTypes.plugin_dir, "icons", "{}.gif".format(grey)))
        self.labels[name] = tk.Label(self.container, image=self.images.get(grey), text=name)
        self.labels[name].grid(row=0, column=col)

        self.labels[name].bind("<Enter>", self.enter)
        self.labels[name].bind("<Leave>", self.leave)
        self.labels[name].bind("<ButtonPress>", self.enter)

    def set_image(self, name, enabled):
        grey = "{}_grey".format(name)

        if enabled:
            setting = name
        else:
            setting = grey

        self.labels[name]["image"] = self.images.get(setting)

        if enabled:
            self.labels[name].grid()
        else:
            self.labels[name].grid_remove()

    def merge_poi(self, hud_category, english_name, body):
        debug("Merge POI")
        found = False
        signals = self.poidata
        for i, v in enumerate(signals):
            if signals[i].get("english_name") == english_name and signals[i].get("hud_category") == hud_category:
                if not body in signals[i].get("body").split(','):
                    self.poidata[i]["body"] = "{},{}".format(signals[i].get("body"), body)
                found = True
        if not found:
            self.poidata.append({"hud_category": hud_category, "english_name": english_name, "body": body})

    def remove_poi(self, hud_category, english_name):
        signals = self.poidata
        for i, v in enumerate(signals):
            if signals[i].get("english_name") == english_name and signals[i].get("hud_category") == hud_category:
                del self.poidata[i]
                self.visualise()

    def visualise(self):

        debug("visualise")
        # we may want to try again if the data hasn't been fetched yet
        if self.waiting:
            debug("Still waiting");
            self.after(1000, self.visualise)
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

            if self.poidata:
                self.grid()
                for r in self.poidata:
                    debug(r)
                    self.set_image(r.get("hud_category"), True)
            else:
                self.grid_remove()

    def journal_entry(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        debug("CodeTypes journal_entry")

        if entry.get("event") in ("FSDJump"):
            # To avoid having check data we will assume we have some by now
            self.visualise()

        if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            # go fetch some data.It will 
            poiTypes(entry.get("StarSystem"), self.getdata).start()
            self.grid_remove()

        if entry.get("event") in ("Location", "StartUp"):
            debug("Looking for POI data in {}".format(system))
            poiTypes(system, self.getdata).start()
            ## lets give it 5 seconds
            self.after(5000, self.visualise)

        if entry.get("event") in ("FSSDiscoveryScan"):
            CodexTypes.fsscount = entry.get("BodyCount")
            debug("body reconciliation: {} {}".format(CodexTypes.bodycount, CodexTypes.fsscount))
            if CodexTypes.fsscount > CodexTypes.bodycount:
                self.merge_poi("Planets", "Unexplored Bodies", "")
                self.visualise()

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in (
                '$Fixed_Event_Life_Ring;', '$Fixed_Event_Life_Cloud;'):
            found = False
            if not self.waiting:
                signals = self.poidata
                for i, v in enumerate(signals):
                    if signals[i].get("english_name") == 'Life Cloud' and entry.get(
                            "SignalName") == '$Fixed_Event_Life_Cloud;':
                        found = True
                    if signals[i].get("english_name") == 'Life Ring' and entry.get(
                            "SignalName") == '$Fixed_Event_Life_Ring;':
                        found = True
                if not found:
                    if entry.get("SignalName") == '$Fixed_Event_Life_Ring;':
                        cloudtype = 'Life Ring'
                    else:
                        cloudtype = 'Life Cloud'
                    self.poidata.append({"hud_category": 'Cloud', "english_name": cloudtype})
                    debug(poidata)
                    self.visualise()

        if entry.get("event") == "FSSSignalDiscovered" and entry.get("SignalName") in ('Guardian Beacon'):
            found = False
            if not self.waiting:
                signals = self.poidata
                for i, v in enumerate(signals):
                    if signals[i].get("english_name") == 'Guardian Beacon':
                        found = True
                if not found:
                    self.poidata.append({"hud_category": 'Guardian', "english_name": 'Guardian Beacon'})
                    self.visualise()

        if entry.get("event") == "Scan" and entry.get("ScanType") == "Detailed":
            self.remove_poi("Planets", "Unexplored Bodies")
            body = entry.get("BodyName").replace(system, '')
            english_name = CodexTypes.body_types.get(entry.get("PlanetClass"))
            if entry.get("PlanetClass") in CodexTypes.body_types.keys():
                debug("PlanetClass".format(entry.get("PlanetClass")))
                self.merge_poi("Planets", english_name, body)
            debug("Volcanism {} landable {}".format(entry.get("Volcanism"), entry.get("Landable")))
            if entry.get("Volcanism") != "" and entry.get("Landable"):
                debug("oh come on!")
                self.merge_poi("Geology", entry.get("Volcanism"), body)
            if entry.get('TerraformState') == 'Terraformable':
                self.merge_poi("Planets", "Terraformable", body)

            if entry.get('OrbitalPeriod'):
                if float(entry.get('OrbitalPeriod')) < 3600:
                    self.merge_poi("Tourist", "Fast Orbit", body)

            self.visualise()

        if entry.get("event") == "SAASignalsFound":
            # if we arent waiting for new data
            bodyName = entry.get("BodyName")
            bodyVal = bodyName.replace(system, '')

            debug("SAASignalsFound")

            if not self.waiting:
                signals = entry.get("Signals")
                for i, v in enumerate(signals):
                    found = False
                    type = signals[i].get("Type")
                    english_name = type.replace("$SAA_SignalType_", "").replace("ical;", "y").replace(";", '')
                    if " Ring" in bodyName:
                        cat = "Ring"
                    if "$SAA_SignalType_" in type:
                        cat = english_name
                    for x, r in enumerate(self.poidata):
                        if r.get("hud_category") == cat and r.get("english_name") == english_name:
                            found = True
                            if not bodyVal in r.get("body"):
                                self.poidata[x]["body"] = "{},{}".format(self.poidata[x]["body"], bodyVal)
                    if not found:
                        self.set_image(cat, True)
                        self.poidata.append({'body': bodyVal, 'hud_category': cat, 'english_name': english_name})
                        self.visualise()
                    debug(self.poidata)
                    debug("cat {} name  {} body {}".format(cat, english_name, bodyVal))

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
        # self.visible()

    def visible(self):

        noicons = (self.hidecodex == 1)

        if noicons:
            self.grid_remove()
            self.isvisible = False
            return False
        else:
            self.grid()
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

        Emitter.__init__(self, cmdr, is_beta, system, x, y, z, entry, entry.get("BodyName"), entry.get("Latitude"),
                         entry.get("Longitude"), client)

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

        if ":" in entry.get("Name"):
            prefix, suffix = entry.get("Name").split(':')
            self.index = self.get_index(entry.get("Name"))

            self.modelreport = None

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
        if self.modelreport and self.system:
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

            emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postCodex",
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
        "Latitude": -10.090128, "Longitude": 114.505409}
    submit("LCU No Fool Like One", False, "Synuefe LY-I b42-2", 814.71875, -222.78125, -151.15625, testentry,
           "Synuefe LY-I b42-2 C 2", -10.090128, 114.505409, client)

    testentry = {"timestamp": "2019-10-10T10:23:32Z",
                 "event": "ApproachSettlement",
                 "Name": "$Ancient_Tiny_003:#index=1;", "Name_Localised": "Guardian Structure",
                 "SystemAddress": 5079737705833,
                 "BodyID": 25, "BodyName": "Synuefe LY-I b42-2 C 2",
                 "Latitude": 52.681084, "Longitude": 115.240822}
    submit("LCU No Fool Like One", False, "Synuefe LY-I b42-2", 814.71875, -222.78125, -151.15625, testentry,
           "Synuefe LY-I b42-2 C 2", 52.681084, 115.240822, client)


def submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
    if entry["event"] == "CodexEntry":
        codexEmitter(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client).start()

    if entry["event"] == "ApproachSettlement":
        guardianSites(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client).start()

    if entry.get("event") == "SendText" and entry.get("Message") == "codextest":
        test(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client)
