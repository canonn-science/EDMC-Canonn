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
from systems import edsmGetSystem

REFRESH_CYCLES = 60 ## how many cycles before we refresh
CYCLE=60 * 1000 # 60 seconds
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
        # trigger a tkinter update after 1 second
        self.widget.after(1000,self.widget.update) 

def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)

class PatrolLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching Patrol...",
            url=DEFAULT_URL,
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
        
        self.patrol_count=0
        self.patrol_pos=0
        self.minutes=0
        self.visible()
        self.download()
        
    
        # 
        #self.after(250, self.patrol_update)
        
    def patrol_update(self):
        UpdateThread(self).start()

    def update(self):
        if self.visible():
            if self.patrol_data:
                # patrol=self.patrol_data[self.patrol_pos]
                # self.hyperlink['url'] = patrol['link']
                # self.hyperlink['text'] = decode_unicode_references(patrol['title']['rendered'])
                print("errm")
            else:
                self.hyperlink['text'] = "Patrol refresh failed"
                
    def getFactionData(self,faction):
        '''
           We will get Canonn faction data using an undocumented elitebgs api
           NB: It is possible this could get broken so need to contact CMDR Garud 
        '''
        url="https://elitebgs.app/frontend/factions?name={}".format(faction)
        j = requests.get(url).json()
        if j:
            for s in j.get("docs")[0].get("faction_presence"):
                print(s.get("system_name"))
                edsmGetSystem(s.get("system_name"))
                
        
    def download(self):
        "Update the patrol."
        
        self.getFactionData("Canonn")
        self.getFactionData("Canonn Deep Space Research")
        
        #refesh every 60 seconds
        # self.after(PATROL_CYCLE, self.patrol_update)
        # if self.isvisible:
        
            # if self.patrol_count == self.patrol_pos:           
                # self.patrol_pos=0
            # else:
                # self.patrol_pos+=1
            
            # if self.minutes==0:
                # self.patrol_data = requests.get("https://canonn.science/wp-json/wp/v2/posts").json()
                # self.patrol_count=len(self.patrol_data)-1
                # self.patrol_pos=0
                # self.minutes=REFRESH_CYCLES
            # else:
                # self.minutes+=-1        

    
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
            
    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('HideCanonn', self.canonn.get())      
        config.set('HideFaction', self.faction.get())      
        if self.visible():
            self.patrol_update()
        
        
        
   
