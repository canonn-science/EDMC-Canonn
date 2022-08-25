import plug
import re
import tkinter as tk
from tkinter import Frame
from ttkHyperlinkLabel import HyperlinkLabel

from canonn.debug import Debug
from canonn.helper import objdict
from theme import theme


class Display():

    def __init__(self, parent, gridrow):
        padx, pady = 10, 5  # formatting

        self.gridrow = gridrow
        self.parent = parent

        # we will create and destoy our UI
        self.hidden = True

    def hide(self):

        if not self.hidden:
            self.hidden = True
            self.label.destroy()
            self.frame.destroy()

    def show(self):

        # only do this if the frame does not exist
        if self.hidden:
            self.hidden = False
            self.frame = Frame(self.parent)
            theme.update(self.frame)
            self.frame.columnconfigure(1, weight=1)
            self.frame.grid(row=self.gridrow, column=0,
                            columnspan=2)
            self.label = HyperlinkLabel(self.frame)
            self.label.grid(row=0, column=0)

            siteid = re.search(r'\$Ancient:#index=(.+);',
                               self.entry.Name).group(1)

            theme.update(self.label)
            self.label["text"] = "Click here to report ruin layout"
            self.label.url = f"https://docs.google.com/forms/d/e/1FAIpQLSfS2GwRdzqYfxbSrjU7hgJckDNJbHISgiHp1gWFEHXkrTmhXw/viewform?usp=pp_url&entry.2021507511={self.cmdr}&entry.1090208472={self.system}&entry.2118720333={self.entry.BodyName}&entry.865635247={siteid}"

    def journal_entry(self, cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, journal,
                      state, x, y, z, body, nearloc, client):

        entry = objdict(journal)

        ruins = (
            entry.event == "ApproachSettlement" and
            entry.Name and
            "$Ancient:#index" in entry.Name
        )

        if ruins:
            self.entry = entry
            self.cmdr = cmdr
            self.system = system
            self.show()

        reset = (entry.event in ("StartJump", "FSDJump"))

        if reset:
            self.hide()
