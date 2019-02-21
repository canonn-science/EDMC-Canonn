"""
Module to provide the news.
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


NEWS_CYCLE=60 * 1000 # 1 minute
DEFAULT_URL = 'https://github.com/canonn-science/EDMC-Canonn/releases'
WRAP_LENGTH = 200

def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id


def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)

class ReleaseLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching...",
            url=DEFAULT_URL,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.bind('<Configure>', self.__configure_event)
 
    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)
    
class Release(Frame):

    def __init__(self, parent,release,gridrow):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
                        
        self.hidden=tk.IntVar(value=config.getint("AutoUpdate"))                
        
        
        self.columnconfigure(1, weight=1)
        self.grid(row = gridrow, column = 0, sticky="NSEW",columnspan=2)
        
        self.label=tk.Label(self, text=  "Release:")
        self.label.grid(row = 0, column = 0, sticky=sticky)
        
        self.hyperlink=ReleaseLink(self)
        self.hyperlink.grid(row = 0, column = 1,sticky="NSEW")
        
        self.release=release
        self.news_count=0
        self.news_pos=0
        self.minutes=0
        self.visible()
        #self.hyperlink.bind('<Configure>', self.hyperlink.configure_event)
        self.after(250, self.news_update)
        
    def version2number(self,version):
        major,minor,patch=version.split('.')
        return (int(major)*1000000)+(int(minor)*1000)+int(patch)

    def news_update(self):
        "Update the news."
        
        #refesh every 60 seconds
        self.after(NEWS_CYCLE, self.news_update)
        
        
        
        self.latest=requests.get("https://api.github.com/repos/canonn-science/EDMC-Canonn/releases/latest").json()
        
        current=self.version2number(self.release)
        release=self.version2number(self.latest.get("tag_name"))
        
        print(current)
        print(release)
        
        self.hyperlink['url'] = self.latest.get("html_url")
        self.hyperlink['text'] = self.latest.get("tag_name")

        if current==release:
            self.grid_remove()
        elif current > release:
            self.hyperlink['text'] = "Experimental Release {}".format(self.release)
            self.grid()
        else:
            self.hyperlink['text'] = "Please Upgrade {}".format(self.latest.get("tag_name"))
            self.grid()            
    
    def plugin_prefs(self, parent, cmdr, is_beta,gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.hidden=tk.IntVar(value=config.getint("AutoUpdate"))
        
        #frame = nb.Frame(parent)
        #frame.columnconfigure(1, weight=1)
        return nb.Checkbutton(parent, text="Auto Update THis Plugin", variable=self.hidden).grid(row = gridrow, column = 0,sticky="NSEW")
        
        #return frame

    def visible(self):
        if self.hidden.get() == 1:
            self.grid_remove()
            return False
        else:
            self.grid()
            return True

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('AutoUpdate', self.hidden.get())      
        if self.visible():
            self.news_update()
        print("Hidden {}".format(self.hidden.get()))
        
        
   
