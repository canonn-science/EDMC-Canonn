import threading    
import requests
import sys
import json

'''
    { "timestamp":"2018-10-07T13:03:02Z", 
    "event":"USSDrop", 
    "USSType":"$USS_Type_NonHuman;", 
    "USSType_Localised":"Non-Human signal source", 
    "USSThreat":4 }

'''

class HDReport(threading.Thread):

    hdsystem=""
    
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    def __init__(self,cmdr, is_beta, system, station, entry,client):
        threading.Thread.__init__(self)
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client=client

        
    def run(self):
        payload={}
        
        payload["fromSystemName"]=self.entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
        payload["cmdrName"]=self.cmdr  
        payload["isbeta"]= self.is_beta
        payload["clientVersion"]= self.client
        payload["reportStatus"]="accepted"
        payload["reportComment"]="Hyperdiction from TG_ENCOUNTERS"
        payload["hdRawJson"]=self.entry.get("TG_ENCOUNTERS")
        
            
        try:        
            r=requests.post("https://api.canonn.tech:2053/hdreports",data=json.dumps(payload),headers={"content-type":"application/json"})  
            #print payload
            #print r
        except:
            print("[EDMC-Canonn] Issue posting ussReport " + str(sys.exc_info()[0]))                            
            print r
        
def matches(d, field, value):
	return field in d and value == d[field]	        
            
'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
  
'''
def submit(cmdr, is_beta, system, station, entry,client):
      
    # The last system isnt always set so we can ignore 
    if entry["event"] == "Statistics" and entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM"):
        
        lastsystem=entry.get("TG_ENCOUNTERS").get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")   
        if HDReport.hdsystem == lastsystem:
            print("Hyperdiction already recorded here ")
        else:
            HDReport.hdsystem = lastsystem
            HDReport(cmdr, is_beta, lastsystem, station, entry,client).start()   
        
        
    

