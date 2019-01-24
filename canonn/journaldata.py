import threading
import requests
import sys
import json


'''
Added the above events to: https://api.canonn.tech:2053/excludeevents
-DM
'''

class CanonnJournal(threading.Thread):
    '''
        Should probably make this a heritable class as this is a repeating pattern
    '''
    
    exclusions={}
    
    def __init__(self,cmdr, is_beta, system, station, entry,client):
        threading.Thread.__init__(self)
        self.system = system
        self.cmdr = cmdr
        self.station = station
        self.is_beta = is_beta
        self.entry = entry.copy()
        self.client = client

    def run(self):
    
        if not CanonnJournal.exclusions:
            r=requests.get("https://api.canonn.tech:2053/excludeevents")  
            if r.status_code == requests.codes.ok:
                for exc in r.json():
                    CanonnJournal.exclusions[exc["eventName"]]=True
                print CanonnJournal.exclusions
    
            
        payload={}
        payload["systemName"]=self.system
        payload["cmdrName"]=self.cmdr  
        payload["rawJson"]=self.entry
        payload["eventName"]=self.entry["event"]
        payload["clientVersion"]= self.client
        payload["isBeta"]= self.is_beta
        
        included_event = not CanonnJournal.exclusions.get(self.entry.get("event"))
        
        if included_event:
                    
                r=requests.post("https://api.canonn.tech:2053/eventreports",data=json.dumps(payload),headers={"content-type":"application/json"})  
                if not r.status_code == requests.codes.ok:
                    print r.status_code
                    print r.json()
                    print json.dumps(payload)
                    
        else:
            print("excluding {}".format(self.entry.get("event")))

'''
    from canonn import journaldata
    journaldata.submit(cmdr, system, station, entry)
'''
def submit(cmdr, is_beta, system, station, entry,client):
    CanonnJournal(cmdr, is_beta, system, station, entry,client).start()   