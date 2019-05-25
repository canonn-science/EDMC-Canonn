from config import config
import myNotebook as nb
from urllib import quote_plus
import requests
import json

from canonn import journaldata
from canonn import factionkill
from canonn import nhss
from canonn import codex
from canonn import hdreport
from canonn import news
from canonn import release
from canonn import legacy
from canonn import clientreport
from canonn import fssreports
from canonn import patrol
from canonn.systems import Systems
from canonn.debug import Debug
from canonn.debug import debug
from canonn.whitelist import whiteList

from canonn import  materialReport



import ttk
import Tkinter as tk
import sys
    
this = sys.modules[__name__]

this.nearloc = {
   'Latitude' : None,
   'Longitude' : None,
   'Altitude' : None,
   'Heading' : None,
   'Time' : None
}


myPlugin = "EDMC-Canonn"


this.version="2.2.0"
this.client_version="{}.{}".format(myPlugin,this.version)
this.body_name=None
    
def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)
    
    this.news.plugin_prefs(frame, cmdr, is_beta,1)
    this.release.plugin_prefs(frame, cmdr, is_beta,2)
    this.patrol.plugin_prefs(frame, cmdr, is_beta,3)
    Debug.plugin_prefs(frame,this.client_version,4)
    this.codexcontrol.plugin_prefs(frame, cmdr, is_beta,5)
    hdreport.HDInspector(frame,cmdr, is_beta,this.client_version,6)
    
    
    
    return frame

    
def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    this.news.prefs_changed(cmdr, is_beta)
    this.release.prefs_changed(cmdr, is_beta)
    this.patrol.prefs_changed(cmdr, is_beta)
    this.codexcontrol.prefs_changed(cmdr, is_beta)
    Debug.prefs_changed()
    
   
def plugin_start(plugin_dir):
    """
    Load Template plugin into EDMC
    """
    
    #print this.patrol
    release.Release.plugin_start(plugin_dir)
    Debug.setClient(this.client_version)
    patrol.CanonnPatrol.plugin_start(plugin_dir)
    codex.CodexTypes.plugin_start(plugin_dir)
    
    
    
    
    return 'Canonn'
    
def plugin_stop():
    """
    EDMC is closing
    """
    debug("Stopping the plugin")
    this.patrol.plugin_stop()
    
def plugin_app(parent):

    this.parent = parent
    #create a new frame as a containier for the status
    padx, pady = 10, 5  # formatting
    sticky = tk.EW + tk.N  # full width, stuck to the top
    anchor = tk.NW

    frame = this.frame = tk.Frame(parent)
    frame.columnconfigure(0, weight=1)

    table = tk.Frame(frame)
    table.columnconfigure(1, weight=1)
    table.grid(sticky="NSEW")
    
    
    this.news = news.CanonnNews(table,0)
    this.release = release.Release(table,this.version,1)
    this.codexcontrol = codex.CodexTypes(table,2)
    this.patrol = patrol.CanonnPatrol(table,3)
    whitelist=whiteList(parent)
    whitelist.fetchData()
    
    
    
    
    return frame
    
   
def journal_entry(cmdr, is_beta, system, station, entry, state):
    '''
    
    '''
    # capture some stats when we launch not read for that yet
    # startup_stats(cmdr)

    if entry.get("event") == "FSDJump":
        Systems.storeSystem(system,entry.get("StarPos"))
        
    if ('Body' in entry):
            this.body_name = entry['Body']        
        
    if system:
        x,y,z=Systems.edsmGetSystem(system)
    else:
        x=None
        y=None
        z=None    
    
    return journal_entry_wrapper(cmdr, is_beta, system, station, entry, state,x,y,z,this.body_name,this.nearloc['Latitude'],this.nearloc['Longitude'],this.client_version)    
    
# Detect journal events
def journal_entry_wrapper(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client):
    factionkill.submit(cmdr, is_beta, system, station, entry,client)
    nhss.submit(cmdr, is_beta, system, station, entry,client)
    hdreport.submit(cmdr, is_beta, system, station, entry,client)
    codex.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    fssreports.submit(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    journaldata.submit(cmdr, is_beta, system, station, entry,client)
    clientreport.submit(cmdr,is_beta,client,entry)
    this.patrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    this.codexcontrol.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    whiteList.journal_entry(cmdr, is_beta, system, station, entry, state,x,y,z,body,lat,lon,client)
    materialReport.submit (cmdr, is_beta, system, station, entry,client,lat,lon,body,state,x,y,z)
    
    # legacy logging to google sheets
    legacy.statistics(cmdr, is_beta, system, station, entry, state)
    legacy.CodexEntry(cmdr, is_beta, system, x,y,z, entry, body,lat,lon,client)
    legacy.AXZone(cmdr, is_beta, system,x,y,z, station, entry, state)
    legacy.faction_kill(cmdr, is_beta, system, station, entry, state)
    legacy.NHSS.submit(cmdr, is_beta, system,x,y,z, station, entry,client)
        
    
def dashboard_entry(cmdr, is_beta, entry):
      
    
    this.landed = entry['Flags'] & 1<<1 and True or False
    this.SCmode = entry['Flags'] & 1<<4 and True or False
    this.SRVmode = entry['Flags'] & 1<<26 and True or False
    this.landed = this.landed or this.SRVmode
      #print "LatLon = {}".format(entry['Flags'] & 1<<21 and True or False)
      #print entry
    if(entry['Flags'] & 1<<21 and True or False):
        if('Latitude' in entry):
            this.nearloc['Latitude'] = entry['Latitude']
            this.nearloc['Longitude'] = entry['Longitude']
    else:
        this.body_name = None
        this.nearloc['Latitude'] = None
        this.nearloc['Longitude'] = None    
    
def cmdr_data(data, is_beta):
    """
    We have new data on our commander
    """
    #debug(json.dumps(data,indent=4))
    this.patrol.cmdr_data(data, is_beta)
