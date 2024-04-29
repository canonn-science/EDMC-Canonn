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
from canonn.systems import Systems


class gSubmitNHSS(threading.Thread):
    def __init__(self, cmdr, system, x, y, z, threat_level):
        threading.Thread.__init__(self)
        self.cmdr = quote_plus(cmdr.encode("utf8"))
        self.system = quote_plus(system.encode("utf8"))
        self.x = x
        self.y = y
        self.z = z
        self.threat_level = threat_level

    def run(self):

        Debug.logger.debug("sending gSubmitNHSS")
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/submitNHSS?cmdrName={}".format(
            self.cmdr
        )
        url = url + "&systemName={}".format(self.system)
        url = url + "&x={}".format(self.x)
        url = url + "&y={}".format(self.y)
        url = url + "&z={}".format(self.z)
        url = url + "&threat_level={}".format(self.threat_level)

        r = requests.get(url)

        if not r.status_code == requests.codes.ok:
            Debug.logger.error("gSubmitNHSS {} ".format(url))
            Debug.logger.error(r.status_code)
            Debug.logger.error(r.json())


"""
    { 
        "timestamp":"2018-10-07T13:03:02Z", 
        "event":"USSDrop", 
        "USSType":"$USS_Type_NonHuman;", 
        "USSType_Localised":"Non-Human signal source", 
        "USSThreat":4 
    }
"""

"""
Defining a class so that we can store the ones already seen and avoid resending. 
"""


class NHSS:

    # this is our store
    fss = {}

    def __init__(self, cmdr, is_beta, system, entry, client):

        self.system = system
        self.cmdr = cmdr
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client = client
        self.modelreport = "nhssreports"

        if self.entry["event"] == "FSSSignalDiscovered":
            threatLevel = self.entry.get("ThreatLevel")
            type = "FSS"
        else:
            threatLevel = self.entry.get("USSThreat")
            type = "Drop"

        x, y, z = Systems.edsmGetSystem(self.system)
        gSubmitNHSS(self.cmdr, self.system, x, y, z, threatLevel).start()


def submit(cmdr, is_beta, system, station, entry, client):

    # USS and FFS
    if (
        entry["event"] in ("USSDrop", "FSSSignalDiscovered")
        and entry.get("USSType") == "$USS_Type_NonHuman;"
    ):

        # The have different names for teh same thing so normalise
        if entry["event"] == "FSSSignalDiscovered":
            threatLevel = entry.get("ThreatLevel")
        else:
            threatLevel = entry.get("USSThreat")

        # see if you have system and threat levels store
        # Thsi will fail if it a new threat level in the current system
        try:
            globalfss = NHSS.fss.get(system)
            oldthreat = globalfss.get(threatLevel)
            # debug(globalfss)
        except:
            oldthreat = False

        if oldthreat:
            Debug.logger.debug("Threat level already recorded here " + str(threatLevel))

        else:
            # debug("Threat {}".format(threatLevel))
            try:
                # set the threatlevel for the system
                NHSS.fss[system][threatLevel] = True
            except:
                # we couldnt find teh system so lets define it
                NHSS.fss[system] = {threatLevel: True}

            NHSS(cmdr, is_beta, system, entry, client)
