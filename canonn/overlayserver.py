from email import header
from random import Random


import time
import sys
import json
import plug

# 127.0.0.1:5010

this = sys.modules[__name__]
this.overlay_connected = False

try:
    import edmcoverlay
    if edmcoverlay.check_game_running():
        this._overlay = edmcoverlay.Overlay()
        this.connection = this._overlay.connect()
        this.overlay_connected = True
    else:
        plug.show_error("Restart EDMC after the game is loaded")
except:
    this.overlay_connected = False
    pass


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
    if cfg["EnableOverlay"] == 1 and config_data is not None:
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


def send_message(id, text, color, x, y, ttl=4, size="normal"):
    # print("{} => {} //x:{}/y:{}".format(id,text,x,y))
    # at this point we have checked config so if we
    # have failed then its because the plugin is missing

    if this.overlay_connected == False:
        plug.show_error("Retrying Overlay Connection")
        this._overlay = edmcoverlay.Overlay()
        this.connection = this._overlay.connect()
        this.overlay_connected = True

    try:
        if edmcoverlay.check_game_running():
            this._overlay.send_message(
                id, text, color, x, y, ttl=ttl, size=size)
        else:
            plug.show_error("Game not running")
    except:
        plug.show_error("Need to install the EDMCOverlay plugin")
