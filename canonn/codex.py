import threading
import requests
import sys
import json
from emitter import Emitter
from urllib import quote_plus
from debug import Debug
from debug import debug,error
from Tkinter import Frame
import Tkinter as tk
from config import config
import os
import myNotebook as nb

class poiTypes(threading.Thread):
    def __init__(self,system,callback):
        threading.Thread.__init__(self)
        self.system=quote_plus(system.encode('utf8'))
        self.callback=callback

    def run(self):
        debug("running poitypes")
        self.callback(self.system)

            
    def recycle(self):
        print "Recycling Labels"
        
        for label in self.lt:
            label.grid_remove()
        for label in self.lp:
            label.grid_remove()            
            
        #Frame.destroy(self)
        
        
class CodexTypes(Frame):

    tooltips={
            "Geology": "Geology: Vents and fumeroles",
            "Cloud": "Lagrange Clouds",
            "Anomaly": "Anomalous stellar phenomena",
            "Thargoid": "Thargoid sites or barnacles",
            "Biology": "Biological surface signals",
            "Guardian": "Guardian sites",
            "None": "Unclassified codex entry",
    }

    def __init__(self, parent,gridrow):
        "Initialise the ``Patrol``."
        Frame.__init__(
            self,
            parent
        )
        
        self.waiting=True
        
        self.hidecodexbtn=tk.IntVar(value=config.getint("Canonn:HideCodex"))
        self.hidecodex=self.hidecodexbtn.get()        
        
        self.container=Frame(self)
        self.container.columnconfigure(1, weight=1)
        #self.tooltip=Frame(self)
        #self.tooltip.columnconfigure(1, weight=1)
        #self.tooltip.grid(row = 1, column = 0,sticky="NSEW")
        
        #self.tooltiplist=tk.Frame(self.tooltip)
        self.tooltiplist=tk.Frame(self)
        
        self.images={}
        self.labels={}
        self.tooltipcol1=[]
        self.tooltipcol2=[]
        
        
        self.addimage("Geology",0)
        self.addimage("Cloud",1)
        self.addimage("Anomaly",2)
        self.addimage("Thargoid",3)
        self.addimage("Biology",4)
        self.addimage("Guardian",5)
        self.addimage("None",6)
        
        #self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        self.grid(row = gridrow, column = 0)
        self.container.grid(row = 0, column = 0, sticky="W")
        self.poidata=[]
        #self.tooltip.grid_remove()
        self.tooltiplist.grid_remove()
        self.grid_remove()
        
        
    def getdata(self,system):
    
        url = "https://us-central1-canonn-api-236217.cloudfunctions.net/poiList?system={}".format(system)
        debug(url)
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            self.poidata=r.json()
            self.waiting=False
            
            
            
    def enter(self,event):
    
        type=event.widget["text"]
        #clear it if it exists
        for col in self.tooltipcol1:
            col["text"]=""
            col.grid_remove()
        for col in self.tooltipcol2:
            col["text"]=""
            col.grid_remove()            
        
        poicount=0
        
        # need to initialise if not exists
        if len(self.tooltipcol1) == 0:
            self.tooltipcol1.append(tk.Label(self.tooltiplist,text=""))
            self.tooltipcol2.append(tk.Label(self.tooltiplist,text=""))
        
        
        for poi in self.poidata:
            if poi.get("hud_category") == type:
                ## add a new label if it dont exist
                if len(self.tooltipcol1)==poicount:
                    self.tooltipcol1.append(tk.Label(self.tooltiplist,text=poi.get("english_name")))
                    self.tooltipcol2.append(tk.Label(self.tooltiplist,text=poi.get("body")))
                else:    ## just set the label
                    self.tooltipcol1[poicount]["text"]=poi.get("english_name")
                    self.tooltipcol2[poicount]["text"]=poi.get("body")
                    
                #remember to grid them    
                self.tooltipcol1[poicount].grid(row=poicount,column=0,columnspan=1,sticky="NSEW")
                self.tooltipcol2[poicount].grid(row=poicount,column=1,sticky="NSEW")
                poicount=poicount+1
                
                
                
        if poicount ==0:
            self.tooltipcol1[poicount]["text"]=CodexTypes.tooltips.get(type)
            self.tooltipcol1[poicount].grid(row=poicount,column=0,columnspan=2)
            self.tooltipcol2[poicount].grid_remove()
        
        #self.tooltip.grid(sticky="NSEW")
        self.tooltiplist.grid(sticky="NSEW")
        
        ##self.tooltip["text"]=CodexTypes.tooltips.get(event.widget["text"])
        
    def leave(self,event):
        #self.tooltip.grid_remove()
        self.tooltiplist.grid_remove()
        
                    
    def addimage(self,name,col):
        
        grey="{}_grey".format(name)
        self.images[name] = tk.PhotoImage(file = os.path.join(CodexTypes.plugin_dir,"icons","{}.gif".format(name)))
        self.images[grey] = tk.PhotoImage(file = os.path.join(CodexTypes.plugin_dir,"icons","{}.gif".format(grey)))
        self.labels[name]=tk.Label(self.container,image=self.images.get(grey),text=name)
        self.labels[name].grid(row=0,column=col)
        
        self.labels[name].bind("<Enter>", self.enter)
        self.labels[name].bind("<Leave>", self.leave)
        self.labels[name].bind("<ButtonPress>", self.enter)
        
        
    def set_image(self,name,enabled):
        grey="{}_grey".format(name)
        
        if enabled:
            setting=name
        else:
            setting=grey          
            
        self.labels[name]["image"]=self.images.get(setting)
        
    def visualise(self):
            
        #we may want to try again if the data hasn't been fetched yet
        if self.waiting:
            debug("Still waiting");
            self.after(1000,self.visualise)
        else:    
            
            self.set_image("Geology",False)
            self.set_image("Cloud",False)
            self.set_image("Anomaly",False)
            self.set_image("Thargoid",False)
            self.set_image("Biology",False)
            self.set_image("Guardian",False)
            self.set_image("None",False)

            if self.poidata:
                self.grid()
                for r in self.poidata:
                    debug(r)
                    self.set_image(r.get("hud_category"),True)
            else:
                self.grid_remove()
            
            
        
    def journal_entry(self,cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):
        debug("CodeTypes journal_entry")
    
        if entry.get("event")in ("FSDJump") :
            #To avoid having check data we will assume we have some by now
     
            self.visualise()
        
        if entry.get("event") == "StartJump" and entry.get("JumpType") == "Hyperspace":
            # go fetch some data.It will 
            poiTypes(entry.get("StarSystem"),self.getdata).start()
            self.grid_remove()
            
        if entry.get("event") in ("Location","StartUp"):
            debug("Looking for POI data in {}".format(system))
            poiTypes(system,self.getdata).start()
            ## lets give it 1 seconds 
            self.after(1000,self.visualise)
        
    
    @classmethod    
    def plugin_start(cls,plugin_dir):
        cls.plugin_dir=plugin_dir
        
        
    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):
        "Called to get a tk Frame for the settings dialog."
        
        self.hidecodexbtn=tk.IntVar(value=config.getint("Canonn:HideCodex"))
        
        self.hidecodex=self.hidecodexbtn.get()
                        
        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row = gridrow, column = 0,sticky="NSEW")
        
        nb.Label(frame,text="Codex Settings").grid(row=0,column=0,sticky="NW")
        nb.Checkbutton(frame, text="Hide Codex Icons", variable=self.hidecodexbtn).grid(row = 1, column = 0,sticky="NW")
        
        return frame        
        
    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('Canonn:HideCodex', self.hidecodexbtn.get())      
        
        self.hidecodex=self.hidecodexbtn.get()
                
        #dont check the retval 
        #self.visible()
        

    def visible(self):
        
        noicons=(self.hidecodex == 1)
        
        if noicons:
            self.grid_remove()
            self.isvisible=False
            return False
        else:
            self.grid()
            self.isvisible=True
            return True                

# experimental
# submitting to a google cloud function
class gSubmitCodex(threading.Thread):
    def __init__(self,cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client):
        
        threading.Thread.__init__(self)
        #debug("gSubmitCodex({},{},{},{},{},{},{},{},{},{},{})".format((self,cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client)))
        self.cmdr=quote_plus(cmdr.encode('utf8'))
        self.system=quote_plus(system.encode('utf8'))
        self.x=x
        self.y=y
        self.z=z
        self.body=""
        self.lat=""
        self.lon=""
        if body:
            self.body=quote_plus(body.encode('utf8'))
        if lat:    
            self.lat=lat
            self.lon=lon
        
        if is_beta:
            self.is_beta = 'Y'
        else:
            self.is_beta = 'N'    
                    
        self.entry=entry
        
        

    def run(self):
        
        
        debug("sending gSubmitCodex")
        url="https://us-central1-canonn-api-236217.cloudfunctions.net/submitCodex?cmdrName={}".format(self.cmdr)
        url=url+"&system={}".format(self.system)
        url=url+"&body={}".format(self.body)
        url=url+"&x={}".format(self.x)
        url=url+"&y={}".format(self.y)
        url=url+"&z={}".format(self.z)
        url=url+"&latitude={}".format(self.lat)
        url=url+"&longitude={}".format(self.lon)
        url=url+"&entryid={}".format(self.entry.get("EntryID"))
        url=url+"&name={}".format(self.entry.get("Name").encode('utf8'))
        url=url+"&name_localised={}".format(self.entry.get("Name_Localised").encode('utf8'))
        url=url+"&category={}".format(self.entry.get("Category").encode('utf8'))
        url=url+"&category_localised={}".format(self.entry.get("Category_Localised").encode('utf8'))
        url=url+"&sub_category={}".format(self.entry.get("SubCategory").encode('utf8'))
        url=url+"&sub_category_localised={}".format(self.entry.get("SubCategory_Localised").encode('utf8'))
        url=url+"&region_name={}".format(self.entry.get("Region").encode('utf8'))
        url=url+"&region_name_localised={}".format(self.entry.get("Region_Localised").encode('utf8'))
        url=url+"&is_beta={}".format(self.is_beta)
        
        debug(url)
                    
        r=requests.get(url)
    
        if not r.status_code == requests.codes.ok:
            error("gSubmitCodex {} ".format(url))
            error(r.status_code)
            error(r.json())


class codexEmitter(Emitter):
    types={}
    reporttypes={}
    excludecodices={}
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        Emitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="xxreports"
        self.modeltype="xxtypes"
        
    def getSystemPayload(self,name):
        payload=self.setPayload()
        payload["userType"]="pc"
        payload["reportType"]="new"
        payload["type"]=name
        payload["reportStatus"]="pending"
        payload["isBeta"]=self.is_beta
        payload["clientVersion"]=self.client
    
        return payload           

    def getBodyPayload(self,name):
        payload=self.getSystemPayload(name)
        payload["bodyName"]=self.body
        payload["coordX"]=self.x
        payload["coordY"]=self.y
        payload["coordZ"]=self.z
        payload["latitude"]=self.lat
        payload["longitude"]=self.lon
    
        return payload           
    
    def getCodexPayload(self):
        payload=self.getBodyPayload(self.entry.get("Name"))
        payload["entryId"]=self.entry.get("EntryID")
        payload["codexName"]=self.entry.get("Name")
        payload["codexNameLocalised"]=self.entry.get("Name_Localised")
        payload["subCategory"]=self.entry.get("SubCategory")
        payload["subCategoryLocalised"]=self.entry.get("SubCategory_Localised")
        payload["category"]=self.entry.get("Category")
        payload["categoryLocalised"]=self.entry.get("Category_Localised")
        payload["regionName"]=self.entry.get("Region")
        payload["regionLocalised"]=self.entry.get("Region_Localised")
        payload["systemAddress"]=self.entry.get("SystemAddress")
        payload["voucherAmount"]=self.entry.get("VoucherAmount")
        payload["rawJson"]=self.entry
        del payload["type"]
        del payload["reportStatus"]
        del payload["userType"]
        del payload["reportType"]
        
        return payload
    
    def getReportTypes(self,id):
        if not codexEmitter.reporttypes.get(id):        
            url="{}/reporttypes?journalID={}&_limit=1000".format(self.getUrl(),id)
            debug(url)
            r=requests.get("{}/reporttypes?journalID={}&_limit=1000".format(self.getUrl(),id))    
            if r.status_code == requests.codes.ok:

                for exc in r.json():

                    codexEmitter.reporttypes["{}".format(exc["journalID"])]={ "endpoint": exc["endpoint"], "location": exc["location"], "type": exc["type"]}
                    
            else:
                error("error in getReportTypes")
                
    def getExcluded(self):
        if not codexEmitter.excludecodices:
            tempexclude={}
            r=requests.get("{}/excludecodices&_limit=1000".format(self.getUrl()))  
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    tempexclude["${}_name;".format(exc["codexName"])]=True
                
                codexEmitter.excludecodices=tempexclude
                    
    def run(self):
        
        self.getExcluded()
        
        
        
        #is this a code entry and do we want to record it? 
        if not codexEmitter.excludecodices.get(self.entry.get("Name").lower()) and not self.entry.get("Category") == '$Codex_Category_StellarBodies;':
            self.getReportTypes(self.entry.get("EntryID"))    
            url=self.getUrl()
       
            # going to take advantage of strapi and execute our google function here
            gSubmitCodex(self.cmdr, self.is_beta, self.system, self.x,self.y,self.z,self.entry, self.body,self.lat,self.lon,self.client).start()   
            
            jid=self.entry.get("EntryID")
            reportType = codexEmitter.reporttypes.get(str(jid))
            
            if reportType:
                debug(reportType)
                if reportType.get("location") == "body":
                    payload=self.getBodyPayload(reportType.get("type"))
                    self.modelreport=reportType.get("endpoint")
                else:
                    payload=self.getSystemPayload(reportType.get("type"))
                    self.modelreport=reportType.get("endpoint")
            else:
                payload=self.getCodexPayload()
                self.modelreport="reportcodices"
                
            debug("Send Reports {}/{}".format(url,self.modelreport))
            
            self.send(payload,url)
            
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
    if entry["event"] == "CodexEntry" :
        codexEmitter(cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client).start()   
       