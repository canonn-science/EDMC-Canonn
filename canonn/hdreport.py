import threading    
import requests
import sys
import json
from emitter import Emitter
from debug import Debug
from debug import debug,error

'''

We want to record the system where the user was last hyperdicted
Ths is in the statistics event which appears evert time the user
returns from the main menu. We want to record   


'''

class HDReport(Emitter):

    hdsystem=""

    def __init__(self,cmdr, is_beta, system,entry,client):
        Emitter.__init__(self,cmdr, is_beta, system, None,None,None, entry, None,None,None,client)
        self.system = system
        self.cmdr = cmdr
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client=client
        self.modelreport="hdreports"

    def setPayload(self):
        payload={}
        payload["fromSystemName"]=self.entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
        payload["cmdrName"]=self.cmdr  
        payload["isbeta"]= self.is_beta
        payload["clientVersion"]= self.client
        payload["reportStatus"]="accepted"
        payload["reportComment"]="Hyperdiction from TG_ENCOUNTERS"
        payload["hdRawJson"]=self.entry.get("TG_ENCOUNTERS")

            
        return payload
        
    #going to overload run so that we can check for the last hdsystem
    def run(self):
        url=self.getUrl()
        
        if HDReport.hdsystem == "":
        
            r = requests.get("{}/{}?cmdrName={}&_sort=created_at:DESC&_limit=1".format(url,self.modelreport,self.cmdr))
            j = r.json()
            if j:
        
                HDReport.hdsystem=j[0].get("fromSystemName")
        
        if self.entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM") == HDReport.hdsystem:
            debug("Hyperdiction already recorded here - server")
        else:
        
            payload=self.setPayload()
            self.send(payload,url)

def submit(cmdr, is_beta, system, station, entry,client):
    
    # The last system isnt always set so we can ignore 
    
    if entry["event"] == "Statistics" and entry.get("TG_ENCOUNTERS"):
        # there is no guarentee TG_ENCOUNTER_TOTAL_LAST_SYSTEM will have a value
        if entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM"):
        
            lastsystem=entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")   
            if HDReport.hdsystem == lastsystem:
                debug("Hyperdiction already recorded here - session ")
            else:
                HDReport(cmdr, is_beta, lastsystem,  entry,client).start()   
