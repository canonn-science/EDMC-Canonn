# EDMC-Canonn
EDMC plugin to automatically collect accurate science data from the galaxy and coordinate missions

Features will be added in the Project Board

# Important

This plugin is currently only writing to the Canonn API and therefore anything you log may not end up being captured at this current time. Use the USS Survey plugin for the time being. NB The USS Survey and Canonn survey are not compatible when run together unless you are on the same version

# Features

## Patrol System
The Patrol system will eventualy be used for directing people to places of interest to Canonn. This will be based on the legacy patrol system for now. In addition we now have two extra patrol types. 
 
 * Canonn Influence Patrol: This tells you where systems have a Canonn Presence and gives some informatio about the current state
 * Ship Locations: This tells you where your ships are located
 
 ToDo: Controls to cycle through patrols.

## Canonn News Feed
See the top stories on rotation

## Hyperdiction reporting 
Hyperdiction reporting is logged from the Thargoid Encounter Stats screen. 

## NHSS Reporting
This captures NHSS information from the FSS scanner and USS Drops. Only logs one instance of each threat level per system

## Codex
This records the codex entries and a bit of extra info about body and lat lon. The codex entries are routed to the appropriate CAPI report. eg fgreports btreports etc.

## Thargoid Kills 
This records Thargoids kills. What else did you expect herds of wilderbeast running through the serengeti?

## Journal Data
This records all journal entries that haven't specifically been excluded. NB the exclusion list needs to be bigger.

## FSS Data
This records FSSSignalDicovered Messages that havent beenexcluded. Also records AX Conflict Zones in their own model

## Legacy Reporting
In the interests of launching the new plugin quicker I have integrated the legacy code that is used to opulate the spreadheets this will allow us to run reports in parallel. 
