import threading
import requests
import sys
import json
from emitter import Emitter
from urllib import quote_plus
from debug import Debug
from debug import debug,error


class fssEmitter(Emitter):
    types={}
    reporttypes={}
    excludefss={}
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        Emitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="xxreports"
        self.modeltype="xxtypes"
        
    def getFssPayload(self):
        payload=self.setPayload()
        payload["reportStatus"]="pending"
        payload["systemAddress"]=self.entry.get("SystemAddress")
        payload["signalName"]=self.entry.get("SignalName")
        payload["signalNameLocalised"]=self.entry.get("SignalName_Localised")
        
        payload["spawningState"]=self.entry.get("SpawningState")
        payload["spawningStateLocalised"]=self.entry.get("SpawningState_Localised")
        payload["spawningFaction"]=self.entry.get("SpawningFaction")
        
        payload["rawJson"]=self.entry
            
        return payload           
        
    def getLcPayload(self):
        payload=self.setPayload()
        payload["reportStatus"]="pending"
        payload["systemAddress"]=self.entry.get("SystemAddress")
        payload["signalName"]=self.entry.get("SignalName")
        payload["signalNameLocalised"]=self.entry.get("SignalName_Localised")
        
        
        debug(payload)
        
        payload["rawJson"]=self.entry
            
        return payload                   
        
    def getAXPayload(self):
        payload=self.setPayload()
        payload["reportStatus"]="pending"
        payload["systemAddress"]=self.entry.get("SystemAddress")
        #can remove these from strapi model because they will always be the same
        #payload["signalName"]=self.entry.get("signalName")
        #payload["signalNameLocalised"]=self.entry.get("signalNameLocalised")
        payload["rawJson"]=self.entry
                
    def getExcluded(self):
        if not fssEmitter.excludefss:
            r=requests.get("{}/excludefssess?_limit=1000".format(self.getUrl()))  
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    fssEmitter.excludefss["${}_name;".format(exc["signalName"])]=True
                    
    def run(self):
        
        self.getExcluded()
        
        #is this a code entry and do we want to record it?
        if self.entry["event"] == "FSSSignalDiscovered" and not fssEmitter.excludefss.get(self.entry.get("SignalName")) and not self.entry.get("SignalName") == "$USS;" and not self.entry.get("IsStation"):
            
            url=self.getUrl()
            
            if self.entry.get("SignalName") == "$Warzone_TG;":
                payload=self.getAXPayload()
                self.modelreport-"axczfssreports"
            elif self.entry.get("SignalName") == "$Fixed_Event_Life_Cloud;":
                debug("Life Cloud")
                payload=self.getLcPayload()
                self.modelreport="lcfssreports"
            else: 
                payload=self.getFssPayload()
                self.modelreport="reportfsses"
            
            self.send(payload,url)

def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
    fssEmitter(cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client).start()   