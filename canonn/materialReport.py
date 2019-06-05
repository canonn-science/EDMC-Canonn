# -*- coding: utf-8 -*-
import threading
import requests
from urllib import quote_plus
import sys
import json
from emitter import Emitter
from debug import Debug
from debug import debug,error


              

class MeterialsCollected(Emitter):
    
    def __init__(cmdr, is_beta, system, station, entry,client,lat,lon,body,state,x,y,z,DistFromStarLS):
        self.state=state
        self.DistFromStarLS=DistFromStarLS
        debug("MAterial rep FacState "+str(self.state))
        Emitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body, lat, lon,client)       

        self.modelreport="materialreports"
        
    def setPayload(self):
        payload={}
        payload["system"]=self.system
        payload["body"]=  self.body
        payload["latitude"]=  self.lat
        payload["longitude"]=  self.lon
        payload["category"]=self.entry["Category"]
        payload["journalName"]=self.entry["Name"]        
        payload["count"]=self.entry["Count"]
        payload["distanceFromMainStar"] = self.DistFromStarLS
        payload["coordX"] = self.x
        payload["coordY"] = self.y
        payload["coordZ"] = self.z
        payload["isbeta"]= self.is_beta
        payload["clientVersion"]= self.client
        payload["factionState"]=self.state

        return payload


def matches(d, field, value):
    return field in d and value == d[field]    
    

def submit(cmdr, is_beta, system,SysFactionState,DistFromStarLS, station, entry, state,x,y,z,body,lat,lon,client):
    if entry["event"] == "MaterialCollected" :
        MeterialsCollected(cmdr, is_beta, system, station, entry,client,lat,lon,body,state,x,y,z,DistFromStarLS).start()   
        