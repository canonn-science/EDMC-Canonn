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
import re
import threading
import time
import myNotebook as nb
import queue as Q

from threading import Thread
from ttkHyperlinkLabel import HyperlinkLabel

from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.systems import Systems
from config import config

class extoolTypes():
    system = None
    system64 = None
    syscoords = None
    body = None
    body_drop = None
    radius = None
    landingpad = None
    nearloc = None
    neardest = None
    
    def __init__(self):
        self.session = requests.Session()
        self.queue = Q.Queue()
        self.thread = Thread(target = self.worker, name = 'ExTool worker')
        self.thread.daemon = True
        self.thread.start()
    
    @classmethod
    def plugin_start(self, plugin_dir):
        self.plugin_dir = plugin_dir
        
    def plugin_stop(self):
        self.queue.put(None)
        self.thread.join()
        self.thread = None
        #print "Farewell cruel world!"
    
    def updateStatus(self, body, radius, nearloc):
        self.body = body
        self.radius = radius
        self.nearloc = nearloc
    
    # Worker thread
    def worker(self):
        url = "https://elite.laulhere.com/ExTool/send_data"
        while True:
            item = self.queue.get()
            if not item:
                return	# Closing
            else:
                (mode, data, callback) = item
            
            if(mode=='senddata'):

                retrying = 0
                while retrying < 3:
                    try:
                        reply = None
                        #print("SEND EXTOOL", mode, data)
                        r = self.session.post(url, json=data, timeout=20)
                        #print("TEXT EXTOOL", r.text)
                        r.raise_for_status()
                        reply = r.json()
                        (code, msg) = reply['Status'], reply['StatusMsg']
                        #print("REPLY EXTOOL", reply)
                        
                        if (code // 100 != 1):	# 1xx = OK, 2xx = WARNING, 3xx 4xx 5xx = fatal error
                            if (code // 100 == 2):
                                Debug.logger.debug(('Warning: ExTool {MSG}').format(MSG=msg))
                            else:
                                Debug.logger.error(('Error: ExTool {MSG}').format(MSG=msg))
                        #else:
                        #    Debug.logger.debug(('ExTool {MSG}').format(MSG=msg))
                        
                        if callback:
                            callback(reply)
                        break
                   
                    except:
                        print("SEND EXTOOL", mode, data)
                        print("TEXT EXTOOL", r.text)
                        print("REPLY EXTOOL", reply)
                        retrying += 1
                else:
                    Debug.logger.error(("Error: Can't connect to ExTool Server"))

          
            #elif(mode=='playsound'):
            #    try:
            #        PlaySound(data, SND_FILENAME)
            #    except:
            #        plug.show_error(_("Error: Can't play sound for ExTool"))
    
    def call(self, cmdr, sendmode, args, callback=None):
        #args = json.loads(args)
        args['cmdr'] = cmdr
        args['mode'] = sendmode
        args['version'] = self.version
        args['apikey'] = ""
        self.queue.put(('senddata', args, callback))
        
    def send_data(self, cmdr, event, timestamp, rawentry):
        payload = {
            'system' : self.system,
            'system64' : self.system64,
            'coords' : self.syscoords,
            'body' : self.body,
            'bodydrop' : self.body_drop,
            'radius' : self.radius,
            'landingpad' : self.landingpad,
            'nearloc' : self.nearloc,
            'rawentry' : rawentry,
            'timestamp' : time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
        }
        self.call(cmdr, event, payload)
        
    
    def journal_entry(self, cmdr, is_beta, system, station, entry, state, client):
        
        self.version = client
        if is_beta or not state.get("Odyssey"):
            return
        
        timestamp = time.mktime(time.strptime(entry.get('timestamp'), '%Y-%m-%dT%H:%M:%SZ'))
        
        if entry.get("event") in ("Location", "StartUp", "FSDJump", "CarrierJump"):
            self.system64 = entry.get("SystemAddress")
            self.system = entry.get("StarSystem")
            self.syscoords = entry.get("StarPos")
            self.landingpad = None
            self.body_drop = None
            self.send_data(cmdr, entry.get("event"), timestamp, entry)
        
        if entry.get("event") in ("Location", "StartUp"):
            if "Body" in entry:
                self.body_drop = entry['Body']
        
        if entry.get("event") in ("DockingGranted"):
            self.landingpad = entry.get("LandingPad")
        if entry.get("event") in ("SupercruiseEntry"):
            self.landingpad = None
            self.body_drop = None
        if entry.get("event") in ("SupercruiseExit"):
            if "Body" in entry:
                self.body_drop = entry['Body']
        if entry.get("event") in ("StartJump"):
            if entry.get("JumpType") in ("Hyperspace"):
                self.body_drop = None
        
        if entry.get("event") in ("SellOrganicData", "MissionAccepted"):
            # no need system or body
            self.send_data(cmdr, entry.get("event"), timestamp, entry)
            
        if entry.get("event") in ("Touchdown", "Liftoff"):
            # everything is in the entry (system and body)
            self.send_data(cmdr, entry.get("event"), timestamp, entry)
        
        if entry.get("event") in ("Disembark", "Embark"):
            if entry.get("Taxi") == True and entry.get("OnPlanet") == True:
                self.send_data(cmdr, entry.get("event"), timestamp, entry)
            
        if entry.get("event") in ("Docked"):
            if entry.get("StationType") != "FleetCarrier":
                self.send_data(cmdr, entry.get("event"), timestamp, entry)
            
        if entry.get("event") in ("CodexEntry", "DatalinkScan", "DatalinkVoucher", "DataScanned", "CollectCargo", "MaterialCollected"):
            # space or planet
            # missing body : CodexEntry
            # missing body, lat & lon : Docked
            # missing system, body, lat & lon : DatalinkScan, DatalinkVoucher, DataScanned, MaterialCollected, CollectCargo
            if entry.get("EntryID") is not None:
                if entry.get("EntryID")==2330403 and entry.get("Name")=="$Codex_Ent_Cactoid_03_A_Name;":
                    entry["Name"]="$Codex_Ent_Cactoid_04_A_Name;"
            self.send_data(cmdr, entry.get("event"), timestamp, entry)
            
        if entry.get("event") in ("FSSSignalDiscovered"):
            FleetCarrier = False
            if entry.get("IsStation"):
                prog = re.compile("^.* [A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]$")
                FleetCarrier = prog.match(entry.get("SignalName"))
                prog = re.compile("^.*[a-z].*$")
                FleetCarrier = FleetCarrier and not prog.match(entry.get("SignalName"))
                prog = re.compile("^[A-Z0-9][A-Z0-9][A-Z0-9]-[A-Z0-9][A-Z0-9][A-Z0-9]$")
                FleetCarrier = FleetCarrier or prog.match(entry.get("SignalName"))
            if not FleetCarrier:
                # space only
                self.send_data(cmdr, entry.get("event"), timestamp, entry)
            
        if entry.get("event") in ("ApproachSettlement", "SAASignalsFound", "SAAScanComplete", "ScanOrganic", "BackpackChange"):
            # planet only
            # missing system, body, lat & lon : BackpackChange
            self.send_data(cmdr, entry.get("event"), timestamp, entry)
        
class BearingDestination():
    state = 0
    system = None
    body = None
    radius = None
    latitude = None
    longitude = None
    target = {}

    def __init__(self, parent, gridrow):
        self.frame = Frame(parent)
        self.frame.grid(row=gridrow)
        self.container = Frame(self.frame)
        self.container.columnconfigure(1, weight=1)
        self.container.grid(row=1)
        self.bearing_cancel = tk.Label(self.container)
        self.bearing_cancel.grid(row=0, column=0, sticky="NSEW")
        self.bearing_cancel['text'] = "X"
        self.bearing_cancel['fg'] = "blue"
        self.bearing_cancel['cursor'] = "hand2"
        self.bearing_cancel.bind("<ButtonPress>", self.eventDeactivate)
        self.bearing_status = tk.Label(self.container)
        self.bearing_status.grid(row=0, column=1, sticky="NSEW")
        #self.bearing_status.config(font=("Arial Black", 22))
        self.hide()

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

    def hide(self):
        self.frame.grid_remove()

    def show(self):
        self.frame.grid()

    def journal_entry(self, cmdr, is_beta, system, entry, client):

        if entry.get("event") == "LeaveBody":
            self.eventDeactivate(None)

        if entry.get("event") == "SendText":
            message_part = entry.get("Message").lower().split(' ')
            canonn_dest = (len(message_part) > 1)
            canonn_dest = (canonn_dest and message_part[0] == 'canonn')
            canonn_dest = (canonn_dest and message_part[1] == 'dest')

        if entry.get("event") == "SendText" and canonn_dest:
            self.system = system
            try:
                if len(message_part) == 2:
                    raise
                elif len(message_part) == 3:
                    lat = float(message_part[2].split(",")[0])
                    lon = float(message_part[2].split(",")[1])
                elif len(message_part) == 4:
                    lat = float(message_part[2])
                    lon = float(message_part[3])
                self.state = 1
            except:
                lat = None
                lon = None
                self.state = 0
                self.hide()
            self.setTargetLatLon("Custom", lat, lon)
            self.calculateBearing(self.body, self.radius, self.latitude, self.longitude)

    def eventDeactivate(self, event):
        self.state = 0
        self.target = {}
        self.hide()

    def ActivateTarget(self, lat, lon):
        self.setTargetLatLon("Custom", lat, lon)
        self.state = 1
        self.calculateBearing(self.body, self.radius, self.latitude, self.longitude)
    
    def AddTarget(self, name, lat, lon):
        self.setTargetLatLon(name, lat, lon)
        self.state = 1
        self.calculateBearing(self.body, self.radius, self.latitude, self.longitude)
    
    def setTargetLatLon(self, name, lat, lon):
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
        if (name is not None) and (lat is not None) and (lon is not None):
            self.target[name] = {"latitude" : lat, "longitude" : lon}
        else:
            self.target = {}

    def updatePosition(self, body, radius, lat, lon, heading):
        self.latitude = lat
        self.longitude = lon
        self.radius = radius
        self.body = body
        self.calculateBearing(body, radius, lat, lon, heading)

    def calculateBearing(self, body, radius, lat, lon, heading=None):
        if self.state == 1:
            if (lat is not None) and (lon is not None) and (radius is not None) and (body is not None) and (len(self.target)>0):
                radius = radius/1000
                closest_target = None
                closest_distance = None
                for target_name in self.target:
                    dist = calc_distance(lat, lon, self.target[target_name]["latitude"], self.target[target_name]["longitude"], radius)
                    if closest_target is None:
                        closest_target = target_name
                        closest_distance = dist
                    else:
                        if dist < closest_distance:
                            closest_target = target_name
                            closest_distance = dist
                brng = calc_bearing(lat, lon, self.target[closest_target]["latitude"],self.target[closest_target]["longitude"], radius)
                self.updateBearing(closest_target, round(brng, 2), round(dist, 3), heading)
            else:
                self.state = 0
                self.target = {}
                #self.updateBearing("-", "-", "-")
                self.updateBearing()
                #UpdateRadius(self, self.system, my_body).start()

    def updateBearing(self, target_name=None, bearing=None, distance=None, heading=None):
        #debug({"heading": heading, "bearing": bearing})
        
        if target_name is not None:
            fg = "grey"
            if (bearing and heading):
                if int(heading) == round(bearing, 0):
                    fg = "green"
                bupper = (round(bearing, 0)+1) % 360
                blower = (round(bearing, 0)-1) % 360
                if int(heading) in (bupper, blower):
                    fg = "orange"

            self.bearing_status["foreground"] = fg
            if target_name == "Custom":
                self.bearing_status["text"] = "   DEST ({},{}) : BEARING {} / DIST {} km".format(self.target[target_name]["latitude"], self.target[target_name]["longitude"], bearing, distance)
            else:
                self.bearing_status["text"] = "   {} : BEARING {} / DIST {} km".format(self.target[target_name]["name"], bearing, distance)
        
        if self.state == 1:
            self.show()
        else:
            self.hide()
        #debug("updateBearing = {} / {}".format(bearing, distance))

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.frame = nb.Frame(parent)
        self.frame.columnconfigure(1, weight=1)
        self.frame.grid(row=gridrow, column=0, sticky="NSEW")
        nb.Label(self.frame, text=f"These followed in-game text command are used to get bearing and distance for a destination (latitude,longitude) on a planet :\ncanonn dest <latitude> <longitude>\n\t<latitude> = float (-90 -> 90)\n\t<longitude> = float (-180 -> 180)\nUse the next command to remove the destination:\ncanonn dest", justify=tk.LEFT, anchor="w").grid(row=0, column=0, sticky="NW")

        return self.frame


def calc_distance(phi_a, lambda_a, phi_b, lambda_b, radius):

    # debug("calc_distance = {} {} {} {} {}".format(
    #    phi_a, lambda_a, phi_b, lambda_b, radius))

    if radius is None:
        return 0.0

    phi_a = phi_a * math.pi / 180.
    lambda_a = lambda_a * math.pi / 180.
    phi_b = phi_b * math.pi / 180.
    lambda_b = lambda_b * math.pi / 180.

    if(phi_a != phi_b or lambda_b != lambda_a):
        d_lambda = lambda_b - lambda_a
        S_ab = math.acos(math.sin(phi_a)*math.sin(phi_b) +
                         math.cos(phi_a)*math.cos(phi_b)*math.cos(d_lambda))
        return S_ab * radius
    else:
        return 0.0


def calc_bearing(phi_a, lambda_a, phi_b, lambda_b, radius):

    # debug("calc_bearing = {} {} {} {} {}".format(
    #    phi_a, lambda_a, phi_b, lambda_b, radius))

    if radius is None:
        return 0.0

    phi_a = phi_a * math.pi / 180.
    lambda_a = lambda_a * math.pi / 180.
    phi_b = phi_b * math.pi / 180.
    lambda_b = lambda_b * math.pi / 180.

    if(phi_a != phi_b or lambda_b != lambda_a):
        d_lambda = lambda_b - lambda_a
        y = math.sin(d_lambda)*math.cos(phi_b)
        x = math.cos(phi_a)*math.sin(phi_b)-math.sin(phi_a) * \
            math.cos(phi_b)*math.cos(d_lambda)
        brng = math.atan2(y, x)*180./math.pi
        if brng < 0:
            brng += 360.
        return brng
    else:
        return 0.0

