"""
Architect Display

Shows whether the current system (when Canonn or Canonn Deep Space Research
hold a minor faction presence there) already has a registered system
Architect, sourced from the Canonn Architects tracking sheet. If nobody has
registered one yet, shows a link to the submission form pre-filled with the
commander's name and the current system.
"""

import csv
import json
import os
import sys
import threading

import requests
import tkinter as tk
from tkinter import Frame

from canonn.debug import Debug
from canonn.systems import recent_journal
from canonn.tooltip import CreateToolTip
from config import config
from theme import theme
from ttkHyperlinkLabel import HyperlinkLabel

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

TSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vS5TMBu2KJQBaNqSBropWVdXUcOjz-wJe57e8h4pRPzr7zZ066yjO-H2Z7hqZe-fOVSpzy-7dzAqU2z"
    "/pub?gid=1448295597&single=true&output=tsv"
)
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfXin9fy62qiVurl1HRypwELW-nh6GATmxODgqMOPhb-S2sCA/viewform"
NAME_ENTRY = "entry.865244908"
SYSTEM_ENTRY = "entry.451477697"

TARGET_FACTIONS = {"canonn", "canonn deep space research"}
MEMBER_VALUE = "the architect is a canonn member"
NOT_A_COLONY_VALUE = "nobody the system is not a colony"
DONT_KNOW_VALUE = "don't know"


def get_field(row, index):
    try:
        return row[index]
    except IndexError:
        return None


def parse_architect_row(row):
    """
    Row columns: Timestamp, Your Name, System Name, Architect Name,
    Canonn Architect, Preferred Faction

    Returns (system_key, record) where system_key is the lower-cased,
    trimmed system name, or (None, None) if the row has no system name.
    """
    system = get_field(row, 2)
    architect = get_field(row, 3)
    canonn_architect = (get_field(row, 4) or "").strip().lower()
    preferred_faction = get_field(row, 5)

    if not system or not system.strip():
        return None, None

    record = {
        "architect": (architect or "").strip(),
        "member": canonn_architect == MEMBER_VALUE,
        "not_a_colony": canonn_architect == NOT_A_COLONY_VALUE,
        "unsure": canonn_architect == DONT_KNOW_VALUE,
        "preferred_faction": (preferred_faction or "").strip(),
    }
    return system.strip().lower(), record


def system_has_target_faction(entry):
    """
    True if entry (a Location/FSDJump/CarrierJump/StartUp journal event)
    lists Canonn or Canonn Deep Space Research among the system's factions.
    """
    factions = entry.get("Factions") or []
    for faction in factions:
        name = (faction.get("Name") or "").strip().lower()
        if name in TARGET_FACTIONS:
            return True
    return False


def find_recent_factions(system):
    """
    EDMC fires a synthetic "StartUp" event instead of the real "Location"
    when it attaches to a game that's already running, and per EDMC's
    PLUGINS.md that synthetic entry carries none of the original journal
    fields -- no "Factions" among them. Recover it by scanning the current
    journal file directly for the last real Location/FSDJump/CarrierJump
    entry for this system.
    """
    factions = None
    try:
        with open(recent_journal(), encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("event") in ("Location", "FSDJump", "CarrierJump"):
                    if entry.get("StarSystem") == system:
                        factions = entry.get("Factions")
    except Exception as e:
        Debug.logger.error("Failed to scan journal for a Factions fallback")
        Debug.logger.error(e)
    return factions


def build_prefill_url(cmdr, system):
    return "{}?usp=pp_url&{}={}&{}={}".format(
        FORM_URL,
        NAME_ENTRY,
        quote_plus(cmdr or ""),
        SYSTEM_ENTRY,
        quote_plus(system or ""),
    )


class ArchitectDisplay():

    @classmethod
    def plugin_start(cls, plugin_dir):
        cls.plugin_dir = plugin_dir

    def __init__(self, parent, gridrow):
        self.parent = parent
        self.gridrow = gridrow

        self.cmdr = ""
        self.system = ""
        self.eligible = False
        self.architects = {}
        self.download_started = False
        # True once a download has finished (successfully or not) this
        # session -- until then, an on-disk cache miss might just mean the
        # cache predates a recent registration, not "nobody's registered".
        self.data_ready = False

        self.cache_path = os.path.join(
            config.app_dir_path, "canonn", "EDMC-Canonn.architects"
        )
        self.load_cache()

        self.icon = tk.PhotoImage(
            file=os.path.join(
                ArchitectDisplay.plugin_dir, "icons", "canonn_member.png"
            )
        )

        self.frame = Frame(parent)
        self.frame.columnconfigure(1, weight=1)
        self.frame.grid(row=gridrow, column=0, columnspan=2, sticky="NSEW")

        self.label = tk.Label(self.frame, compound="left")
        self.label.grid(row=0, column=0, sticky="W")
        theme.update(self.label)
        self.tooltip = CreateToolTip(self.label, text="")

        self.link = HyperlinkLabel(
            self.frame,
            cursor=sys.platform == "darwin" and "pointinghand" or "hand2",
        )
        # Own row (not row 0, shared with self.label) so the two can be
        # shown at the same time -- needed for the "unsure" state, which
        # shows the architect's name plus a request to confirm/update it.
        self.link.grid(row=1, column=0, sticky="W")
        theme.update(self.link)

        self.label.grid_remove()
        self.link.grid_remove()
        self.frame.grid_remove()

    def load_cache(self):
        try:
            with open(self.cache_path) as f:
                self.architects = json.load(f)
        except Exception:
            Debug.logger.debug(
                "No Canonn architects cache yet at {}".format(self.cache_path)
            )

    def save_cache(self):
        try:
            with open(self.cache_path, "w+") as f:
                json.dump(self.architects, f)
        except Exception as e:
            Debug.logger.error("Failed to save Canonn architects cache")
            Debug.logger.error(e)

    def download(self):
        Debug.logger.debug("Downloading Canonn Architects TSV")
        try:
            r = requests.get(TSV_URL, stream=True)
            reader = csv.reader(
                r.content.decode("utf-8").splitlines(), delimiter="\t"
            )
            next(reader)  # header row
            architects = {}
            for row in reader:
                # Google Sheets always appends new form responses as the
                # last row, in submission order, so simply letting a later
                # row overwrite an earlier one for the same system is
                # enough to guarantee we keep the most recent entry.
                key, record = parse_architect_row(row)
                if key:
                    architects[key] = record
            self.architects = architects
            self.save_cache()
        except Exception as e:
            Debug.logger.error("Failed to download Canonn Architects TSV")
            Debug.logger.error(e)

        self.data_ready = True

        # Hand the UI update back to the Tk main loop instead of touching the
        # widgets directly from this background thread -- Tk is not
        # thread-safe, and `after()` is the safe way to marshal a call onto
        # the main thread from another one.
        try:
            self.frame.after(0, self.refresh)
        except Exception:
            pass

    def start_download(self):
        if not self.download_started:
            self.download_started = True
            threading.Thread(target=self.download, daemon=True).start()

    def refresh(self):
        if not self.eligible:
            self.frame.grid_remove()
            return

        self.frame.grid()
        record = self.architects.get((self.system or "").strip().lower())

        if record and record.get("not_a_colony"):
            self.link.grid_remove()
            self.label["image"] = ""
            self.label["text"] = "Core Canonn System"
            self.tooltip.text = "The system is not a colony"
            self.label.grid()
        elif record and record.get("architect") and record.get("unsure"):
            # We have a name on file, but the submitter didn't know if
            # they're a Canonn member -- show the name and ask for an
            # update, rather than picking a member/non-member icon we're
            # not confident in.
            self.label["image"] = ""
            self.label["text"] = "Architect: {}".format(record.get("architect"))
            self.tooltip.text = "Please try and find out if they are a member"
            self.label.grid()
            self.link["text"] = "Canonn membership unknown - click to update"
            self.link["url"] = build_prefill_url(self.cmdr, self.system)
            self.link.grid()
        elif record and record.get("architect"):
            self.link.grid_remove()
            self.label["image"] = self.icon if record.get("member") else ""
            self.label["text"] = "Architect: {}".format(record.get("architect"))
            if record.get("member"):
                self.tooltip.text = "Preferred Faction: {}".format(
                    record.get("preferred_faction") or "Unknown"
                )
            else:
                self.tooltip.text = "No BGS without Architects Permission"
            self.label.grid()
        elif self.data_ready:
            # Only ask to register an Architect once we've actually checked
            # the current registry this session -- an on-disk cache miss on
            # its own might just mean the cache predates a recent
            # registration, not that nobody's registered.
            self.label.grid_remove()
            self.link["text"] = "No Architect registered - click to submit"
            self.link["url"] = build_prefill_url(self.cmdr, self.system)
            self.link.grid()
        else:
            self.link.grid_remove()
            self.label["image"] = ""
            self.label["text"] = "Checking Canonn Architect Registry..."
            self.label.grid()

    def journal_entry(self, cmdr, system, entry):
        if cmdr:
            self.cmdr = cmdr

        event = entry.get("event")

        if event == "StartUp":
            # Per EDMC's PLUGINS.md, this synthetic entry (fired when EDMC
            # attaches to a game that's already running) carries none of the
            # original journal fields -- no "Factions" among them. Resolve it
            # from the journal file in the background so a slow disk read
            # never blocks the UI thread.
            self.system = system
            threading.Thread(
                target=self.resolve_missing_factions,
                args=(system,),
                daemon=True,
            ).start()

        elif event in ("Location", "FSDJump", "CarrierJump"):
            self.system = system
            self.eligible = system_has_target_faction(entry)

            if self.eligible:
                self.start_download()

            self.refresh()

        if event == "StartJump" and entry.get("JumpType") == "Hyperspace":
            self.eligible = False
            self.frame.grid_remove()

    def resolve_missing_factions(self, system):
        factions = find_recent_factions(system) or []
        eligible = system_has_target_faction({"Factions": factions})

        def apply():
            # Ignore a stale result if the player already jumped elsewhere
            # while this background lookup was running.
            if self.system != system:
                return
            self.eligible = eligible
            if self.eligible:
                self.start_download()
            self.refresh()

        try:
            self.frame.after(0, apply)
        except Exception:
            pass
