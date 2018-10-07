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

class UssDrop(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    def __init__(self,cmdr, is_beta, system, station, entry):
        threading.Thread.__init__(self)
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.is_beta = is_beta
        self.entry = entry.copy()

        
    def run(self):
        payload={}
        payload["systemName"]=self.system
        payload["cmdrName"]=self.cmdr  
        payload["ussRawJson"]=self.entry
        payload["threatLevel"]=self.entry["USSThreat"]
        payload["type"]=self.entry["USSType"][1:-1]
        payload["isbeta"]= self.is_beta
            
        try:        
            r=requests.post("https://api.canonn.tech:2053/ussreports",data=json.dumps(payload),headers={"content-type":"application/json"})  
            print payload
            print r
        except:
            print("[EDMC-Canonn] Issue posting FactionKIll " + str(sys.exc_info()[0]))                            
            print r
        
def matches(d, field, value):
	return field in d and value == d[field]	        
            
'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
  
'''
def submit(cmdr, is_beta, system, station, entry):
    if entry["event"] == "USSDrop" :
        UssDrop(cmdr, is_beta, system, station, entry).start()   
    

