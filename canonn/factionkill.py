import threading
import requests
import sys
import json

'''
    {   "timestamp":"2018-10-07T13:03:47Z", 
        "event":"FactionKillBond", 
        "Reward":10000, 
        "AwardingFaction":"$faction_PilotsFederation;", 
        "AwardingFaction_Localised":"Pilots Federation", 
        "VictimFaction":"$faction_Thargoid;", 
        "VictimFaction_Localised":"Thargoids" }

'''

class FactionKill(threading.Thread):
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
        self.client = client

        
    def run(self):
        payload={}
        payload["systemname"]=self.system
        payload["cmdrName"]=self.cmdr  
        payload["rawEvent"]=self.entry
        payload["reward"]=self.entry["Reward"]
        payload["rewardingFaction"]=self.entry["AwardingFaction"]
        payload["victimFaction"]=self.entry["VictimFaction"]
        payload["isbeta"]= self.is_beta
        payload["clientVersion"]= self.client
            
        try:        
            r=requests.post("https://api.canonn.tech:2053/killreports",data=json.dumps(payload),headers={"content-type":"application/json"})  
        except:
            print("[EDMC-Canonn] Issue posting FactionKIll " + str(sys.exc_info()[0]))                            
            print r
        
def matches(d, field, value):
	return field in d and value == d[field]	        
            
'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
  
'''
def submit(cmdr, is_beta, system, station, entry,client):
    if entry["event"] == "FactionKillBond" and (
        matches(entry, 'VictimFaction', '$faction_Thargoid;') or 
        matches(entry, 'VictimFaction', '$faction_Guardian;')
    ):
        FactionKill(cmdr, is_beta, system, station, entry,client).start()   
    
    
