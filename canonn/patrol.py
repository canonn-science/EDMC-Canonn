"""
Patrols
"""

import Tkinter as tk
from Tkinter import Frame
import uuid
from ttkHyperlinkLabel import HyperlinkLabel
import requests
import json
import re
import myNotebook as nb
from config import config
import threading
from systems import Systems
import math
from debug import Debug
from debug import debug,error





CYCLE=60 * 1000 * 60 # 60 minutes
DEFAULT_URL = ""
WRAP_LENGTH = 200

def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id

class UpdateThread(threading.Thread):
    def __init__(self,widget):
        threading.Thread.__init__(self)
        self.widget=widget
    
    def run(self):
        # download cannot contain any tkinter changes
        self.widget.download()
        # update can't be inside a thread
        self.widget.after(500,self.widget.update) 

def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)

class PatrolLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching Patrol...",
            url=DEFAULT_URL,
            popup_copy = True,
            #wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        #self.bind('<Configure>', self.__configure_event)
 
    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)
    
class InfoLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching Patrol...",
            url=DEFAULT_URL,
            popup_copy = True,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.bind('<Configure>', self.__configure_event)
 
    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)    
    
class CanonnPatrol(Frame):

    def __init__(self, parent,gridrow):
        "Initialise the ``Patrol``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
                        
        self.canonn=tk.IntVar(value=config.getint("HideCanonn"))
        self.faction=tk.IntVar(value=config.getint("HideFaction"))              
        
        
        self.columnconfigure(1, weight=1)
        self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        
        self.label=tk.Label(self, text=  "Patrol:")         
        self.label.grid(row = 0, column = 0, sticky=sticky)
        
        self.hyperlink=PatrolLink(self)
        self.hyperlink.grid(row = 0, column = 1,sticky="NSEW")
        self.distance=tk.Label(self, text=  "...")         
        self.distance.grid(row = 0, column = 2,sticky="NSEW")
        self.distance.grid_remove()
        
        self.infolink=InfoLink(self)
        self.infolink.grid(row = 1, column = 0,sticky="NSEW",columnspan=3)
        self.infolink.grid_remove()
        
        self.patrol_list=[]
        
        self.patrol_count=0
        self.patrol_pos=0
        self.minutes=0
        self.visible()
        
        
        self.system=""
        # 
        self.after(250, self.patrol_update)
        
    def patrol_update(self):
        UpdateThread(self).start()
        self.after(CYCLE, self.patrol_update)

    def update(self):
        if self.visible():
            if self.patrol_list and self.system:
                p=Systems.edsmGetSystem(self.system)
                self.nearest=self.getNearest(p)
                self.hyperlink['text']=self.nearest.get("system")
                self.hyperlink['url']=self.nearest.get("url")
                self.distance['text']="{}ly".format(round(getDistance(p,self.nearest.get("coords")),2))
                self.infolink['text']=self.nearest.get("instructions")
                self.infolink['url']=self.nearest.get("url")
                self.infolink.grid()
                self.distance.grid()
            else:
                self.hyperlink['text'] = "Fetching patrols"
                self.infolink.grid_remove()
                self.distance.grid_remove()
        
    def getStates(self,state_name,bgs):
        sa=[]
        active_states=bgs.get(state_name)
        if active_states:
            sa=active_states[0].values()
        
        if sa:
            states=","
            states=states.join(sa)
            return states
        else:
            return None
            
                
    def getBGSInstructions(self,bgs):
        target=0.50 <= float(bgs.get("influence")) <= 0.65
        over=float(bgs.get("influence"))>0.65
        under=float(bgs.get("influence"))<0.50
        
        if  self.getStates("active_states",bgs):       
            states=" States: {}".format(self.getStates("active_states",bgs))
        else:
            states=""
        
        # if  self.getStates("pending_states",bgs):       
            # pstates=" Pending: {}".format(self.getStates("pending_states",bgs))
        # else:
            # pstates=""
        
        debug(bgs)
        if target:
            return "Canonn Influence {}%{}".format(round(float(bgs.get("influence")*100),2),states)
        if  over:
            return  "Canonn Influence {}%{} Check #mission_minor_faction on discord for instructions.".format(round(float(bgs.get("influence")*100),2),states)
        if under:
            return "Canonn Influence {}%{} Please complete missions for Canonn to increase our influence".format(round(float(bgs.get("influence")*100),2),states)
        
        
        
    
    def getBGSPatrol(self,bgs):
        
        
        x,y,z=Systems.edsmGetSystem(bgs.get("system_name"))
        r = {
            "type": "BGS",
            "system": bgs.get("system_name"),
            "coords": (x,y,z),
            "instructions": self.getBGSInstructions(bgs),
            "url":  "https://elitebgs.app/system/{}".format(bgs.get("system_id"))
        }
        return r
                
    def getFactionData(self,faction):
        '''
           We will get Canonn faction data using an undocumented elitebgs api
           NB: It is possible this could get broken so need to contact CMDR Garud 
        '''
        
        patrol=[]
        
        url="https://elitebgs.app/frontend/factions?name={}".format(faction)
        j = requests.get(url).json()
        if j:
            for bgs in j.get("docs")[0].get("faction_presence"):
                
                patrol.append(self.getBGSPatrol(bgs))
        
        
        return patrol
        
    def download(self):
        "Update the patrol."
        
        patrol_list=[]
        patrol_list.extend(self.getFactionData("Canonn"))
        patrol_list.extend(self.getFactionData("Canonn Deep Space Research"))
        
        self.patrol_list=patrol_list
       
    
    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.canonn=tk.IntVar(value=config.getint("HideCanonn"))
        self.faction=tk.IntVar(value=config.getint("HideFaction"))
        
        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row = 0, column = 0,sticky="NSEW")
        
        nb.Checkbutton(frame, text="Hide Canonn Patrols", variable=self.canonn).grid(row = 0, column = 0,sticky="NW")
        nb.Checkbutton(frame, text="Hide Canonn Faction Systems", variable=self.faction).grid(row = 0, column = 2,sticky="NW")
        
        return frame

    def visible(self):
        
        nopatrols=self.canonn.get() == 1 and self.faction.get() ==1
        
        if nopatrols:
            self.grid_remove()
            self.isvisible=False;
            return False
        else:
            self.grid()
            self.isvisible=True;
            return True        
            
    def getNearest(self,location):
        nearest=""
        for patrol in self.patrol_list:
            if nearest != "":           
                
                if getDistance(location,patrol.get("coords")) < getDistance(location,nearest.get("coords")): 
                    nearest=patrol
            else:        
                
                nearest=patrol
            
        return nearest
            
            
    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('HideCanonn', self.canonn.get())      
        config.set('HideFaction', self.faction.get())      
        if self.visible():
            self.patrol_update()
        
    def journal_entry(self,cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):
        # We don't care what the journal entry is as long as the system has changed.
        
        
        if self.system != system:
            debug("Refresshing Patrol")
            self.system=system
            # self.nearest=self.getNearest((x,y,z))
            # self.hyperlink['text']=self.nearest.get("system")
            # self.hyperlink['url']=self.nearest.get("url")
            # self.distance['text']="{}ly".format(round(getDistance((x,y,z),self.nearest.get("coords")),2))
            # self.infolink['text']=self.nearest.get("instructions")
            # self.infolink['url']=self.nearest.get("url")
            # self.infolink.grid()
            self.update()
        else:
            error("nope {}".format(entry.get("event")))
            error(system)
            error(self.system)
            
            
def getDistance(p,g):
    # gets the distance between two systems
    return math.sqrt(sum(tuple([math.pow(p[i]-g[i],2)  for i in range(3)])))
   
