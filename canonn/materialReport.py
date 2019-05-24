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
    
    def __init__(self,cmdr, is_beta, system, station, entry,client,lat,lon,body,state):
        Emitter.__init__(self,cmdr, is_beta, system, None,None,None, entry, body, lat, lon,client)
        self.modelreport="materialreports"
        
    def setPayload(self):
        payload={}
        payload["system"]=self.system
        payload["body"]=  self.body
        payload["latitude"]=  self.lat
        payload["longitude"]=  self.lon
        payload["category"]=self.entry["Category"]
        payload["journalName"]=self.entry["Name"]
        #payload["journalLocalised"]=unicode(self.entry.get(u"Name_Localised"))
        payload["count"]=self.entry["Count"]
        #payload["distanceFromMainStar"] = #TODO find method to calculate distance
        payload["isbeta"]= self.is_beta
        payload["clientVersion"]= self.client
        #payload["state"]=self.state 

        return payload


def matches(d, field, value):
    return field in d and value == d[field]    
    
'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
'''
def submit(cmdr, is_beta, system, station, entry,client,lat,lon,body,state):
    if entry["event"] == "MaterialCollected" :
        MeterialsCollected(cmdr, is_beta, system, station, entry,client,lat,lon,body,state).start()   
        
