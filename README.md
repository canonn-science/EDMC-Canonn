# EDMC-Canonn
EDMC plugin to automatically collect accurate science data from the galaxy and coordinate missions

# Features

## Patrol System
The Patrol system is used for directing people to places of interest to Canonn and for providing some useful location information. The patrol will display the nearest location to the commander position. Patrols are not automaticaly updated they only get loaded on statup of after going into the configuration screen
 
 * Canonn patrols usually consist of locations where data is incomplete. 
 * Canonn Influence Patrol: This tells you where systems have a Canonn Presence and gives some informatio about the current state
 * Galactic Mapping POIs show you the nearest Galactic mapping project entry.
 * Thargoid Sites show you the location of the nearest site and its type. 
 * Guardian Sites shows you the nearest guardian site 
 
## Canonn News Feed
See the top stories on rotation

## Hyperdiction reporting 
Hyperdiction reporting is logged from the Thargoid Encounter Stats screen. There is also a button in the settings which will allow you to upload all hyperdictions from your journal. 

## NHSS Reporting
This captures NHSS information from the FSS scanner and USS Drops. Only logs one instance of each threat level per system

## Codex Icons
The plugin will look up EDSM and Canonn Databases to identify interesting facts about the system and display icons that show you what is in the current system.  This may be biology, geology or system features such as earth like worlds, shepherd moons and close orbits. It will also show you how many bodies are recorded in EDSM and how many bodies there are in total. It also shows you Jumponium materials.

## Codex

This records the codex entries and a bit of extra info about body and lat lon. The codex entries are routed to the appropriate CAPI report. eg fgreports btreports etc. Most data gets sent to be stored in the Canonn API https://api.canonn.tech/documentation

We also provide excel sheets with much of the data held in the CAPI

* [Surface Biology](https://canonn.fyi/biosheet)
* [Guardian](https://canonn.fyi/guardiansheet)
* [Lagrange Clouds](https://docs.google.com/spreadsheets/d/11BCZRci0YlgW0sFdxvB_srq7ssxHzstMAiewhSGHE94)
* [Thargoid](https://canonn.fyi/thargoidsheet)

All Codex data some FSS Events and SAA Signals are stored in a cloud mysql database and used for showing code icons. This data can be accessed through data dumps in compressed json format.

* [Codex Events](https://drive.google.com/file/d/138PgJgUCv1Y10LRDsj3eUnOZh3cf_1v4/view?usp=sharing)
* [FSS Events](https://drive.google.com/file/d/167wFlOrklf5tT2C1LtYGi8Ryjg-HpFXB/view?usp=sharing)
* [Signals](https://drive.google.com/file/d/1VyxpC3xux7A9oKYZ9xEApVND-CFeF_Lf/view?usp=sharing)

## Thargoid Kills 
This records Thargoids kills. What else did you expect herds of wilderbeast running through the serengeti?

## Journal Data
This records all journal entries that haven't specifically been excluded. NB the exclusion list needs to be bigger.

## FSS Data
This records FSSSignalDicovered Messages that havent beenexcluded. Also records AX Conflict Zones in their own model

## Carrier Location Data
This records FSSSignalDicovered from carriers. A public API will follow soon.

## Status Capture
This is a system that captures the status.json and stores it in the database with comments. 

## canonn dest
typing canonn dest <lat> <lon> will give you a bearing to that latitude and longitude that you can follow with colour on target indicators