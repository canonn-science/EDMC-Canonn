import threading
import requests
import sys
import json
from canonn.debug import Debug
from canonn.debug import debug, error


class postJson(threading.Thread):
    def __init__(self, url, payload):
        threading.Thread.__init__(self)
        self.url = url
        self.payload = payload

    def run(self):
        Debug.logger.debug("emitter.post")

        r = requests.post(self.url, data=json.dumps(self.payload, ensure_ascii=False).encode('utf8'),
                          headers={"content-type": "application/json"})
        if not r.status_code == requests.codes.ok:
            Debug.logger.error(json.dumps(self.payload))
            headers = r.headers
            contentType = str(headers['content-type'])
            if 'json' in contentType:
                Debug.logger.error(json.dumps(r.content))
            else:
                Debug.logger.error(r.content)
            Debug.logger.error(r.status_code)
        else:
            Debug.logger.debug("emitter.post success")
            Debug.logger.debug(json.dumps(r.json(), indent=4))


def post(url, payload):
    postJson(url, payload).start()


class Emitter(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    urls = {
        "live": "https://api.canonn.tech",
        "staging": "https://api.canonn.tech:2053",
        "development":  "https://api.canonn.tech:2083"
    }

    route = ""

    def __init__(self, cmdr, is_beta, system, x, y, z, entry, body, lat, lon, client):
        threading.Thread.__init__(self)
        self.cmdr = cmdr
        self.system = system
        self.x = x
        self.y = y
        self.z = z
        self.body = body
        self.lat = lat
        self.lon = lon
        self.is_beta = is_beta
        if entry:
            self.entry = entry.copy()
        self.client = client
        Emitter.setRoute(is_beta, client)
        self.modelreport = "clientreports"

    @classmethod
    def setRoute(cls, is_beta, client):
        if Emitter.route:
            return Emitter.route
        else:
            # first check to see if we are an official release
            repo, tag = client.split(".", 1)
            r = requests.get(
                "https://api.github.com/repos/canonn-science/{}/releases/tags/{}".format(repo, tag))
            j = r.json()
            if r.status_code == 404:
                Debug.logger.debug("Release not in github")
                Emitter.route = Emitter.urls.get("development")
            elif j.get("prerelease"):
                Debug.logger.debug("Prerelease in github")
                Emitter.route = Emitter.urls.get("staging")
            else:
                Debug.logger.debug("Release in github")
                Emitter.route = Emitter.urls.get("live")

            r = requests.get(
                "{}/clientroutes?clientVersion={}".format(Emitter.urls.get("live"), client))
            j = r.json()
            if not r.status_code == requests.codes.ok or not j:
                Debug.logger.debug("Using {}".format(Emitter.route))
            else:
                Emitter.route = j[0].get("route")
                Debug.logger.debug(
                    "Route override to {}".format(Emitter.route))

        return Emitter.route

    def getUrl(self):
        if self.is_beta:
            url = Emitter.urls.get("staging")
        else:
            url = Emitter.route
        return url

    def setPayload(self):
        payload = {}
        payload["cmdrName"] = self.cmdr
        payload["systemName"] = self.system
        payload["isBeta"] = self.is_beta
        payload["clientVersion"] = self.client
        return payload

    def run(self):

        # configure the payload
        payload = self.setPayload()
        url = self.getUrl()
        self.send(payload, url)

    def send(self, payload, url):
        fullurl = "{}/{}".format(url, self.modelreport)
        r = requests.post(fullurl, data=json.dumps(payload, ensure_ascii=False).encode(
            'utf8'), headers={"content-type": "application/json"})

        if not r.status_code == requests.codes.ok:
            Debug.logger.error("{}/{}".format(url, self.modelreport))
            Debug.logger.error(r.status_code)
            headers = r.headers
            contentType = str(headers['content-type'])
            Debug.logger.error(contentType)
            if 'json' in contentType:
                Debug.logger.error(json.dumps(r.json()))
            else:
                if "Offline for Maintenance" in str(r.content):
                    Debug.logger.error("Canonn API Offline")
                else:
                    Debug.logger.error(r.content)
            Debug.logger.error(json.dumps(payload))
        else:
            Debug.logger.debug("{}?id={}".format(fullurl, r.json().get("id")))
