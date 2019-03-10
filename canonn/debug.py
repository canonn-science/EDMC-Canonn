import Tkinter as tk
from Tkinter import Frame
import myNotebook as nb
from config import config
import datetime 

class Debug:
        
    debugvar=tk.IntVar(value=config.getint("CanonnDebug"))
    client="Canonn"
    
    @classmethod
    def setClient(cls,client):
        Debug.client=client
            
    @classmethod
    def p(cls,value):
        print("{} [{}] {}".format(datetime.datetime.now(),Debug.client,str(value)))
            
    @classmethod
    def debug(cls,value):
        
        if cls.debugvar.get() == 1:
            cls.p(value)

        
    @classmethod
    def plugin_prefs(cls, parent,client,gridrow):
        "Called to get a tk Frame for the settings dialog."

        cls.debugvar=tk.IntVar(value=config.getint("CanonnDebug"))
        Debug.client=client
        
        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        frame.grid(row = 0, column = 0,sticky="NSEW")
        
        nb.Checkbutton(frame, text="Turn on Debugging", variable=cls.debugvar).grid(row = 0, column = 0,sticky="NW")
        
        return frame
        
    @classmethod    
    def prefs_changed(cls):
        "Called when the user clicks OK on the settings dialog."
        config.set('CanonnDebug', cls.debugvar.get())      
        
def debug(value):
    Debug.debug(value)
    
def error(value):
    Debug.p(value)    