from email import header
from random import Random


import time
import sys
import json
import plug

from canonn.debug import Debug


# 127.0.0.1:5010

this = sys.modules[__name__]


def getConfig(rtype, config_data):
    config = config_data["types"][rtype]
    position = config_data["positions"][config["position"]]
    config["posx"] = position["x"]
    config["posy"] = position["y"]
    return config


def getData(data, config, type):
    if type == "patrol":
        data = {
            "message": "System: {}\n\nRating: {}\n\nDistance: {}ly\n\nInstructions: {}".format(data["system"], data["rating"], data["distance"], data["text"]),
            "header_text": "{} - {}ly away".format(config["header"]["text"], data["distance"]),
        }
        return data
    elif type == "startup":
        data = {
            "header_text": "//Canonn overlay//",
            "message": "Canonn overlay started",
        }
        return data
    elif type == "nearest_trading":
        data = {
            "header_text": "{} -  {} away".format(config["header"]["text"], data["distance"]),
            "message": data["text"],
        }
        return data
    elif type == "nearest_station":
        data = {
            "header_text": "{} -  {} away".format(config["header"]["text"], data["distance"]),
            "message": data["text"],
        }
        return data
    elif type == "nearest":
        data = {
            "header_text": "{} -  {} away".format(config["header"]["text"], data["distance"]),
            "message": data["text"],
        }
        return data
    elif type == "nearest_challenge":
        data = {
            "header_text": "{} -  {}ly away".format(config["header"]["text"], data["distance"]),
            "message": "Location: {}\nSystem: {}".format(data["location"], data["system"]),
        }
        return data
    elif type == "addinfo_poi":
        data = {
            "header_text": "{} - {}".format(config["header"]["text"], data["hud_category"]),
            "message": "Name: {}\nBody: {}".format(data["name"], data["body"]),
        }
        return data


def wrapText(text, max_length):
    lines = []

    current_lines = text.split("\n")
    for cline in current_lines:
        line = ""
        words = cline.split(" ")
        for word in words:
            if len(line) + len(word) + 1 > int(max_length):
                lines.append(line)
                line = word + " "
            else:
                line += word + " "
        if (len(line) != 0):
            if(line[0] == " "):
                line = line[1:]
            lines.append(line)
    return lines


def overlayDisplayMessage(message, cfg, rtype, config_data):

    if cfg["EnableOverlay"] == 1:
        if(rtype.split("_")[0] == "patrol" and int(cfg["EnableOverlayPatrol"]) == 0):
            return
        if(rtype.split("_")[0] == "addinfo" and int(cfg["EnableOverlayAddinfo"]) == 0):
            return
        if(rtype.split("_")[0] == "nearest" and int(cfg["EnableOverlayNearest"]) == 0):
            return

        config = getConfig(rtype, config_data)
        if(config["enabled"] == False):
            return

        data = getData(message, config, rtype)
        id = ("CANONN-{}-{}").format(rtype, config['posx'])
        display(data["message"], id, config['color'], config['posx'], config['posy'], config['display_time'], config["header"]
                ["color"], data["header_text"], config["max_size"], config["header_spacing"], config["line_spacing"])
    # else:
    #    print("Cannon Overlay requested but Disabled in the settings")


def display(message, id, color, posx, posy, ttl, header_color, header_text, max_size=20, header_spacing=45, line_spacing=20):
    lines = wrapText(message, max_size)
    if(header_text != ""):
        current_posy = posy + header_spacing
        send_message(str(id)+"-header", str(header_text), str(header_color),
                     int(posx), int(posy), ttl=int(ttl), size="large")
    else:
        current_posy = posy

    i = 1
    for line in lines:
        send_message(str(id)+"-"+str(i), str(line), str(color),
                     int(posx), int(current_posy), ttl=int(ttl), size="normal")
        current_posy += line_spacing
        i += 1


# this is being lazy-loaded, but better to have something in the named
# slot than nothing.  makes debugging easier.  `import` will overwrite
# this with the actual module, if we are able to do so.
#
# given the potential for EDMC to load our plugin first, before the
# EDMCOverlay plugin, or some plugin that offers a compatibility layer
# with it, I switched to pure lazy loading — slippycheeze
edmcoverlay = None

# make sure this *always* has a value, so `send_message` doesn't have to.
this._overlay = None

# make sure we only warn the user *once* that EDMCOverlay isn't available; we
# default to being rather spammy until they turn off the option, and we can be
# nicer than that.
this._warned_about_missing_overlay = False


def send_message(id, text, color, x, y, ttl=4, size="normal"):
    # print("{} => {} //x:{}/y:{}".format(id,text,x,y))
    # at this point we have checked config so if we
    # have failed then its because the plugin is missing

    # make sure the byte compiler does not treat this as a local variable.
    global edmcoverlay

    try:
        if edmcoverlay is None:
            import edmcoverlay
        if this._overlay is None:
            this._overlay = edmcoverlay.Overlay()

        if this._overlay is not None:
            this._overlay.send_message(
                id, text, color, x, y, ttl=ttl, size=size)

        # in the event the overlay is not available, we can silently ignore the
        # problem in the hope it improves later.  user won't get an alert, but
        # better than a string of failures every time we try and send.
    except ModuleNotFoundError:
        if not this._warned_about_missing_overlay:
            Debug.logger.exception("import of edmcoverlay failed")
            plug.show_error(f"Need to install the EDMCOverlay plugin")
            this._warned_about_missing_overlay = True
        # suppress this error, we "handled" it ourselves.
        pass
    except Exception as ex:
        Debug.logger.exception(
            "sending a message through the EDMCOverlay plugin failed")

        # the reasonable inference is that `_overlay.send_message()` is
        # throwing, so then the connection is probably broken.
        #
        # If the problem is, eg, that the EDMCOverlay.exe server has crashed or
        # our socket was strangely closed, or something, the new client instance
        # will start another, so this is a solid recovery strategy.
        this._overlay = None

        # ...and suppress the problem, neh?
        pass
