try:
    from urllib.parse import quote_plus
    from tkinter import Frame
    import tkinter as tk
except:
    from urllib import quote_plus
    from Tkinter import Frame
    import Tkinter as tk

from canonn.debug import Debug
from canonn.debug import debug, error
import canonn.emitter
import threading
import requests
import sys
import json


class whiteListGetter(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self.callback = callback

    def run(self):
        Debug.logger.debug("getting whiteList")
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/whitelist"
        r = requests.get(url)

        if not r.status_code == requests.codes.ok:
            Debug.logger.error("whiteListGetter {} ".format(url))
            Debug.logger.error(r.status_code)
            Debug.logger.error(r.json())
            results = []
        else:
            results = r.json()

        self.callback(results)


class whiteListSetter(threading.Thread):

    def __init__(self, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):
        threading.Thread.__init__(self)
        self.cmdr = cmdr
        self.system = system
        self.odyssey = state.get("Odyssey")
        self.is_beta = is_beta
        self.station = station
        self.odyssey = station
        self.body = body
        self.entry = entry
        self.state = state
        self.x = x
        self.y = y
        self.z = z
        self.lat = lat
        self.lon = lon
        self.client = client

    def run(self):

        canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/postEvent",
            {
                "gameState": {
                    "systemName": self.system,
                    "systemCoordinates": [self.x, self.y, self.z],
                    "bodyName": self.body,
                    "station": self.station,
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
        


'''
  Going to declare this aa a frame so I can run a time
'''


class whiteList(Frame):

    whitelist = []

    def __init__(self, parent):
        Frame.__init__(
            self,
            parent
        )

    '''
        if all the keys match then return true
    '''
    @classmethod
    def matchkeys(cls, event, entry):

        ev = json.loads(event)
        for key in ev.keys():
            if not entry.get(key) == ev.get(key):
                return False

        return True

    @classmethod
    def journal_entry(cls, cmdr, is_beta, system, station, entry, state, x, y, z, body, lat, lon, client):

        for event in whiteList.whitelist:

            if cls.matchkeys(event.get("definition"), entry):
                Debug.logger.debug("Match {}".format(entry.get("event")))
                whiteListSetter(cmdr, is_beta, system, station, entry,
                                state, x, y, z, body, lat, lon, client).start()

    # we will only load this on startup

    def fetchData(self):
        whiteListGetter(self.whiteListCallback).start()

    def whiteListCallback(self, data):
        whiteList.whitelist = data
