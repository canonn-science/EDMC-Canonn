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

ship_types={   
        'adder': 'Adder',
        'typex_3': 'Alliance Challenger',
        'typex': 'Alliance Chieftain',
        'typex_2': 'Alliance Crusader',
        'anaconda': 'Anaconda',
        'asp explorer': 'Asp Explorer',
        'asp': 'Asp Explorer',
        'asp scout': 'Asp Scout',
        'asp_scout': 'Asp Scout',
        'beluga liner': 'Beluga Liner',
        'belugaliner': 'Beluga Liner',
        'cobra mk. iii': 'Cobra MkIII',
        'cobramkiii':  'Cobra MkIII',
        'cobra mk. iv': 'Cobra MkIV',
        'cobramkiv': 'Cobra MkIV',
        'diamondback explorer': 'Diamondback Explorer',
        'diamondbackxl': 'Diamondback Explorer',
        'diamondback scout': 'Diamondback Scout',
        'diamondback': 'Diamondback Scout',
        'dolphin': 'Dolphin',
        'eagle': 'Eagle',
        'federal assault ship': 'Federal Assault Ship',
        'federation_dropship_mkii': 'Federal Assault Ship',       
        'federal corvette': 'Federal Corvette',
        'federation_corvette': 'Federal Corvette',
        'federal dropship': 'Federal Dropship',
        'federation_dropship': 'Federal Dropship',
        'federal gunship': 'Federal Gunship',
        'federation_gunship': 'Federal Gunship',
        'fer-de-lance': 'Fer-de-Lance',
        'ferdelance': 'Fer-de-Lance',
        'hauler': 'Hauler',
        'imperial clipper': 'Imperial Clipper',
        'empire_trader': 'Imperial Clipper',
        'imperial courier': 'Imperial Courier',
        'empire_courier': 'Imperial Courier',
        'imperial cutter': 'Imperial Cutter',
        'cutter': 'Imperial Cutter',
        'imperial eagle': 'Imperial Eagle',
        'empire_eagle': 'Imperial Eagle',
        'keelback': 'Keelback',
        'independant_trader': 'Keelback',
        'krait_mkii': 'Krait MkII',
        'krait_light': 'Krait Phantom',
        'mamba': 'Mamba',
        'orca': 'Orca',
        'python': 'Python',
        'sidewinder': 'Sidewinder',
        'type 6 transporter': 'Type-6 Transporter',
        'type6': 'Type-6 Transporter',
        'type 7 transporter': 'Type-7 Transporter',
        'type7':'Type-7 Transporter',
        'type 9 heavy': 'Type-9 Heavy',
        'type9': 'Type-9 Heavy',
        'type 10 defender': 'Type-10 Defender',
        'type9_military': 'Type-10 Defender',
        'viper mk. iii': 'Viper MkIII',
        'viper': 'Viper MkIII',
        'viper mk. iv': 'Viper MkIV',
        'viper_mkiv': 'Viper MkIV',
        'vulture': 'Vulture'
}

def getShipType(key):
    name=ship_types.get(key.lower())
    if name:
        return name
    else:
        return key

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
        self.ships=[]
        
        self.canonn=tk.IntVar(value=config.getint("HideCanonn"))
        self.faction=tk.IntVar(value=config.getint("HideFaction"))              
        self.hideships=tk.IntVar(value=config.getint("HideShips"))              
        
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
                if self.system:
                    self.hyperlink['text'] = "Fetching patrols..."
                else:
                    self.hyperlink['text'] = "Waiting for location"
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
        
        #debug(bgs)
        if target:
            return "Canonn Influence {}%{}".format(round(float(bgs.get("influence")*100),2),states)
        if  over:
            return  "Canonn Influence {}%{} Check #mission_minor_faction on discord for instructions.".format(round(float(bgs.get("influence")*100),2),states)
        if under:
            return "Canonn Influence {}%{} Please complete missions for Canonn to increase our influence".format(round(float(bgs.get("influence")*100),2),states)
        
        
    
    
    def getBGSPatrol(self,bgs):
        x,y,z=Systems.edsmGetSystem(bgs.get("system_name"))
        return newPatrol("BGS",bgs.get("system_name"),(x,y,z),self.getBGSInstructions(bgs),"https://elitebgs.app/system/{}".format(bgs.get("system_id")))
            
        
                
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
        debug("Download Patrol Data")
        
        patrol_list=[]
        if self.faction.get() != 1:
            debug("Getting Faction Data")
            patrol_list.extend(self.getFactionData("Canonn"))
            patrol_list.extend(self.getFactionData("Canonn Deep Space Research"))
            
        if self.ships and self.hideships.get() != 1:
            patrol_list.extend(self.ships)

        self.patrol_list=patrol_list
       
    
    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):
        "Called to get a tk Frame for the settings dialog."
        
        self.canonn=tk.IntVar(value=config.getint("HideCanonn"))
        self.faction=tk.IntVar(value=config.getint("HideFaction"))
        self.hideships=tk.IntVar(value=config.getint("HideShips"))
        
        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row = gridrow, column = 0,sticky="NSEW")
        
        nb.Checkbutton(frame, text="Hide Canonn Patrols", variable=self.canonn).grid(row = 0, column = 0,sticky="NW")
        nb.Checkbutton(frame, text="Hide Canonn Faction Systems", variable=self.faction).grid(row = 0, column = 2,sticky="NW")
        nb.Checkbutton(frame, text="Hide Your Ships", variable=self.hideships).grid(row = 0, column = 3,sticky="NW")
        
        return frame

    def visible(self):
        
        nopatrols=self.canonn.get() == 1 and self.faction.get() ==1 and self.hideships.get() ==1
        
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
        config.set('HideShips', self.hideships.get())      
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

    def cmdr_data(self,data, is_beta):
        """
        We have new data on our commander
        
        Lets get a list of ships
        """
        self.ships=[]
        self.system=data.get("lastSystem").get("name")
        
        current_ship=data.get("commander").get("currentShipId")
        
        for ship in data.get("ships").keys():
            debug(ship)
            debug(current_ship)
            if int(ship) != int(current_ship):
                ship_system=data.get("ships").get(ship).get("starsystem").get("name")
                ship_pos=Systems.edsmGetSystem(ship_system)
                ship_type=getShipType(data.get("ships").get(ship).get("name"))
                ship_name=data.get("ships").get(ship).get("shipName")
                ship_station=data.get("ships").get(ship).get("station").get("name")
                ship_info="Your {}, {} is docked at {}".format(ship_type,ship_name,ship_station)
                self.ships.append(newPatrol("SHIPS",ship_system,ship_pos,ship_info,None))
                debug(json.dumps(data.get("ships").get(ship),indent=4))
        UpdateThread(self).start()
        debug(json.dumps(data,indent=4))
            
def getDistance(p,g):
    # gets the distance between two systems
    return math.sqrt(sum(tuple([math.pow(p[i]-g[i],2)  for i in range(3)])))
   
def newPatrol(type,system,coords,instructions,url):
    return {
        "type": type,
        "system": system,
        "coords": coords,
        "instructions": instructions,
        "url":  url
    }