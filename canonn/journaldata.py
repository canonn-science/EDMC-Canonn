import json
import os
import requests
import sys
import threading
import time
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.emitter import Emitter

'''
Added the above events to: https://api.canonn.tech:2053/excludeevents
-DM
'''


class CanonnJournal(Emitter):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''

    exclusions = {}

    def __init__(self, cmdr, is_beta, system, station, entry, client, body, lat, lon):
        Emitter.__init__(self, cmdr, is_beta, system, None,
                         None, None, entry, None, None, None, client)
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client = client
        self.eventAltName = entry.get("Name")
        if entry.get("bodyName"):
            self.body = entry.get("BodyName")
        else:
            self.body = body

        if entry.get("Latitude"):
            self.lat = entry.get("Latitude")
        else:
            self.lat = lat

        if entry.get("Longitude"):
            self.lon = entry.get("Longitude")
        else:
            self.lon = lon
        self.modelreport = "reportevents"

    def setPayload(self):
        payload = {}
        payload["systemName"] = self.system
        payload["cmdrName"] = self.cmdr
        payload["rawJson"] = self.entry
        payload["eventName"] = self.entry["event"]
        payload["eventAltName"] = self.eventAltName
        payload["clientVersion"] = self.client
        payload["isBeta"] = self.is_beta
        if self.body:
            payload["BodyName"] = self.body
            payload["Latitude"] = self.lat
            payload["Longitude"] = self.lon
        return payload

    @classmethod
    def get_excludes(cls):
        # hard coded may as well get the exclude from live
        url = "https://api.canonn.tech"
        tempexcludes = {}
        r = requests.get("{}/excludeevents?_limit=1000".format(url))

        if r.status_code == requests.codes.ok:
            # populate a local variable so other threads dont see incomplete results
            for exc in r.json():
                tempexcludes[exc["eventName"]] = True
            CanonnJournal.exclusions = tempexcludes
            #Debug.logger.debug("Jouurnal excludes got")
        else:
            Debug.logger.error("{}/excludeevents".format(url))

    def run(self):
        url = self.getUrl()

        payload = {}
        payload["systemName"] = self.system
        payload["cmdrName"] = self.cmdr
        payload["rawJson"] = self.entry
        payload["eventName"] = self.entry["event"]
        payload["eventAltName"] = self.eventAltName
        payload["clientVersion"] = self.client
        if self.body:
            payload["BodyName"] = self.body
            payload["Latitude"] = self.lat
            payload["Longitude"] = self.lon

        payload["isBeta"] = self.is_beta

        included_event = not CanonnJournal.exclusions.get(
            self.entry.get("event"))

        if included_event:
            payload = self.setPayload()
            self.send(payload, url)


'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
'''


class Exclude(threading.Thread):
    def __init__(self, callback):
        # Debug.logger.debug("initialise POITYpes Thread")
        threading.Thread.__init__(self)
        self.callback = callback

    def run(self):
        Debug.logger.debug("getting excludes from strapi")
        self.callback()
        # Debug.logger.debug("poitypes Callback Complete")


def plugin_start(plugin_dir):
    # CanonnJournal.exclusions=
    tempexcludes = {}
    json.loads(open(os.path.join(plugin_dir, 'data/excludeevents.json')).read())
    for exc in json.loads(open(os.path.join(plugin_dir, 'data/excludeevents.json')).read()):
        tempexcludes[exc["eventName"]] = True

    CanonnJournal.exclusions = tempexcludes

    Debug.logger.debug(
        "Journal excludes got now firing off thread to update them")
    Exclude(CanonnJournal.get_excludes).start()


def submit(cmdr, is_beta, system, station, entry, client, body, lat, lon):
    if CanonnJournal.exclusions:
        included_event = not CanonnJournal.exclusions.get(entry.get("event"))

    if included_event:
        CanonnJournal(cmdr, is_beta, system, station,
                      entry, client, body, lat, lon).start()
