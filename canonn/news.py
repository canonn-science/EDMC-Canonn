"""
Module to provide the news.
"""
try:
    import tkinter as tk
    from tkinter import Frame
except:
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
from canonn.debug import Debug
from canonn.debug import debug, error
import html


REFRESH_CYCLES = 60  # how many cycles before we refresh
NEWS_CYCLE = 60 * 1000  # 60 seconds
DEFAULT_NEWS_URL = 'https://canonn.science/wp-json/wp/v2/posts'
WRAP_LENGTH = 200


def _callback(matches):
    id = matches.group(1)
    try:
        return unichr(int(id))
    except:
        return id


class UpdateThread(threading.Thread):
    def __init__(self, widget):
        threading.Thread.__init__(self)
        self.widget = widget

    def run(self):
        Debug.logger.debug("News: UpdateThread")
        # download cannot contain any tkinter changes
        self.widget.download()


def decode_unicode_references(data):
    return re.sub("&#(\d+)(;|(?=\s))", _callback, data)


class NewsLink(HyperlinkLabel):

    def __init__(self, parent):

        HyperlinkLabel.__init__(
            self,
            parent,
            text="Fetching News...",
            url=DEFAULT_NEWS_URL,
            wraplength=50,  # updated in __configure_event below
            anchor=tk.NW
        )
        self.resized = False
        self.bind('<Configure>', self.__configure_event)

    def __reset(self):
        self.resized = False

    def __configure_event(self, event):
        "Handle resizing."

        if not self.resized:
            Debug.logger.debug("News widget resize")
            self.resized = True
            self.configure(wraplength=event.width)
            self.after(500, self.__reset)


class CanonnNews(Frame):

    def __init__(self, parent, gridrow):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        Frame.__init__(
            self,
            parent
        )

        self.hidden = tk.IntVar(value=config.get_int("HideNews"))

        self.news_data = []
        self.columnconfigure(1, weight=1)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        self.label = tk.Label(self, text="Canonn:")
        self.label.grid(row=0, column=0, sticky=sticky)
        self.label.bind("<Button-1>", self.click_news)

        self.hyperlink = NewsLink(self)
        self.hyperlink.grid(row=0, column=1, sticky="NSEW")

        self.news_count = 0
        self.news_pos = 0
        self.minutes = 0
        self.visible()
        #self.hyperlink.bind('<Configure>', self.hyperlink.configure_event)
        self.after(250, self.news_update)
        self.bind('<<NewsData>>', self.eupdate)

    def news_update(self):

        if self.isvisible:

            if self.news_count == self.news_pos:
                self.news_pos = 0
            else:
                self.news_pos += 1

            if self.minutes == 0:
                UpdateThread(self).start()
            else:
                self.minutes += -1

        self.update()
        # refesh every 60 seconds
        Debug.logger.debug("Refreshing News")
        self.after(NEWS_CYCLE, self.news_update)

    def eupdate(self, event):
        self.update()

    def update(self):
        if self.visible():
            if self.news_data:
                news = self.news_data[self.news_pos]
                self.hyperlink['url'] = news['link']
                self.hyperlink['text'] = html.unescape(
                    news['title']['rendered'])
            else:
                Debug.logger.debug("News download not complete")

    def click_news(self, event):
        if self.news_count == self.news_pos:
            self.news_pos = 0
        else:
            self.news_pos += 1

        self.update()

    def download(self):
        "Update the news."

        if self.isvisible:

            Debug.logger.debug("Fetching News")
            r = requests.get("https://canonn.science/wp-json/wp/v2/posts")
            r.encoding = 'utf-8'
            self.news_data = r.json()

            self.news_count = len(self.news_data)-1
            self.news_pos = 0
            self.minutes = REFRESH_CYCLES
            if not config.shutting_down:
                self.event_generate('<<NewsData>>', when='tail')

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.hidden = tk.IntVar(value=config.get_int("HideNews"))

        #frame = nb.Frame(parent)
        #frame.columnconfigure(1, weight=1)
        return nb.Checkbutton(parent, text="Hide Canonn News", variable=self.hidden).grid(row=gridrow, column=0, sticky="NSEW")

        # return frame

    def visible(self):
        if self.hidden.get() == 1:
            self.grid()
            self.grid_remove()
            self.isvisible = False
            return False
        else:
            self.grid()
            self.isvisible = True
            return True

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('HideNews', self.hidden.get())
        if self.visible():
            self.news_update()
