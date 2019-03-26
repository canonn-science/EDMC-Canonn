import threading
import requests
import sys
import json
import time
from emitter import Emitter
from debug import Debug
from debug import debug,error


'''
Added the above events to: https://api.canonn.tech:2053/excludeevents
-DM
'''

class CanonnJournal(Emitter):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    
    exclusions={}
    
    def __init__(self,cmdr, is_beta, system, station, entry,client):
        Emitter.__init__(self,cmdr, is_beta, system, None,None,None, entry, None,None,None,client)
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client = client
        self.modelreport="reportevents"

    def setPayload(self):        
        payload={}
        payload["systemName"]=self.system
        payload["cmdrName"]=self.cmdr  
        payload["rawJson"]=self.entry
        payload["eventName"]=self.entry["event"]
        payload["clientVersion"]= self.client
        payload["isBeta"]= self.is_beta
        return payload
        
    def run(self):
        url=self.getUrl()
        if not CanonnJournal.exclusions:
            debug("getting journal excludes")
            tempexcludes={}
            r=requests.get("{}/excludeevents?_limit=1000".format(url))
            
            if r.status_code == requests.codes.ok:
                # populate a local variable so other threads dont see incomplete results
                for exc in r.json():
                    tempexcludes[exc["eventName"]]=True
                CanonnJournal.exclusions=tempexcludes
                debug("Jouurnal excludes got")
            else:
                error("{}/excludeevents".format(url))

        payload={}
        payload["systemName"]=self.system
        payload["cmdrName"]=self.cmdr  
        payload["rawJson"]=self.entry
        payload["eventName"]=self.entry["event"]
        payload["clientVersion"]= self.client
        payload["isBeta"]= self.is_beta
        
        
        
        included_event = not CanonnJournal.exclusions.get(self.entry.get("event"))
        
        if included_event:
                    
            payload=self.setPayload()
            self.send(payload,url)           

'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
'''
def submit(cmdr, is_beta, system, station, entry,client):
    CanonnJournal(cmdr, is_beta, system, station, entry,client).start()   