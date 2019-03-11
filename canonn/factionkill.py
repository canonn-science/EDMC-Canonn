import threading
import requests
import sys
import json
from emitter import Emitter
from debug import Debug
from debug import debug,error

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


class FactionKill(Emitter):
    
    def __init__(self,cmdr, is_beta, system,entry,client):
        Emitter.__init__(self,cmdr, is_beta, system, None,None,None, entry, None,None,None,client)
        self.modelreport="killreports"
        
    def setPayload(self):
        payload={}
        payload["systemname"]=self.system
        payload["cmdrName"]=self.cmdr  
        payload["rawEvent"]=self.entry
        payload["reward"]=self.entry["Reward"]
        payload["rewardingFaction"]=self.entry["AwardingFaction"]
        payload["victimFaction"]=self.entry["VictimFaction"]
        payload["isbeta"]= self.is_beta
        payload["clientVersion"]= self.client
            
        return payload

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
        FactionKill(cmdr, is_beta, system,  entry, client).start()   

