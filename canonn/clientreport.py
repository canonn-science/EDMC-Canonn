import threading
import requests
import sys
import json
from emitter import Emitter
from urllib import quote_plus
from debug import Debug
from debug import debug,error
from release import Release

class clientReport(Emitter):
    
    done=False    
        
    def __init__(self,cmdr, is_beta,client):
        
        self.modelreport="clientreports" 
        Emitter.__init__(self,cmdr, is_beta, None, None,None,None, None, None,None,None,client)
        
    def setPayload(self):
        payload={}
        payload["cmdrName"]=self.cmdr  
        payload["isBeta"]=self.is_beta
        payload["clientVersion"]=self.client
        if Release.get_auto() == 1:
            payload["AutoUpdateDisabled"]=False
        else:
            payload["AutoUpdateDisabled"]=True
            
        return payload  

    def run(self):
        if not clientReport.done:           
            debug("sending client report")    
            #configure the payload       
            payload=self.setPayload()
            url=self.getUrl()
            self.send(payload,url)        
            clientReport.done=True

def submit(cmdr, is_beta, client,entry):  
    
    if entry.get("event") in ("Location","StartUp"):
        clientReport(cmdr, is_beta, client).start()   