try:
    from urllib.parse import quote_plus
    from urllib.parse import urlencode
except:
    from urllib import quote_plus
    from urllib import urlencode


import threading
from queue import Queue
import requests
import sys
import json
from canonn.emitter import Emitter
import canonn.emitter
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.systems import Systems
import random
import time


class fleetProcess(threading.Thread):
    def __init__(self, dummy):
        threading.Thread.__init__(self)

    def run(self):
        Fleet.process()


class Fleet():

    carriers = Queue()

    @classmethod
    def put(cls, system, x, y, z, entry):
        data = {"system": system, "coords": [x, y, z], "entry": entry}
        debug(data)
        cls.carriers.put(data)

    @classmethod
    def process(cls):
        while not cls.carriers.empty():
            # process each of the entries
            data = cls.carriers.get()
            entry = data.get("entry")
            isStation = (entry.get("IsStation"))
            FleetCarrier = (entry.get("SignalName") and entry.get(
                "SignalName")[-4] == '-' and entry.get("SignalName")[-8] == ' ' and isStation)
            if FleetCarrier:
                payload = {
                    "StationName": entry.get("SignalName")[-7:],
                    "CarrierName": entry.get("SignalName")[:-8],
                    "StarSystem": data.get("system"),
                    "StarPos":  data.get("coords"),
                    "timestamp": entry.get("timestamp"),
                    "StationServices": None
                }
                Fleet.postCarrier(payload)

    @classmethod
    def postCarrier(cls, m):
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/postFleetCarriers?serial_no={}&system={}&x={}&y={}&z={}&timestamp={}&name={}"
        name = m.get("CarrierName")
        serial = m.get("StationName")
        system = m.get("StarSystem")
        x = m.get("StarPos")[0]
        y = m.get("StarPos")[1]
        z = m.get("StarPos")[2]
        timestamp = m.get("timestamp")

        payload = url.format(serial, system, x, y, z, timestamp,  name)
        debug(payload)
        r = requests.get(payload)
        if not r.status_code == requests.codes.ok:
            headers = r.headers
            contentType = str(headers['content-type'])
            if 'json' in contentType:
                error(json.dumps(r.content))
            else:
                error(r.content)
            error(r.status_code)


def submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
    if entry.get("event") == "FSSSignalDiscovered" and not is_beta:
        debug("FleetCarrier Put")
        Fleet.put(system, x, y, z, entry)

    if entry.get("event") in ("StartJump", "Location", "Docked") and not is_beta:
        debug("FleetCarrier Process")
        fleetProcess(None).start()
