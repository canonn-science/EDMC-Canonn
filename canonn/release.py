"""
Module for managing releases
"""

try:
    import tkinter as tk
    from tkinter import Frame
    from io import BytesIO
    from io import StringIO
except:
    import Tkinter as tk
    from Tkinter import Frame
    import StringIO
    import StringIO as BytesIO

import json
import myNotebook as nb
import os
import plug
import re
import requests
import shutil
import threading

import uuid
import zipfile
from canonn.debug import Debug
from canonn.debug import debug, error
from canonn.player import Player
from config import config


from ttkHyperlinkLabel import HyperlinkLabel

RELEASE_CYCLE = 60 * 1000 * 60  # 1 Hour
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


class ReleaseThread(threading.Thread):
    def __init__(self, release):
        threading.Thread.__init__(self)
        self.release = release

    def run(self):
        Debug.logger.debug("Release: UpdateThread")
        self.release.release_pull()


class Release(Frame):

    def __init__(self, parent, release, gridrow):
        "Initialise the ``News``."

        padx, pady = 10, 5  # formatting
        sticky = tk.EW + tk.N  # full width, stuck to the top
        anchor = tk.NW

        Frame.__init__(
            self,
            parent
        )

        self.installed = False

        self.auto = tk.IntVar(value=config.get_int("AutoUpdate"))
        self.novoices = tk.IntVar(value=config.get_int("NoVoices"))
        self.rmbackup = tk.IntVar(value=config.get_int("RemoveBackup"))

        self.columnconfigure(1, weight=1)
        self.grid(row=gridrow, column=0, sticky="NSEW", columnspan=2)

        self.label = tk.Label(self, text="Release:")
        self.label.grid(row=0, column=0, sticky=sticky)

        self.hyperlink = ReleaseLink(self)
        self.hyperlink.grid(row=0, column=1, sticky="NSEW")

        self.button = tk.Button(
            self, text="Click here to upgrade", command=self.click_installer)
        self.button.grid(row=1, column=0, columnspan=2, sticky="NSEW")
        self.button.grid_remove()

        self.release = release
        self.news_count = 0
        self.news_pos = 0
        self.minutes = 0
        self.latest = {}

        # self.hyperlink.bind('<Configure>', self.hyperlink.configure_event)
        self.bind('<<ReleaseUpdate>>', self.release_update)

        Debug.logger.debug(config.get_str('Canonn:RemoveBackup'))

        self.update(None)

        if self.rmbackup.get() == 1 and config.get_str('Canonn:RemoveBackup') and config.get_str('Canonn:RemoveBackup') != "None":
            delete_dir = config.get_str('Canonn:RemoveBackup')
            Debug.logger.debug('Canonn:RemoveBackup {}'.format(delete_dir))
            try:
                shutil.rmtree(delete_dir)

            except:
                Debug.logger.error("Cant delete {}".format(delete_dir))

            # lets not keep trying
            config.set('Canonn:RemoveBackup', "None")

    def update(self, event):
        self.release_thread()
        # check again in an hour
        #debug("checking for the next release in one hour")
        #self.after(RELEASE_CYCLE, self.update)

    def version2number(self, version):
        major, minor, patch = version.split('.')
        return (int(major) * 1000000) + (int(minor) * 1000) + int(patch)

    def release_thread(self):
        ReleaseThread(self).start()

    def release_pull(self):
        self.latest = {}
        r = requests.get(
            "https://api.github.com/repos/canonn-science/EDMC-Canonn/releases/latest")
        latest = r.json()
        # Debug.logger.debug(latest)
        if not r.status_code == requests.codes.ok:

            Debug.logger.error("Error fetching release from github")
            Debug.logger.error(r.status_code)
            Debug.logger.error(r.json())

        else:
            self.latest = latest
            Debug.logger.debug("latest release downloaded")
            if not config.shutting_down:
                self.event_generate('<<ReleaseUpdate>>', when='tail')

    def release_update(self, event):

        # if we have just installed a new version we can end the cycle
        if not self.installed:

            if self.latest:
                Debug.logger.debug("Latest is not null")

                # self.latest=requests.get("https://api.github.com/repos/canonn-science/EDMC-Canonn/releases/latest").json()

                current = self.version2number(self.release)
                release = self.version2number(self.latest.get("tag_name"))

                self.hyperlink['url'] = self.latest.get("html_url")
                self.hyperlink['text'] = "EDMC-Canonn: {}".format(
                    self.latest.get("tag_name"))

                if current == release:
                    self.grid_remove()
                elif current > release:
                    self.hyperlink['text'] = "Experimental Release {}".format(
                        self.release)
                    self.grid()
                else:

                    if self.auto.get() == 1:
                        self.hyperlink['text'] = "Release {}  Installed Please Restart".format(
                            self.latest.get("tag_name"))

                        if self.installer():
                            self.hyperlink['text'] = "Release {}  Installed Please Restart".format(
                                self.latest.get("tag_name"))
                        else:
                            self.hyperlink['text'] = "Release {}  Upgrade Failed".format(
                                self.latest.get("tag_name"))

                    else:
                        self.hyperlink['text'] = "Please Upgrade {}".format(
                            self.latest.get("tag_name"))
                        self.button.grid()
                        if self.novoices.get() != 1:
                            Player(Release.plugin_dir, [
                                   "sounds\\prefix.wav", "sounds\\nag1.wav"]).start()
                    self.grid()
            else:
                Debug.logger.debug("Latest is null")

    def plugin_prefs(self, parent, cmdr, is_beta, gridrow):
        "Called to get a tk Frame for the settings dialog."

        self.auto = tk.IntVar(value=config.get_int("AutoUpdate"))
        self.rmbackup = tk.IntVar(value=config.get_int("RemoveBackup"))
        self.novoices = tk.IntVar(value=config.get_int("NoVoices"))

        frame = nb.Frame(parent)
        frame.columnconfigure(2, weight=1)
        frame.grid(row=gridrow, column=0, sticky="NSEW")
        nb.Checkbutton(frame, text="Auto Update This Plugin",
                       variable=self.auto).grid(row=0, column=0, sticky="NW")
        nb.Checkbutton(frame, text="Remove backup", variable=self.rmbackup).grid(
            row=0, column=1, sticky="NW")
        nb.Checkbutton(frame, text="Stop talking to me", variable=self.novoices).grid(
            row=0, column=2, sticky="NW")

        return frame

    def prefs_changed(self, cmdr, is_beta):
        "Called when the user clicks OK on the settings dialog."
        config.set('AutoUpdate', self.auto.get())
        config.set('RemoveBackup', self.rmbackup.get())
        config.set('NoVoices', self.novoices.get())

    def click_installer(self):
        self.button.grid_remove()

        if self.installer():
            self.hyperlink['text'] = "Release {}  Installed Please Restart".format(
                self.latest.get("tag_name"))
        else:
            self.hyperlink['text'] = "Release {}  Upgrade Failed".format(
                self.latest.get("tag_name"))

    def installer(self):
        # need to add some defensive code around this
        tag_name = self.latest.get("tag_name")

        Debug.logger.debug("Installing {}".format(tag_name))

        new_plugin_dir = os.path.join(os.path.dirname(
            Release.plugin_dir), "EDMC-Canonn-{}".format(tag_name))

        Debug.logger.debug("Checking for pre-existence")
        if os.path.isdir(new_plugin_dir):
            Debug.logger.error(
                "Download already exists: {}".format(new_plugin_dir))
            plug.show_error("Canonn upgrade failed")
            return False

        try:
            Debug.logger.debug("Downloading new version")
            download = requests.get(
                "https://github.com/canonn-science/EDMC-Canonn/archive/{}.zip".format(tag_name), stream=True)

            try:
                z = zipfile.ZipFile(BytesIO(download.content))
                z.extractall(os.path.dirname(Release.plugin_dir))
            except:
                z = zipfile.ZipFile(StringIO.StringIO(download.content))
                z.extractall(os.path.dirname(Release.plugin_dir))
        except:
            Debug.logger.error("Download failed: {}".format(new_plugin_dir))
            plug.show_error("Canonn upgrade failed")

            return False

        # If we got this far then we have a new plugin so any failures and we will need to delete it

        Debug.logger.debug("disable the current plugin")
        try:
            os.rename(Release.plugin_dir,
                      "{}.disabled".format(Release.plugin_dir))
            Debug.logger.debug("Renamed {} to {}".format(Release.plugin_dir,
                                                         "{}.disabled".format(Release.plugin_dir)))
        except:
            Debug.logger.error(
                "Upgrade failed reverting: {}".format(new_plugin_dir))
            plug.show_error("Canonn upgrade failed")
            shutil.rmtree(new_plugin_dir)
            return False

        if self.rmbackup.get() == 1:
            config.set('Canonn:RemoveBackup',
                       "{}.disabled".format(Release.plugin_dir))

        Debug.logger.debug("Upgrade complete")

        Release.plugin_dir = new_plugin_dir
        self.installed = True

        return True

    @classmethod
    def get_auto(cls):
        return tk.IntVar(value=config.get_int("AutoUpdate")).get()

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir
