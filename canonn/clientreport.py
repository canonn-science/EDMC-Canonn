# assume python 3 before trying python 2.7
try:
    from urllib.parse import quote_plus
except:
    from urllib import quote_plus

import json
import requests
import sys
import threading
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.emitter import Emitter
from canonn.release import Release

import canonn.emitter


class clientReport(Emitter):
    done = False

    def __init__(self, cmdr, is_beta, client):

        self.modelreport = "clientreports"
        Emitter.__init__(self, cmdr, is_beta, None, None, None,
                         None, None, None, None, None, client)

    def setPayload(self):
        payload = {}
        payload["cmdrName"] = self.cmdr
        payload["isBeta"] = self.is_beta
        payload["clientVersion"] = self.client
        if Release.get_auto() == 1:
            payload["AutoUpdateDisabled"] = False
        else:
            payload["AutoUpdateDisabled"] = True

        return payload

    def run(self):
        if not clientReport.done:
            clientReport.done = True
            Debug.logger.debug("sending client report")
            # configure the payload
            payload = self.setPayload()
            url = self.getUrl()
            self.send(payload, url)
            Debug.logger.debug("Google Client Report")
            canonn.emitter.post("https://us-central1-canonn-api-236217.cloudfunctions.net/submitCient",
                                {
                                    "cmdr": payload.get("cmdrName"),
                                    "beta": payload.get("isBeta"),
                                    "client": payload.get("clientVersion"),
                                    "autoupdate": payload.get("AutoUpdateDisabled")
                                })


def submit(cmdr, is_beta, client, entry):
    if entry.get("event") in ("Location", "StartUp"):
        clientReport(cmdr, is_beta, client).start()

    if entry.get("event") in ("Fileheader"):
        canonn.emitter.post(
            "https://us-central1-canonn-api-236217.cloudfunctions.net/postGameVersion", event)
