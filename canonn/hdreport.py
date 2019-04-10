import threading    
import requests
import sys
import json
from emitter import Emitter
from debug import Debug
from debug import debug,error
from config import config
import Tkinter as tk
from Tkinter import Button
from Tkinter import Frame
from systems import Systems
from urllib import quote_plus
import glob
import os
import time

'''

We want to record the system where the user was last hyperdicted
Ths is in the statistics event which appears evert time the user
returns from the main menu. We want to record   


'''


class gSubmitHD(threading.Thread):
    def __init__(self,cmdr,x,y,z,entry):
        threading.Thread.__init__(self)
        self.cmdr=quote_plus(cmdr.encode('utf8'))
        self.system=quote_plus(entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM").encode('utf8'))
        self.x=x
        self.y=y
        self.z=z
        ts=entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP")
        year=int(ts[0:4])-1286
        self.eddatetime="{}-{}:00".format(year,ts[4:])
        debug(self.eddatetime)
        
                            
        self.entry=entry
        
        

    def run(self):
        
        
        debug("sending gSubmitCodex")
        url="https://us-central1-canonn-api-236217.cloudfunctions.net/submitHD?cmdrName={}".format(self.cmdr)
        url=url+"&systemName={}".format(self.system)
        url=url+"&x={}".format(self.x)
        url=url+"&y={}".format(self.y)
        url=url+"&z={}".format(self.z)
        url=url+"&z={}".format(self.eddatetime)
        
        
                    
        r=requests.get(url)
    
        if not r.status_code == requests.codes.ok:
            error("gSubmitHD {} ".format(url))
            error(r.status_code)
            error(r.json())

class HDReport(Emitter):

    hdsystems={}

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
        
    
    def excludesystems(self):    
        url=self.getUrl()
        if not HDReport.hdsystems:
            debug("getting old hdsystems")
            r = requests.get("{}/{}?cmdrName={}&_sort=created_at:DESC&_limit=2000".format(url,self.modelreport,self.cmdr))           
            for hd in r.json():
                debug("excluding: {}".format(hd.get("fromSystemName")))
                HDReport.hdsystems[hd.get("fromSystemName")]=hd.get("fromSystemName")
    
    #going to overload run so that we can check for the last hdsystem
    def run(self):
        url=self.getUrl()
        
        self.excludesystems()
        # if not HDReport.hdsystems:
            # debug("getting old hdsystems")
            # r = requests.get("{}/{}?cmdrName={}&_sort=created_at:DESC&_limit=2000".format(url,self.modelreport,self.cmdr))           
            # for hd in r.json():
                # debug("excluding: {}".format(hd.get("fromSystemName")))
                # HDReport.hdsystems[hd.get("fromSystemName")]=hd.get("fromSystemName")
        
        lasthd=self.entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
        if lasthd:
            if HDReport.hdsystems.get(lasthd):    
                debug("Hyperdiction already recorded here - server")
            else:        
                HDReport.hdsystems[lasthd]=lasthd
                payload=self.setPayload()
                self.send(payload,url)
            
class HDScanner(threading.Thread):

    def __init__(self,process):
        threading.Thread.__init__(self)
        self.process=process
        
    def run(self):
        self.process()
            
class HDInspector(Frame):
    
    def __init__(self, parent,cmdr,is_beta,client,gridrow):
        "Initialise the ``Patrol``."
        Frame.__init__(
            self,
            parent
        )
        self.client=client
        self.commander=cmdr
        self.is_beta=is_beta
        self.grid(row = gridrow, column = 0)
        self.button=Button(self, text="Click here to scan all your journals for Hyperdictions")
        self.button.bind('<Button-1>',self.run)
        self.button.grid(row=0,column = 0)
        Emitter.setRoute(is_beta,client)
        
    def getUrl(self):
        if self.is_beta:
            url=Emitter.urls.get("staging")
        else:
            url=Emitter.route
        return url
        
    def excludesystems(self):    
        url=self.getUrl()
        if not HDReport.hdsystems:
            debug("getting old hdsystems")
            r = requests.get("{}/{}?cmdrName={}&_sort=created_at:DESC&_limit=2000".format(url,"hdreports",self.commander))           
            for hd in r.json():
                debug("excluding: {}".format(hd.get("fromSystemName")))
                HDReport.hdsystems[hd.get("fromSystemName")]=hd.get("fromSystemName")
    
    def run(self,event):
        self.button.grid_remove()
        HDScanner(self.scan_journals).start()
    
    def set_beta(self,entry):
        if entry.get("event") == "Fileheader":
            if "beta" in entry.get("gameversion").lower():
                self.is_beta=True
            else:
                self.is_beta=False
    
    def set_commander(self,entry):
        if entry.get("event") == "Commander":
            self.commander=entry.get("Name")
          
    def detect_hyperdiction(self,entry):
        if entry.get("event") == "Statistics":
            debug("detected")
            submit(self.commander,self.is_beta,None,None,entry,self.client)
            time.sleep(0.1)
        # else:
            # debug(entry.get("event"))
            
        
    def scan_file(self,filename):       
        with open(filename) as f:
            for line in f:
                entry=json.loads(line)
                self.set_beta(entry)
                self.set_commander(entry)               
                self.detect_hyperdiction(entry)
                
        
    def scan_journals(self):
        self.excludesystems()
        config.default_journal_dir
        for filename in glob.glob(os.path.join(config.default_journal_dir, 'journal*.log')):
            self.scan_file(filename)
        
def submit(cmdr, is_beta, system, station, entry,client):
    
    # The last system isnt always set so we can ignore 
    
    if entry["event"] == "Statistics" and entry.get("TG_ENCOUNTERS"):
        # there is no guarentee TG_ENCOUNTER_TOTAL_LAST_SYSTEM will have a value
        if entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM"):
        
            lastsystem=entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")   
            if lastsystem:
                if HDReport.hdsystems.get(lastsystem) == lastsystem:
                    debug("Hyperdiction already recorded here - session ")
                else:
                    HDReport(cmdr, is_beta, lastsystem,  entry,client).start()   
                    x,y,z=Systems.edsmGetSystem(lastsystem)
                    gSubmitHD(cmdr,x,y,z,entry).start()
