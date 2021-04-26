try:
    import tkinter as tk
    from tkinter import Button
    from tkinter import Frame
    from urllib.parse import quote_plus
except:
    import Tkinter as tk
    from Tkinter import Button
    from Tkinter import Frame
    from urllib import quote_plus

import canonn.emitter
import glob
import json
import math
import os
import plug
import requests
import sys
import threading
import time
import myNotebook as nb

from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.systems import Systems
from config import config


# class UpdateRadius(threading.Thread):
    # def __init__(self, widget, system, body):
        # # debug("initialise EDSM_requests Thread")
        # threading.Thread.__init__(self)
        # self.widget = widget
        # self.system = system
        # self.body = body

    # def run(self):
        # # debug("running EDSM_requests")
        # self.widget.getRadius(self.system, self.body)
        # # debug("EDSM_requests Callback Complete")

class BearingDestination():
    state = 0
    system = None
    body = None
    radius = None
    latitude = None
    longitude = None
    target_lat = None
    target_lon = None
    
    def __init__(self, parent, gridrow):
        self.frame = tk.Frame(parent)
        self.frame.grid(row=gridrow)
        self.container = tk.Frame(self.frame)
        self.container.columnconfigure(1, weight=1)
        self.container.grid(row=1)
        self.bearing_status = tk.Label(self.container)
        self.bearing_status.grid(row=0, column=0, columnspan=1, sticky="NSEW")
        #self.bearing_status.config(font=("Arial Black", 22))
        self.hide()
    
    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir
    
    def hide(self):
        self.frame.grid_remove()
    
    def show(self):
        self.frame.grid()
    
    # @classmethod
    # def startJump(cls, target_system):
        # debug("startJump setting state 1 {}".format(target_system))
        # cls.hide()
        # cls.state = 1
        # cls.target_system = target_system

    # @classmethod
    # def FSDJump(cls, system):
        # if cls.state == 1 and not system == cls.target_system:
            # debug("FSDJump setting state 2 {} {}".format(
                # system, cls.target_system))
            # cls.state = 2
        # else:
            # debug("FSDJUMP resetting state back {} {}".format(
                # system, cls.target_system))
            # cls.state = 0

    # @classmethod
    # def SupercruiseExit(cls):
        # cls.hide()
        # state = 0

    # @classmethod
    # def submit(cls, cmdr, is_beta, system, entry, body, client):
        # if entry.get("event") == "SendText":
            # cls.getDestination(cmdr, is_beta, system, body)
        # return
        # # if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            # # cls.startJump(entry.get("StarSystem"))
    
    def journal_entry(self, cmdr, is_beta, system, entry, client):
        
        if entry.get("event") == "SendText":
            message_part = entry.get("Message").lower().split(' ')
            canonn_dest = (len(message_part) > 1)
            canonn_dest = (canonn_dest and message_part[0] == 'canonn')
            canonn_dest = (canonn_dest and message_part[1] == 'dest')

        if entry.get("event") == "SendText" and canonn_dest:
            self.system = system
            try:
                if len(message_part)==2:
                    raise
                elif len(message_part)==3:
                    lat = float(message_part[2].split(",")[0])
                    lon = float(message_part[2].split(",")[1])
                elif len(message_part)==4:
                    lat = float(message_part[2])
                    lon = float(message_part[3])
                self.state = 1
            except:
                lat = None
                lon = None
                self.state = 0
                self.hide()
            self.setTargetLatLon(lat,lon)
            self.calculateBearing(self.body, self.radius, self.latitude, self.longitude)
            
    
    # def getRadius(self, system, body):
        # try:
            # url = "https://www.edsm.net/api-system-v1/bodies?systemName={}".format(
                # quote_plus(system.encode('utf8')))

            # # debug("request {}:  Active Threads {}".format(
            # #    url, threading.activeCount()))

            # r = requests.get(url, timeout=30)
            # # debug("request complete")
            # r.encoding = 'utf-8'
            # if r.status_code == requests.codes.ok:
                # # debug("got EDSM Data")
                # edsm_system = r.json()
                # for edsm_body in edsm_system['bodies']:
                    # if edsm_body['name'] == body:
                        # self.radius = edsm_body['radius']
                        # self.body = edsm_body['name']
            # else:
                # Debug.logger.debug("EDSM Failed")
                # Debug.logger.error("EDSM Failed")
                
            # self.state = 1
        # except:
            # Debug.logger.debug("Error getting EDSM data")
            # self.radius = None
            # self.state = 0
    
    def setTargetLatLon(self, lat, lon):
        if (lat is not None) or (lon is not None):
            if (lat < -90) or (lat > 90):
                lat = None
                lon = None
            if (lon <= -180) or (lon > 180):
                lat = None
                lon = None
        else:
            lat = None
            lon = None
        self.target_lat = lat
        self.target_lon = lon
    
    def updatePosition(self, body, radius, lat, lon):
        self.latitude = lat
        self.longitude = lon
        self.radius = radius
        self.body = body
        self.calculateBearing(body, radius, lat, lon)
    
    def calculateBearing(self, body, radius, lat, lon):
        if self.state == 1:
            if (lat is not None) and (lon is not None) and (radius is not None) and (body is not None) :
                radius = radius/1000
                dist = calc_distance(lat, lon, self.target_lat, self.target_lon, radius)
                brng = calc_bearing(lat, lon, self.target_lat, self.target_lon, radius)
                self.updateBearing(round(brng,2), round(dist,3))
            else:
                self.state = 0
                self.updateBearing("-", "-")
                #UpdateRadius(self, self.system, my_body).start()
        
    def updateBearing(self, bearing = None, distance = None):
        
        self.bearing_status["text"] = "   DEST ({},{}) : BEARING {} / DIST {} km".format(self.target_lat, self.target_lon, bearing, distance)
        if self.state == 1:
            self.show()
        else:
            self.hide()
        debug("updateBearing = {} / {}".format(bearing, distance))
    
    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.frame = nb.Frame(parent)
        self.frame.columnconfigure(1, weight=1)
        self.frame.grid(row=gridrow, column=0, sticky="NSEW")
        nb.Label(self.frame, text=f"These followed in-game text command are used to get bearing and distance for a destination (latitude,longitude) on a planet :\ncanonn dest <latitude> <longitude>\n\t<latitude> = float (-90 -> 90)\n\t<longitude> = float (-180 -> 180)\nUse the next command to remove the destination:\ncanonn dest", justify=tk.LEFT, anchor="w").grid(row=0, column=0, sticky="NW")

        return self.frame

def calc_distance(phi_a, lambda_a, phi_b, lambda_b, radius):

    debug("calc_distance = {} {} {} {} {}".format(phi_a, lambda_a, phi_b, lambda_b, radius))

    if radius is None:
        return 0.0

    phi_a = phi_a * math.pi / 180.
    lambda_a = lambda_a * math.pi / 180.
    phi_b = phi_b * math.pi / 180.
    lambda_b = lambda_b * math.pi / 180.

    if(phi_a != phi_b or lambda_b != lambda_a):
        d_lambda = lambda_b - lambda_a
        S_ab = math.acos(math.sin(phi_a)*math.sin(phi_b)+math.cos(phi_a)*math.cos(phi_b)*math.cos(d_lambda))
        return S_ab * radius
    else:
        return 0.0
        
def calc_bearing(phi_a, lambda_a, phi_b, lambda_b, radius):
       
    debug("calc_bearing = {} {} {} {} {}".format(phi_a, lambda_a, phi_b, lambda_b, radius))

    if radius is None:
        return 0.0

    phi_a = phi_a * math.pi / 180.
    lambda_a = lambda_a * math.pi / 180.
    phi_b = phi_b * math.pi / 180.
    lambda_b = lambda_b * math.pi / 180.

    if(phi_a != phi_b or lambda_b != lambda_a):
        d_lambda = lambda_b - lambda_a
        y = math.sin(d_lambda)*math.cos(phi_b)
        x = math.cos(phi_a)*math.sin(phi_b)-math.sin(phi_a)*math.cos(phi_b)*math.cos(d_lambda)
        brng = math.atan2(y,x)*180./math.pi
        if brng<0:
            brng += 360.
        return brng
    else:
        return 0.0