import threading
import requests
import sys
import json
from emitter import Emitter
from urllib import quote_plus

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
        return payload  

    def run(self):
        if not clientReport.done:           
            print("sending client report")    
            #configure the payload       
            payload=self.setPayload()
            url=self.getUrl()
            self.send(payload,url)        
            clientReport.done=True;
            
def submit(cmdr, is_beta, client):   
    clientReport(cmdr, is_beta, client).start()   