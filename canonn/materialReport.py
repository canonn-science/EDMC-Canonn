# -*- coding: utf-8 -*-
try:
    from urllib.parse import quote_plus
except:
    from urllib import quote_plus

import threading
import requests

import sys
import json
from canonn.emitter import Emitter
from canonn.debug import Debug
from canonn.debug import debug, error


class MaterialsCollected(Emitter):

    def __init__(self, cmdr, is_beta, system, station, entry, client, lat, lon, body, state, allegiance, x, y, z, DistFromStarLS):
        self.state = state
        self.allegiance = allegiance
        self.DistFromStarLS = DistFromStarLS
        Debug.logger.debug("Material rep star dist "+str(self.DistFromStarLS))
        Debug.logger.debug("Material rep FacState "+str(self.state))
        Debug.logger.debug("Material rep FacAllegiance "+str(self.allegiance))
        Emitter.__init__(self, cmdr, is_beta, system, x, y,
                         z, entry, body, lat, lon, client)

        self.modelreport = "materialreports"

    def setPayload(self):
        payload = {}
        payload["system"] = self.system
        if self.body != None:
            payload["body"] = self.body
            payload["latitude"] = self.lat
            payload["longitude"] = self.lon
        else:
            payload["body"] = None
            payload["latitude"] = self.lat
            payload["longitude"] = self.lon
        if self.entry["Category"] == "Encoded":
            payload["collectedFrom"] = "scanned"
        else:
            payload["collectedFrom"] = "collected"
        payload["category"] = self.entry["Category"]
        payload["journalName"] = self.entry["Name"]
        payload["count"] = self.entry["Count"]
        payload["distanceFromMainStar"] = self.DistFromStarLS
        payload["coordX"] = self.x
        payload["coordY"] = self.y
        payload["coordZ"] = self.z
        payload["isbeta"] = self.is_beta
        payload["clientVersion"] = self.client
        payload["factionState"] = self.state
        payload["factionAllegiance"] = self.allegiance

        return payload


class MaterialsReward(Emitter):
    Category = {
        "$MICRORESOURCE_CATEGORY_Manufactured;": "Manufactured",
        "$MICRORESOURCE_CATEGORY_Encoded;": "Encoded",
        "$MICRORESOURCE_CATEGORY_Raw;": "Raw", }

    def __init__(self, cmdr, is_beta, system, station, entry, client, lat, lon, body, state, x, y, z, DistFromStarLS):
        self.state = state
        self.allegiance = allegiance
        self.DistFromStarLS = DistFromStarLS
        Debug.logger.debug("Material rep star dist "+str(self.DistFromStarLS))
        Debug.logger.debug("Material rep FacState "+str(self.state))
        Debug.logger.debug("Material rep FacAllegiance "+str(self.allegiance))
        Emitter.__init__(self, cmdr, is_beta, system, x, y,
                         z, entry, body, lat, lon, client)

        self.modelreport = "materialreports"

    def setPayload(self):
        payload = {}
        payload["system"] = self.system
        if self.body != None:
            payload["body"] = self.body
            payload["latitude"] = self.lat
            payload["longitude"] = self.lon
        else:
            payload["body"] = None
            payload["latitude"] = None
            payload["longitude"] = None
        payload["collectedFrom"] = "missionReward"
        payload["category"] = Category[self.entry["MaterialsReward"][0]["Category"]]
        payload["journalName"] = self.entry["MaterialsReward"][0]["Name"]
        # payload["journalLocalised"]=unicode(self.entry["MaterialsReward"][0].get("Name_Localised"))
        payload["count"] = self.entry["MaterialsReward"][0]["Count"]
        payload["distanceFromMainStar"] = self.DistFromStarLS
        payload["coordX"] = self.x
        payload["coordY"] = self.y
        payload["coordZ"] = self.z
        payload["isbeta"] = self.is_beta
        payload["clientVersion"] = self.client
        payload["factionState"] = self.state
        payload["factionAllegiance"] = self.allegiance
        Debug.logger.debug(payload)
        return payload


def matches(d, field, value):
    return field in d and value == d[field]


def submit(cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, entry, x, y, z, body, lat, lon, client):
    if entry["event"] == "MaterialCollected":
        Debug.logger.debug(entry)
        MaterialsCollected(cmdr, is_beta, system, station, entry, client, lat, lon,
                           body, SysFactionState, SysFactionAllegiance, x, y, z, DistFromStarLS).start()
    if "MaterialsReward" in entry:
        Debug.logger.debug(entry)
        MaterialsReward(cmdr, is_beta, system, station, entry, client, lat, lon, body,
                        SysFactionState, SysFactionAllegiance, x, y, z, DistFromStarLS).start()
