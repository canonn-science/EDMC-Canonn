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
from canonn.release import Release

import canonn.emitter


def submit(cmdr, is_beta, client, entry):
    if entry.get("event") in ("Location", "StartUp"):
        # clientReport(cmdr, is_beta, client).start()
        AutoUpdateDisabled = True
        if Release.get_auto() == 1:
            AutoUpdateDisabled = False

        canonn.emitter.post(
            "https://europe-west1-canonn-api-236217.cloudfunctions.net/submitClient",
            {
                "cmdr": cmdr,
                "beta": is_beta,
                "client": client,
                "autoupdate": AutoUpdateDisabled,
            },
        )
