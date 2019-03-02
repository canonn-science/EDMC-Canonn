import threading
import requests
import sys
import json
from emitter import Emitter
from urllib import quote_plus

class clientReport(Emitter):
       
    done=False    
        
    def __init__(self,cmdr, is_beta,client):
        
        Emitter.__init__(self,cmdr, is_beta, None, None,None,None, None, None,None,None,client)
        if not clientReport.done:            
            self.modelreport="clientreports"
            clientReport.done=True;
        
    def setPayload(self):
        payload={}
        payload["cmdrName"]=self.cmdr  
        payload["isBeta"]=self.is_beta
        payload["clientVersion"]=self.client
        return payload  
        
            
def submit(cmdr, is_beta, client):   
    clientReport(cmdr, is_beta, client).start()   