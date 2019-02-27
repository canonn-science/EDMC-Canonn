# -*- coding: utf-8 -*-
import threading
import requests
from urllib import quote_plus
import sys

class Reporter(threading.Thread):
    def __init__(self, payload):
        threading.Thread.__init__(self)
        self.payload = payload

    def run(self):
        try:
            requests.get(self.payload)
        except:
            print("Issue posting message " + str(sys.exc_info()[0]))
            

class USSDetector:
    'Class for Detecting USS Drops'

    def __init__(self,frame):
        debug("Initiating USS Detector")
        self.frame=frame
        self.uss = False
        today=datetime.datetime.now()
        self.arrival=today.strftime("%Y/%m/%d %H:%M:%S")
        ## we might start in system and so never have jumped
        self.jumped=False

    def Location(self,cmdr, system, station, entry):        
        self.arrival=entry["timestamp"].replace("T"," ").replace("-","/").replace("Z","")
        self.sysx=entry["StarPos"][0]
        self.sysy=entry["StarPos"][1]
        self.sysz=entry["StarPos"][2]
        # need to set this so we know we have coordinates available
        self.jumped=True
        
    def FSDJump(self,cmdr, system, station, entry):
        self.arrival=entry["timestamp"].replace("T"," ").replace("-","/").replace("Z","")
        self.sysx=entry["StarPos"][0]
        self.sysy=entry["StarPos"][1]
        self.sysz=entry["StarPos"][2]
        # need to set this so we know we have coordinates available
        self.jumped=True
      
    def ussDrop(self,cmdr, system, station, entry):
        debug("USS Drop",2)
        self.uss=True
        self.usstype=entry['USSType']
        self.usslocal=entry['USSType_Localised']
        self.threat=str(entry['USSThreat'])  

    def FSSDetect(self,cmdr, system, station, entry):
        debug("FSSDetect",2)
        
        try:
            globalfss=fss.get(system)
            oldthreat=globalfss.get(entry.get("ThreatLevel"))
        except:
            oldthreat=False
        
        if oldthreat==True:
            debug("Threat level already recorded here "+str(entry.get("ThreatLevel")))
        else:
            try:
                fss[system][entry.get("ThreatLevel")] =  True
            except:
                fss[system]={ entry.get("ThreatLevel"): True}
          
                
            debug("Recording threat level "+str(entry.get("ThreatLevel")))
            debug(fss)
            usstype=entry['USSType']
            usslocal=entry['USSType_Localised']
            threat=str(entry['ThreatLevel'])
            self.sysx,self.sysy,self.sysz=edsmGetSystem(system)
                    
                    
            dmerope=getDistanceMerope(self.sysx,self.sysy,self.sysz)
            dsol=getDistanceSol(self.sysx,self.sysy,self.sysz)
            
                                        
            url = "https://docs.google.com/forms/d/e/1FAIpQLScVk2LW6EkIW3hL8EhuLVI5j7jQ1ZmsYCLRxgCZlpHiN8JdcA/formResponse?usp=pp_url&entry.1236915632="+str(this.guid)+"&entry.106150081="+cmdr+"&entry.582675236="+quote_plus(system)+"&entry.158339236="+str(self.sysx)+"&entry.608639155="+str(self.sysy)+"&entry.1737639503="+str(self.sysz)+"&entry.1398738264="+str(dsol)+"&entry.922392846="+str(dmerope)+"&entry.218543806="+quote_plus(usstype)+"&entry.455413428="+quote_plus(usslocal)+"&entry.790504343="+quote_plus(threat)+"&submit=Submit"
                #print url
            Reporter(url).start()        
            url="https://docs.google.com/forms/d/e/1FAIpQLSeOBbUTiD64FyyzkIeZfO5UMfqeuU2lsRf3_Ulh7APddd91JA/formResponse?usp=pp_url"
            url+="&entry.306505776="+quote_plus(system)
            url+="&entry.1559250350=Non Human Signal"
            url+="&entry.1031843658="+str(threat)
            url+="&entry.1519036101="+quote_plus(cmdr)
            Reporter(url).start()        
        
            
    def SupercruiseExit(self,cmdr, system, station, entry):
        if self.uss:
            #This is a USS drop set back to false
            self.uss=False
                    
            
            self.sysx,self.sysy,self.sysz=edsmGetSystem(system)
                
                
            dmerope=getDistanceMerope(self.sysx,self.sysy,self.sysz)
            dsol=getDistanceSol(self.sysx,self.sysy,self.sysz)
            self.timestamp=entry["timestamp"].replace("T"," ").replace("-","/").replace("Z","")
            
            # lets calculate how long it too before you saw that USS
            minutes=dateDiffMinutes(self.arrival,self.timestamp)
            debug("Minutes before USS = "+str(minutes),2)
                                            
            url = "https://docs.google.com/forms/d/e/1FAIpQLScVk2LW6EkIW3hL8EhuLVI5j7jQ1ZmsYCLRxgCZlpHiN8JdcA/formResponse?usp=pp_url&entry.1236915632="+str(this.guid)+"&entry.106150081="+cmdr+"&entry.582675236="+quote_plus(entry['StarSystem'])+"&entry.158339236="+str(self.sysx)+"&entry.608639155="+str(self.sysy)+"&entry.1737639503="+str(self.sysz)+"&entry.413701316="+quote_plus(entry['Body'])+"&entry.1398738264="+str(dsol)+"&entry.922392846="+str(dmerope)+"&entry.218543806="+quote_plus(self.usstype)+"&entry.455413428="+quote_plus(self.usslocal)+"&entry.790504343="+quote_plus(self.threat)+"&submit=Submit"
            #print url
            Reporter(url).start()
        self.uss=False
            
            
        

            
def dateDiffMinutes(s1,s2):
    format="%Y/%m/%d %H:%M:%S"
    d1=datetime.datetime.strptime(s1,format) 
    d2=datetime.datetime.strptime(s2,format)
    
    return (d2-d1).days *24 *60
        
def debug(value,level=None):
    if config.getint("uss_debug") >0:
        print "["+myPlugin+"] "+str(value)
        


def getDistance(x1,y1,z1,x2,y2,z2):
    return round(sqrt(pow(float(x2)-float(x1),2)+pow(float(y2)-float(y1),2)+pow(float(z2)-float(z1),2)),2)
    
    
def plugin_dir():
    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.kernel32.GetEnvironmentVariableW(u"USERPROFILE", buf, 1024)
    home_dir = buf.value
    plugin_base = os.path.basename(os.path.dirname(__file__))
    return home_dir+'\\AppData\\Local\\EDMarketConnector\\plugins\\'+plugin_base
        

def setSystem(system,x,y,z):
    this.systemCache[system]=(x,y,z)
    
def edsmGetSystem(system):
    debug(this.systemCache)
    if this.systemCache.has_key(system):
        debug("using system cache")
        return this.systemCache[system]
        
    else:
        url = 'https://www.edsm.net/api-v1/system?systemName='+quote_plus(system)+'&showCoordinates=1'      
        #print url
        r = requests.get(url)
        s =  r.json()
        #print s
        debug("populating cache")
        this.systemCache[system]=(s["coords"]["x"],s["coords"]["y"],s["coords"]["z"])
        return s["coords"]["x"],s["coords"]["y"],s["coords"]["z"]

def getDistanceMerope(x1,y1,z1):
    return round(sqrt(pow(float(-78.59375)-float(x1),2)+pow(float( -149.625)-float(y1),2)+pow(float(-340.53125)-float(z1),2)),2)        
    
def getDistanceSol(x1,y1,z1):
    return round(sqrt(pow(float(0)-float(x1),2)+pow(float(0)-float(y1),2)+pow(float(0)-float(z1),2)),2)         
        
def journal_entry(cmdr, is_beta, system, station, entry, state):

    startup_stats(cmdr)
    
    if ('Body' in entry):
            this.body_name = entry['Body']    
    
    if config.getint("Anonymous") >0:
        commander="Anonymous"
    else:
        commander=cmdr
        
        
    
    
    if system:
        x,y,z=edsmGetSystem(system)
    else:
        x=None
        y=None
        z=None    
    
    journal_entry_wrapper(commander, is_beta, system, station, entry, state,x,y,z,this.body_name,this.nearloc['Latitude'],this.nearloc['Longitude'],this.client_version)    
    
    
# Detect journal events
def journal_entry_wrapper(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):

    this.guid = uuid.uuid1()
    this.cmdr=cmdr
      
    statistics(cmdr, is_beta, system, station, entry, state)      
    faction_kill(cmdr, is_beta, system, station, entry, state)
    refugee_mission(cmdr, is_beta, system, station, entry, state)
    CodexEntry(cmdr, is_beta, system, station, entry, state)
    AXZone(cmdr, is_beta, system, station, entry, state)
    
    if entry['event'] == 'USSDrop':
        this.ussInator.ussDrop(cmdr, system, station, entry)
        this.canonnReport.ussDrop(cmdr, system, station, entry)
        
    if entry['event'] == 'FSSSignalDiscovered' and entry.get('USSType') == "$USS_Type_NonHuman;":       
        this.ussInator.FSSDetect(cmdr, system, station, entry)
        
        

        
        
    if entry['event'] == 'SupercruiseExit':
        # we need to check if we dropped from a uss
        this.ussInator.SupercruiseExit(cmdr, system, station, entry)        
        this.newsFeed.getPost()  
    
    if entry['event'] == 'StartJump':   
        this.newsFeed.getPost()  
        
    if entry['event'] == 'StartJump' and entry['JumpType'] == 'Hyperspace':
            
        debug("StartJump Hyperspace",2)
        debug(entry,2)
        
        this.hyperdictionInator.StartJump(cmdr, system, station, entry)
                        
                
    
    if entry['event'] == 'FSDJump':
        
        setSystem(entry["StarSystem"],entry["StarPos"][0],entry["StarPos"][1],entry["StarPos"][2])
        debug("FSDJump",2)
        debug(entry,2)
            
        this.ussInator.FSDJump(cmdr, system, station, entry)
        this.hyperdictionInator.FSDJump(cmdr, system, station, entry)   
        this.patrolZone.FSDJump(cmdr, system, station, entry)
        this.meropeLog.FSDJump(cmdr, system, station, entry)
    
    if entry['event'] == 'Location':
        this.patrolZone.Location(cmdr, system, station, entry)
        setSystem(system,entry["StarPos"][0],entry["StarPos"][1],entry["StarPos"][2])
        
    if entry['event'] == '1G':
        this.patrolZone.startUp(cmdr, system, station, entry)       


        

        
def matches(d, field, value):
    return field in d and value == d[field]     
        
def faction_kill(cmdr, is_beta, system, station, entry, state):
    if entry['event'] == "FactionKillBond":
        factionMatch=(matches(entry, 'VictimFaction', '$faction_Thargoid;') or matches(entry, 'VictimFaction', '$faction_Guardian;'))
        if factionMatch and 'Reward' in entry:
            url="https://docs.google.com/forms/d/e/1FAIpQLSevc8RrhOzOq9U0a2VC29N_lgjRfVU9vlF-oKdjhvZu6YnLvw/formResponse?usp=pp_url"
            url+="&entry.567957318="+quote_plus(cmdr);
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

        url+="&entry.1415400073="+quote_plus(cmdr);
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
       
        
        url+="&entry.1257612503="+quote_plus(cmdr);
        url+="&entry.1541680555="+quote_plus(system)
        url+="&entry.484596368="+str(x)
        url+="&entry.1443755704="+str(y)
        url+="&entry.1285491432="+str(z)
        url+="&entry.837147926="+str(entry.get("SystemAddress"))
        
        Reporter(url).start()        

            

## I want to avoid sending this event if there has not been any change
## so we will have a global dict

# this.tg_stats = {
    # "tg_encounter_wakes": 0,
    # "tg_encounter_imprint": 0,
    # "tg_encounter_total": 0,
    # "tg_timestamp": 'x',
    # "tg_scout_count": 0,
    # "tg_last_system": "x"
# }

        
        
def statistics(cmdr, is_beta, system, station, entry, state):
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
        if new_tg_stats == this.tg_stats:
            debug("TG Stats unchanged",2)
        else:
            debug("TG Stats changed",2)
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
            
        
        
        
        
 
    