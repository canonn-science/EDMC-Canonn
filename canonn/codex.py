import threading
import requests
import sys
import json



class Codex(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    def __init__(self,cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
        threading.Thread.__init__(self)
        self.cmdr = cmdr
        self.system = system
        
        self.x=x
        self.y=y
        self.z=z
        self.body = body
        self.lat = lat
        self.lon = lon
        self.is_beta = is_beta
        self.entry = entry.copy()
        seles.client = client
        
        
        
        

        
    def run(self):
        payload={}
        payload["cmdrName"]=self.cmdr  
        payload["systemName"]=self.system
        payload["bodyName"]=self.body
        
        payload["coordX"]=self.x
        payload["coordY"]=self.y
        payload["coordZ"]=self.z
        payload["latitude"]=self.lat
        payload["longitude"]=self.lon
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
        payload["isBeta"]=self.is_beta
        payload["clientVersion"]=self.client
            
        try:        
            r=requests.post("https://api.canonn.tech:2053/codexreports",data=json.dumps(payload),headers={"content-type":"application/json"})  
        except:
            print("[EDMC-Canonn] Issue posting codex entry " + str(sys.exc_info()[0]))                            
            print r
        
def matches(d, field, value):
	return field in d and value == d[field]	        
            
'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
  
'''
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
    if entry["event"] == "CodexEntry":
        Codex(cmdr, is_beta, system, x,y,z,entry, body,lat,lon,client).start()   
    
    
