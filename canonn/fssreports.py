try:
    from urllib.parse import quote_plus
    from urllib.parse import urlencode
except:
    from urllib import quote_plus
    from urllib import urlencode


import threading
import requests
import sys
import json

import canonn.emitter
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.systems import Systems
import random
import time
from queue import Queue


class fssProcess(threading.Thread):
    def __init__(self, dummy):
        threading.Thread.__init__(self)

    def run(self):
        FSS.process()


class FSS:

    events = Queue()

    @classmethod
    def put(cls, cmdr, system, x, y, z, entry, client, state):
        data = {
            "cmdr": cmdr,
            "system": system,
            "coords": [x, y, z],
            "entry": entry,
            "client": client,
            "odyssey": state.get("Odyssey"),
        }
        Debug.logger.debug("Putting FSS Signal on queue")
        cls.events.put(data)

    @classmethod
    def process(cls):

        payload = []

        while not cls.events.empty():
            # process each of the entries
            data = cls.events.get()
            entry = data.get("entry")

            isStation = entry.get("IsStation")
            if len(entry.get("SignalName")) > 8:
                FleetCarrier = (
                    entry.get("SignalName")
                    and entry.get("SignalName")[-4] == "-"
                    and entry.get("SignalName")[-8] == " "
                    and isStation
                )
            else:
                FleetCarrier = False
            FSSSignalDiscovered = entry.get("event") == "FSSSignalDiscovered"
            USS = "$USS" in entry.get("SignalName")

            if not USS:

                payload.append(
                    {
                        "gameState": {
                            "systemName": data.get("system"),
                            "systemCoordinates": data.get("coords"),
                            "clientVersion": data.get("client"),
                            "isBeta": False,
                            "platform": "PC",
                            "odyssey": data.get("odyssey"),
                        },
                        "rawEvents": [entry],
                        "eventType": entry.get("event"),
                        "cmdrName": data.get("cmdr"),
                    }
                )
                Debug.logger.debug(payload)

        if len(payload) > 0:
            FSS.postFSS(payload)

    @classmethod
    def postFSS(cls, payload):
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent"

        Debug.logger.debug("posting FSS")
        Debug.logger.debug(payload)
        r = requests.post(
            url, data=json.dumps(payload, ensure_ascii=False).encode("utf8")
        )
        if not r.status_code == requests.codes.ok:
            headers = r.headers
            contentType = str(headers["content-type"])
            if "json" in contentType:
                Debug.logger.error(json.dumps(r.json()))
            else:
                Debug.logger.error(r.content)
            Debug.logger.error(r.status_code)


def submit(cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client, state):

    if entry.get("event") == "FSSSignalDiscovered" and not is_beta:
        FSS.put(cmdr, system, x, y, z, entry, client, state)

    if (
        entry.get("event")
        in (
            "StartJump",
            "Location",
            "Docked",
            "Shutdown",
            "ShutDown",
            "SupercruiseExit",
            "SupercruiseEntry ",
        )
        and not is_beta
    ):
        Debug.logger.debug("FSS Process")
        fssProcess(None).start()
