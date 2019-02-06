import threading
import requests
import sys
import json



class Emitter(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
              
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
        self.entry = entry.copy()
        self.client = client
        self.urls={ 
        "live": "https://api.canonn.tech:2053",
        "staging": "https://api.canonn.tech:2053",
        "development":  "https://api.canonn.tech:2083"
        }
        self.modelreport="breports"

    def getUrl(self):
        if self.is_beta:
            url=self.urls.get("staging")
        else:
            url=self.urls.get("live")
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
        r=requests.post("{}/{}".format(url,self.modelreport),data=json.dumps(payload),headers={"content-type":"application/json"})  
        if not r.status_code == requests.codes.ok:
            print "{}/{}".format(url,self.modelreport)
            print r.status_code
            print r.json()
            print json.dumps(payload)            

class surfaceEmitter(Emitter):
    types={}
    
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        Emitter.__init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
        self.modelreport="xxreports"
        self.modeltype="xxtypes"
        
    
    def getPayload(self,name):
        payload=self.setPayload()
        payload["userType"]="pc"
        payload["reportType"]="new"
        payload["bodyName"]=self.body
        payload["coordX"]=self.x
        payload["coordY"]=self.y
        payload["coordZ"]=self.z
        payload["latitude"]=self.lat
        payload["longitude"]=self.lon
        payload["type"]=name
        payload["reportStatus"]="pending"
        payload["isBeta"]=self.is_beta
        payload["clientVersion"]=self.client
    
        return payload   
    
    def run(self):
    
        url=self.getUrl()
        # only need to get the types once doing it here to because it is in its ownthread
        if not surfaceEmitter.types.get(self.modeltype):
            r=requests.get("{}/{}".format(url,self.modeltype))  
            #print "{}/{}".format(url,self.modeltype)
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    if exc.get("journalID"):
                        if surfaceEmitter.types.get(self.modeltype):
                            surfaceEmitter.types.get(self.modeltype)[exc.get("journalID")] = exc.get("type") 
                        else:
                            surfaceEmitter.types[self.modeltype]={ exc.get("journalID"):  exc.get("type") }
                #print "{} {}".format(self.modeltype, surfaceEmitter.types)
        
        
        #print ("prepping report")
        #print(surfaceEmitter.types.get(self.modeltype).keys())
        if self.entry["event"] == "CodexEntry" and self.entry.get("EntryID") in surfaceEmitter.types.get(self.modeltype).keys():
            print ("Send Reports")
            name=surfaceEmitter.types[self.modeltype].get(self.entry.get("EntryID"))
            payload=self.getPayload(name)      
            url=self.getUrl()
            self.send(payload,url)
            

            
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
            url="https://api.canonn.tech:2053/reporttypes?journalID={}".format(id)
            print(url)
            r=requests.get("https://api.canonn.tech:2053/reporttypes?journalID={}".format(id))    
            if r.status_code == requests.codes.ok:
                print("before reporttype")
                               
                for exc in r.json():
                    print("looney")
                    codexEmitter.reporttypes["{}".format(exc["journalID"])]={ "endpoint": exc["endpoint"], "location": exc["location"], "type": exc["type"]}
                    print("get reporttype")
                    print(codexEmitter.reporttypes) 
            else:
                print("error")
                
                    
    def getExcluded(self):
        if not codexEmitter.excludecodices:
            r=requests.get("https://api.canonn.tech:2053/excludecodices")  
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    codexEmitter.excludecodices["${}_name;".format(exc["codexName"])]=True
                    
    def run(self):
    
        
        self.getExcluded()
        
        #is this a code entry and do we want to record it?
        if self.entry["event"] == "CodexEntry" and not codexEmitter.excludecodices.get(self.entry.get("codexName")):
            self.getReportTypes(self.entry.get("EntryID"))    
            url=self.getUrl()
            
            print("XXX")
            print(codexEmitter.reporttypes) 
            jid=self.entry.get("EntryID")
            reportType = codexEmitter.reporttypes.get([jid])
            print(reportType)
            
            
            if self.entry.get("EntryID"):
                print("XXX")
                print(self.entry.get("EntryID"))
            
            
            if reportType:
                print(reportType)
                if reportType.get("location") == "body":
                    payload=self.getBodyPayload(reportType.get("type"))
                    self.modelreport=reportType.get("endpoint")
                else:
                    payload=self.getSystemPayload(reportType.get("type"))
                    self.modelreport=reportType.get("endpoint")
            else:
                payload=self.getCodexPayload()
                self.modelreport="codexreports"
                   
            print ("Send Reports {}/{}".format(url,self.modelreport))
            
            self.send(payload,url)
            
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
    codexEmitter(cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client).start()   

            