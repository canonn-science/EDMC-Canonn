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

        r = requests.post(
            self.url,
            data=json.dumps(self.payload, ensure_ascii=False).encode("utf8"),
            headers={"content-type": "application/json"},
        )
        if not r.status_code == requests.codes.ok:
            Debug.logger.error(json.dumps(self.payload))
            headers = r.headers
            contentType = str(headers["content-type"])
            if "json" in contentType:
                Debug.logger.error(json.dumps(r.content))
            else:
                Debug.logger.error(r.content)
            Debug.logger.error(r.status_code)
        else:
            Debug.logger.debug("emitter.post success")
            Debug.logger.debug(json.dumps(r.json(), indent=4))


def post(url, payload):
    postJson(url, payload).start()
