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

REFRESH_CYCLES = 60 ## how many cycles before we refresh
NEWS_CYCLE=60 * 1000 # 10 seconds
DEFAULT_NEWS_URL = 'https://canonn.science/wp-json/wp/v2/posts'
WRAP_LENGTH = 200

def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id


def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)

class NewsLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching...",
            url=DEFAULT_NEWS_URL,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.bind('<Configure>', self.__configure_event)
 
    def __configure_event(self, event):
        "Handle resizing."

        self.configure(wraplength=event.width)
    
class CanonnNews(Frame):

    def __init__(self, parent):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW        
        
        Frame.__init__(
            self,
            parent
        )
                        
        self.columnconfigure(1, weight=1)
        self.grid(row = 0, column = 0, sticky="NSEW",columnspan=2)
        
        self.label=tk.Label(self, text=  "Canonn:")
        self.label.grid(row = 0, column = 0, sticky=sticky)
        
        self.hyperlink=NewsLink(self)
        self.hyperlink.grid(row = 0, column = 1,sticky="NSEW")
        
        self.news_count=0
        self.news_pos=0
        self.minutes=0
        #self.hyperlink.bind('<Configure>', self.hyperlink.configure_event)
        self.after(250, self.news_update)

    def news_update(self):
        "Update the news."
        
        #refesh every 60 seconds
        self.after(NEWS_CYCLE, self.news_update)
        

        
        if self.news_count == self.news_pos:           
            self.news_pos=0
        else:
            print("decrementing news")
            self.news_pos+=1
        
        if self.minutes==0:
            self.news_data = requests.get("https://canonn.science/wp-json/wp/v2/posts").json()
            self.news_count=len(self.news_data)-1
            self.news_pos=0
            self.minutes=REFRESH_CYCLES
        else:
            self.minutes+=-1        
                
        if self.news_data:
            news=self.news_data[self.news_pos]
            self.hyperlink['url'] = news['link']
            self.hyperlink['text'] = decode_unicode_references(news['title']['rendered'])

        else:
            self.hyperlink['text'] = "News refresh failed"

    
    
   
