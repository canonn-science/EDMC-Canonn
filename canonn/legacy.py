# -*- coding: utf-8 -*-
import threading
import requests
from urllib import quote_plus
import sys
from  math import sqrt,pow,trunc
from debug import Debug
from debug import debug,error

class Reporter(threading.Thread):
    def __init__(self, payload):
        threading.Thread.__init__(self)
        self.payload = payload

    def run(self):
        try:
            requests.get(self.payload)
        except:
            print("Issue posting message " + str(sys.exc_info()[0]))
            


def getDistance(x1,y1,z1,x2,y2,z2):
    return round(sqrt(pow(float(x2)-float(x1),2)+pow(float(y2)-float(y1),2)+pow(float(z2)-float(z1),2)),2)

def getDistanceMerope(x1,y1,z1):
    return round(sqrt(pow(float(-78.59375)-float(x1),2)+pow(float( -149.625)-float(y1),2)+pow(float(-340.53125)-float(z1),2)),2)        
    
def getDistanceSol(x1,y1,z1):
    return round(sqrt(pow(float(0)-float(x1),2)+pow(float(0)-float(y1),2)+pow(float(0)-float(z1),2)),2)         
        
        
def matches(d, field, value):
    return field in d and value == d[field]     
        
def faction_kill(cmdr, is_beta, system, station, entry, state):
    if entry['event'] == "FactionKillBond":
        factionMatch=(matches(entry, 'VictimFaction', '$faction_Thargoid;') or matches(entry, 'VictimFaction', '$faction_Guardian;'))
        if factionMatch and 'Reward' in entry:
            url="https://docs.google.com/forms/d/e/1FAIpQLSevc8RrhOzOq9U0a2VC29N_lgjRfVU9vlF-oKdjhvZu6YnLvw/formResponse?usp=pp_url"
            url+="&entry.567957318="+quote_plus(cmdr)
            if is_beta:
                beta='Y'
            else: 
                beta='N'
            url+="&entry.1848556807="+quote_plus(beta)
            url+="&entry.1086702490="+quote_plus(system)
            if station is not None:
                url+="&entry.1446740035="+quote_plus(station)
            
            url+="&entry.396335290="+str(entry["Reward"])
            url+="&entry.576102634="+quote_plus(entry["AwardingFaction"])
            url+="&entry.691973931="+quote_plus(entry["VictimFaction"])
            Reporter(url).start()

def CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client):
    #{ "timestamp":"2018-12-30T00:48:12Z", "event":"CodexEntry", "EntryID":2100301, "Name":"$Codex_Ent_Cone_Name;", "Name_Localised":"Bark Mounds", "SubCategory":"$Codex_SubCategory_Organic_Structures;", "SubCategory_Localised":"Organic structures", "Category":"$Codex_Category_Biology;", "Category_Localised":"Biological and Geological", "Region":"$Codex_RegionName_18;", "Region_Localised":"Inner Orion Spur", "System":"HIP 16378", "SystemAddress":1, "VoucherAmount":2500 }
    if entry['event'] == "CodexEntry":
        url="https://docs.google.com/forms/d/e/1FAIpQLSfdr7GFj6JJ1ubeRXP_uZu3Xx9HPYT6507lRLqqC0oUZyj-Jg/formResponse?usp=pp_url"

        url+="&entry.1415400073="+quote_plus(cmdr)
        url+="&entry.1860059185="+quote_plus(system)
        url+="&entry.810133478="+str(x)
        url+="&entry.226558470="+str(y)
        url+="&entry.1643947574="+str(z)
        if body:
            url+="&entry.1432569164="+quote_plus(body)
        if lat:
            url+="&entry.1891952962="+str(lat)
            url+="&entry.405491858="+str(lon)
        url+="&entry.1531581549="+quote_plus(str(entry["EntryID"]))
        url+="&entry.1911890028="+quote_plus(entry["Name"])
        url+="&entry.1057995915="+quote_plus(entry["Name_Localised"])
        url+="&entry.598514572="+quote_plus(entry["SubCategory"])
        url+="&entry.222515268="+quote_plus(entry["SubCategory_Localised"])
        url+="&entry.198049318="+quote_plus(entry["Category"])
        url+="&entry.348683576="+quote_plus(entry["Category_Localised"])
        url+="&entry.761612585="+quote_plus(entry["Region"])
        url+="&entry.216399442="+quote_plus(entry["Region_Localised"])
        url+="&entry.1236018468="+quote_plus(str(entry["SystemAddress"]))
        if('VoucherAmount' in entry):
            url+="&entry.1250864566="+quote_plus(str(entry["VoucherAmount"]))
                
        
        Reporter(url).start()

        
def AXZone(cmdr, is_beta, system,x,y,z,station, entry, state):
    #{ "timestamp":"2019-01-19T23:22:26Z", "event":"FSSSignalDiscovered", "SystemAddress":250414621860, "SignalName":"$Warzone_TG;", "SignalName_Localised":"AX Conflict Zone" }
    if entry['event'] == "FSSSignalDiscovered" and entry["SignalName"] == "$Warzone_TG;":
        
        url="https://docs.google.com/forms/d/e/1FAIpQLSdHFZ8Mp4EHsJH6gUqXyeWkeEUt3YOGEaOO3X8H4m-gHNYzdQ/formResponse?usp=pp_url"

        
        url+="&entry.1257612503="+quote_plus(cmdr)
        url+="&entry.1541680555="+quote_plus(system)
        url+="&entry.484596368="+str(x)
        url+="&entry.1443755704="+str(y)
        url+="&entry.1285491432="+str(z)
        url+="&entry.837147926="+str(entry.get("SystemAddress"))
        
        Reporter(url).start()

## I want to avoid sending this event if there has not been any change
## so we will have a global dict

class Stats():
    
    tg_stats = {
        "tg_encounter_wakes": 0,
        "tg_encounter_imprint": 0,
        "tg_encounter_total": 0,
        "tg_timestamp": 'x',
        "tg_scout_count": 0,
        "tg_last_system": "x"
    }
    
    @classmethod    
    def statistics(this,cmdr, is_beta, system, station, entry, state):
        
        if entry['event'] == "Statistics":
            tge=entry.get('TG_ENCOUNTERS')
            new_tg_stats = {
                "tg_encounter_wakes": tge.get("TG_ENCOUNTER_WAKES"),
                "tg_encounter_imprint": tge.get("TG_ENCOUNTER_IMPRINT"),
                "tg_encounter_total": tge.get("TG_ENCOUNTER_TOTAL"),
                "tg_timestamp": tge.get("TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP"),
                "tg_scout_count": tge.get("TG_SCOUT_COUNT"),
                "tg_last_system": tge.get("TG_ENCOUNTER_TOTAL_LAST_SYSTEM")
            }
            if new_tg_stats != this.tg_stats:

                this.tg_stats=new_tg_stats
                url="https://docs.google.com/forms/d/e/1FAIpQLScF_URtGFf1-CyMNr4iuTHkxyxOMWcrZ2ZycrKAiej0eC-hTA/formResponse?usp=pp_url"
                url+="&entry.613206362="+quote_plus(cmdr)
                if "TG_ENCOUNTER_WAKES" in entry['TG_ENCOUNTERS']:
                    url+="&entry.1085684396="+str(entry['TG_ENCOUNTERS']["TG_ENCOUNTER_WAKES"])
                if "TG_ENCOUNTER_IMPRINT" in entry['TG_ENCOUNTERS']:
                    url+="&entry.2026302508="+str(entry['TG_ENCOUNTERS']["TG_ENCOUNTER_IMPRINT"])
                if "TG_ENCOUNTER_TOTAL" in entry['TG_ENCOUNTERS']:
                    url+="&entry.1600696255="+str(entry['TG_ENCOUNTERS']["TG_ENCOUNTER_TOTAL"])
                if "TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP" in entry['TG_ENCOUNTERS']:
                    url+="&entry.712826938="+str(entry['TG_ENCOUNTERS']["TG_ENCOUNTER_TOTAL_LAST_TIMESTAMP"])
                if "TG_SCOUT_COUNT" in entry['TG_ENCOUNTERS']:
                    url+="&entry.1384358412="+str(entry['TG_ENCOUNTERS']["TG_SCOUT_COUNT"])
                if "TG_ENCOUNTER_TOTAL_LAST_SYSTEM" in entry['TG_ENCOUNTERS']:
                    url+="&entry.1091946522="+str(entry['TG_ENCOUNTERS']["TG_ENCOUNTER_TOTAL_LAST_SYSTEM"])
                Reporter(url).start()
                
        
        
def statistics(cmdr, is_beta, system, station, entry, state):  
    Stats.statistics(cmdr, is_beta, system, station, entry, state)

class NHSS(threading.Thread):

    fss= {}
    
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    def __init__(self,cmdr, is_beta, system, x,y,z,station, entry,client):
        threading.Thread.__init__(self)
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client=client
        self.x=x
        self.y=y
        self.z=z

    def run(self):
        payload={}

        if self.entry["event"] == 'FSSSignalDiscovered':
            threatLevel=self.entry.get("ThreatLevel")
            type="FSS"
        else:
            threatLevel=self.entry.get("USSThreat")
            type="Drop"

        payload["systemName"]=self.system
        payload["cmdrName"]=self.cmdr  
        payload["nhssRawJson"]=self.entry
        payload["threatLevel"]=threatLevel
        payload["isbeta"]= self.is_beta
        payload["clientVersion"]= self.client
        payload["reportStatus"]="accepted"
        payload["reportComment"]=type

        dsol=getDistance(0,0,0,self.x,self.y,self.z)
        dmerope=getDistance(-78.59375,149.625,-340.53125,self.x,self.y,self.z)
        
        url = "https://docs.google.com/forms/d/e/1FAIpQLScVk2LW6EkIW3hL8EhuLVI5j7jQ1ZmsYCLRxgCZlpHiN8JdcA/formResponse?usp=pp_url"
        url+="&entry.106150081="+quote_plus(self.cmdr)
        url+="&entry.582675236="+quote_plus(self.system)
        url+="&entry.158339236="+str(self.x)
        url+="&entry.608639155="+str(self.y)
        url+="&entry.1737639503="+str(self.z)
        url+="&entry.1398738264="+str(dsol)
        url+="&entry.922392846="+str(dmerope)
        url+="&entry.218543806="+quote_plus("$USS_Type_NonHuman;")
        url+="&entry.455413428="+quote_plus("Non-Human signal source")
        url+="&entry.790504343="+str(threatLevel)
        r=requests.post(url)  
        
        url="https://docs.google.com/forms/d/e/1FAIpQLSeOBbUTiD64FyyzkIeZfO5UMfqeuU2lsRf3_Ulh7APddd91JA/formResponse?usp=pp_url"
        url+="&entry.306505776="+quote_plus(self.system)
        url+="&entry.1559250350=Non Human Signal"
        url+="&entry.1031843658="+str(threatLevel)
        url+="&entry.1519036101="+quote_plus(self.cmdr)
        r=requests.post(url)  



    @classmethod
    def submit(cls,cmdr, is_beta, system,x,y,z, station, entry,client):

        #USS and FFS
        if entry["event"] in ("USSDrop",'FSSSignalDiscovered') and entry.get("USSType") == "$USS_Type_NonHuman;" : 

            # The have different names for teh same thing so normalise
            if entry["event"] == 'FSSSignalDiscovered':
                threatLevel=entry.get("ThreatLevel")
            else:
                threatLevel=entry.get("USSThreat")

            # see if you have system and threat levels store
            # Thsi will fail if it a new threat level in the current system
            try:
                globalfss=NHSS.fss.get(system)
                oldthreat=globalfss.get(threatLevel)
                #debug(globalfss)
            except:
                oldthreat=False

            if oldthreat:
                debug("Threat level already recorded here "+str(threatLevel))

            else:
                #debug("Threat {}".format(threatLevel))
                try:
                    #set the threatlevel for the system
                    NHSS.fss[system][threatLevel] =  True
                except:
                    #we couldnt find teh system so lets define it
                    NHSS.fss[system]={ threatLevel: True}

                NHSS(cmdr, is_beta, system,x,y,z, station, entry,client).start()
