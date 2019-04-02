import threading
import requests
from urllib import quote_plus
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

# experimental
# submitting to a google cloud function
class gSubmitKill(threading.Thread):
    def __init__(self,cmdr, is_beta, system, reward,victimFaction):
        threading.Thread.__init__(self)
        self.cmdr=quote_plus(cmdr.encode('utf8'))
        self.system=quote_plus(system.encode('utf8'))
        if is_beta:
            self.is_beta = 'Y'
        else:
            self.is_beta = 'N'    
        self.reward=str(reward)
        self.victimFaction=quote_plus(victimFaction.encode('utf8'))

    def run(self):
        # don't bother sending beta
        if self.is_beta == 'N':
            debug("sending gSubmitKill")
            url="https://us-central1-canonn-api-236217.cloudfunctions.net/submitKills?cmdrName={}&systemName={}&isBeta={}&reward={}&victimFaction={}".format(self.cmdr,self.system,self.is_beta,self.reward,self.victimFaction)    
            
            r=requests.get(url)
        
            if not r.status_code == requests.codes.ok:
                error("gSubmitKills {} ".format(url))
                error(r.status_code)
                error(r.json())
                        
                

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
        gSubmitKill(cmdr, is_beta, system, entry.get("Reward"),entry.get("VictimFaction")).start();

