import threading
import requests
import sys
import json
from debug import Debug
from debug import debug,error



class Emitter(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    urls={ 
        "live": "https://api.canonn.tech",
        "staging": "https://api.canonn.tech:2053",
        "development":  "https://api.canonn.tech:2083"
    }               
        
    route=""    
        
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        threading.Thread.__init__(self)
        self.cmdr=cmdr
        self.system=system
        self.x=x
        self.y=y
        self.z=z
        self.body = body
        self.lat = lat
        self.lon = lon
        self.is_beta = is_beta
        if entry:
            self.entry = entry.copy()
        self.client = client
        Emitter.setRoute(is_beta,client)
        self.modelreport="clientreports"

    @classmethod
    def setRoute(cls,is_beta,client):
        if Emitter.route:
            return Emitter.route
        else:
            ## this url will need to bechanged to the live server whenready
            r=requests.get("{}/clientroutes?clientversion={}".format(Emitter.urls.get("live"),client))
            j = r.json()
            if not r.status_code == requests.codes.ok or not j:
                Emitter.route=Emitter.urls.get("development")
            else:   
                Emitter.route=j[0].get("route")
                
        return Emitter.route

        
    def getUrl(self):
        if self.is_beta:
            url=Emitter.urls.get("staging")
        else:
            url=Emitter.route
        return url
        
    def setPayload(self):
        payload={}
        payload["cmdrName"]=self.cmdr  
        payload["systemName"]=self.system
        payload["isBeta"]=self.is_beta
        payload["clientVersion"]=self.client
        return payload   
    
    def run(self):
    
        #configure the payload       
        payload=self.setPayload()
        url=self.getUrl()
        self.send(payload,url)
    
    def send(self,payload,url):
        fullurl="{}/{}".format(url,self.modelreport)
        r=requests.post(fullurl,data=json.dumps(payload, ensure_ascii=False).encode('utf8'),headers={"content-type":"application/json"})  
        
        if not r.status_code == requests.codes.ok:
            error("{}/{}".format(url,self.modelreport))
            error(r.status_code)
            error(r.json())
            error(json.dumps(payload))
        else:
            debug("{}?id={}".format(fullurl,r.json().get("id")))


            


            