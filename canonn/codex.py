import threading
import requests
import sys
import json
from emitter import Emitter
from urllib import quote_plus
from debug import Debug
from debug import debug,error

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
            r=requests.get("{}/excludecodices&_limit=1000".format(self.getUrl()))  
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    codexEmitter.excludecodices["${}_name;".format(exc["codexName"])]=True
                    
    def run(self):
        
        self.getExcluded()
        
        
        
        #is this a code entry and do we want to record it? 
        if not codexEmitter.excludecodices.get(self.entry.get("Name").lower()):
            self.getReportTypes(self.entry.get("EntryID"))    
            url=self.getUrl()
            
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