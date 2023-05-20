import plug
from config import config
import tkinter as tk
from tkinter import Frame
from theme import theme
from canonn.debug import Debug
import math


class OrganicScanner():

    def journal_entry(self, cmdr, is_beta, system, SysFactionState, SysFactionAllegiance, DistFromStarLS, station, entry,
                      state, x, y, z, body, nearloc, client):
        if entry.get("event") == "ScanOrganic":
            if entry.get("ScanType") in ("Sample", "Log"):
                self.species = entry.get("Species_Localised")
                self.genus = entry.get("Genus")
                self.show()
                self.label["text"] = entry.get("Variant_Localised")
                self.distance_label["text"] = entry.get("Genus_Localised")
                # store the position of the last scan
                self.lastloc = nearloc.copy()
                self.target_distance = self.get_distances(self.genus)
                self.distance_label["text"] = 0
                self.distance = 0
                theme.update(self.label)
                theme.update(self.distance_label)

            else:
                self.lastloc = None
                self.hide()

    def __init__(self, parent, gridrow):

        self.gridrow = gridrow
        self.parent = parent

        # we do not declare any widgets here as we will need to destroy them
        # to force the frame to be hidden. But we start hidden so set a value
        self.hidden = True

    def updatePosition(self, body_name, planet_radius, nearloc):

        if not self.hidden:
            if not body_name:
                self.hide()
            else:
                self.distance = self.calc_distance(
                    self.lastloc["Latitude"],
                    self.lastloc["Longitude"],
                    nearloc["Latitude"],
                    nearloc["Longitude"],
                    planet_radius
                )

                self.distance_label["text"] = f"{math.floor(self.distance)}m"
                if self.distance > self.target_distance:
                    self.distance_label.config(fg="green")
                    self.label.config(fg="green")
                else:
                    theme.update(self.label)
                    theme.update(self.distance_label)

    def calc_distance(self, lat_a, lon_a, lat_b, lon_b, radius):

        if radius is None:
            return 0.0

        lat_a = lat_a * math.pi / 180.
        lon_a = lon_a * math.pi / 180.
        lat_b = lat_b * math.pi / 180.
        lon_b = lon_b * math.pi / 180.

        if(lat_a != lat_b or lon_b != lon_a):
            d_lambda = lon_b - lon_a
            S_ab = math.acos(math.sin(lat_a)*math.sin(lat_b) +
                             math.cos(lat_a)*math.cos(lat_b)*math.cos(d_lambda))
            return S_ab * radius
        else:
            return 0.0

    def get_distances(self, genus):

        lookup = {
            "$Codex_Ent_Aleoids_Genus_Name;": 150,
            "$Codex_Ent_Vents_Name;": 100,
            "$Codex_Ent_Sphere_Name;": 100,
            "$Codex_Ent_Bacterial_Genus_Name;": 500,
            "$Codex_Ent_Cone_Name;": 100,
            "$Codex_Ent_Brancae_Name;": 100,  # brain tree?
            "$Codex_Ent_Seed_Name;": 100,  # brain tree
            "$Codex_Ent_Cactoid_Genus_Name;": 300,
            "$Codex_Ent_Clypeus_Genus_Name;": 150,
            # seen some mispelled entries
            "$Codex_Ent_Clepeus_Genus_Name;": 150,
            "$Codex_Ent_Conchas_Genus_Name;": 150,
            "$Codex_Ent_Ground_Struct_Ice_Name;": 100,
            "$Codex_Ent_Electricae_Genus_Name;": 1000,
            "$Codex_Ent_Fonticulus_Genus_Name;": 500,
            "$Codex_Ent_Shrubs_Genus_Name;": 150,
            "$Codex_Ent_Fumerolas_Genus_Name;": 100,
            "$Codex_Ent_Fungoids_Genus_Name;": 300,
            "$Codex_Ent_Osseus_Genus_Name;": 800,
            "$Codex_Ent_Recepta_Genus_Name;": 150,
            "$Codex_Ent_Tube_Name;": 100,
            "$Codex_Ent_Stratum_Genus_Name;": 500,
            "$Codex_Ent_Tubus_Genus_Name;": 800,
            "$Codex_Ent_Tussocks_Genus_Name;": 200
        }
        return lookup.get(genus) or 100

    def show(self):

        if self.hidden:
            self.hidden = False
            self.frame = Frame(self.parent)

            self.frame.columnconfigure(2, weight=1)
            self.frame.grid(row=self.gridrow, column=0,
                            columnspan=2)
            self.label = tk.Label(self.frame)
            self.label.grid(row=0, column=0)
            self.distance_label = tk.Label(self.frame)
            self.distance_label.grid(row=0, column=1)

            theme.update(self.frame)
            theme.update(self.label)
            theme.update(self.distance_label)

    def hide(self):

        if not self.hidden:
            self.hidden = True
            self.label.destroy()
            self.distance_label.destroy()
            self.frame.destroy()
