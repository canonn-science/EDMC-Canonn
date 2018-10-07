from config import config
import myNotebook as nb

from canonn import journaldata
from canonn import factionkill

import ttk
import Tkinter as tk
import sys
    
this = sys.modules[__name__]
    
def plugin_prefs(parent, cmdr, is_beta):
    """
    Return a TK Frame for adding to the EDMC settings dialog.
    """
    this.anon = tk.IntVar(value=config.getint("Anonymous")) # Retrieve saved value from config
    frame = nb.Frame(parent)
    frame.columnconfigure(3, weight=1)
    nb.Checkbutton(frame, text="I want to be anonymous", variable=this.anon).grid(row = 1, column = 0,sticky=tk.W)

    
def prefs_changed(cmdr, is_beta):
    """
    Save settings.
    """
    config.set('Anonymous', this.anon.get())       
   
def plugin_start():
    """
    Load Template plugin into EDMC
    """
    
    #print this.patrol
    return 'Canonn'
    
def plugin_app(parent):

    this.parent = parent
    #create a new frame as a containier for the status
    
    this.frame = tk.Frame(parent)    
   
def journal_entry(cmdr, is_beta, system, station, entry, state):
    '''
    Commanders may want to be anonymous so we we have a journal entry anonymiser
    that passes the journale entry to the one that does all the real work
    '''
    # capture some stats when we launch not read for that yet
    # startup_stats(cmdr)

    if config.getint("Anonymous") >0:
        commander="Anonymous"
        if cmdr in str(entry):
            #entry["cmdrName"]="Anonymous"
            s = str(entry).replace(cmdr,"Anonymous")
            entry=eval(s)
    else:
        commander=cmdr
       
    # 
    return journal_entry_wrapper(commander, is_beta, system, station, entry, state)
    
# Detect journal events
def journal_entry_wrapper(cmdr, is_beta, system, station, entry, state):
    journaldata.submit(cmdr, is_beta, system, station, entry)
    factionkill.submit(cmdr, is_beta, system, station, entry)
    