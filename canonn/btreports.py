import threading
import requests
import sys
import json

'''
    {   
        "timestamp":"2018-10-07T13:03:47Z", 
        "event":"FactionKillBond", 
        "Reward":10000, 
        "AwardingFaction":"$faction_PilotsFederation;", 
        "AwardingFaction_Localised":"Pilots Federation", 
        "VictimFaction":"$faction_Thargoid;", 
        "VictimFaction_Localised":"Thargoids" 
    }
'''

class btReports(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    
    bttypes=[]
    btlist={}
    
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

    def run(self):
    
        # only need to get the types once doing it here to because it is in its ownthread
        if not btReports.bttypes:
            r=requests.get("https://api.canonn.tech:2053/bttypes")  
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    if exc.get("journalID"):
                        btReports.bttypes.append(exc.get("journalID"))
                        btReports.btlist[exc.get("journalID")]=exc.get("type")
                print btReports.bttypes
                
                
                
        if self.entry.get("EntryID") in btReports.bttypes:
            name=btReports.btlist.get(self.entry.get("EntryID"))
            payload={}
            payload["userType"]="pc"
            payload["reportType"]="new"
            payload["cmdrName"]=self.cmdr  
            payload["systemName"]=self.system
            payload["bodyName"]=self.body
            payload["coordX"]=self.x
            payload["coordY"]=self.y
            payload["coordZ"]=self.z
            payload["latitude"]=self.lat
            payload["longitude"]=self.lon
            #payload["entryId"]=self.entry.get("EntryID")
            payload["type"]=name
            payload["reportStatus"]="pending"
            #payload["codexName"]=self.entry.get("Name")
            #payload["codexNameLocalised"]=self.entry.get("Name_Localised")
            #payload["subCategory"]=self.entry.get("SubCategory")
            #payload["subCategoryLocalised"]=self.entry.get("SubCategory_Localised")
            #payload["category"]=self.entry.get("Category")
            #payload["categoryLocalised"]=self.entry.get("Category_Localised")
            #payload["regionID"]=self.entry.get("Region")
            #payload["regionLocalised"]=self.entry.get("Region_Localised")
            #payload["systemAddress"]=self.entry.get("SystemAddress")
            #payload["voucherAmount"]=self.entry.get("VoucherAmount")
            #payload["rawJson"]=self.entry
            payload["isBeta"]=self.is_beta
            payload["clientVersion"]=self.client
                
                      
            r=requests.post("https://api.canonn.tech:2053/btreports",data=json.dumps(payload),headers={"content-type":"application/json"})  
            if not r.status_code == requests.codes.ok:
                print r.status_code
                print r.json()
                print json.dumps(payload)            

def matches(d, field, value):
	return field in d and value == d[field]	        
            
'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
'''
def submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):


    if entry["event"] == "CodexEntry":
        btReports(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client).start()   

