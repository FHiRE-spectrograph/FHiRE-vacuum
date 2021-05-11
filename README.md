# FHiRE Vacuum System GUI
## Updated: 3-24-21
### Contact: Jason Rothenberg (jrothenb@uwyo.edu)

*Scripts posted to GITHUB  
__bold__ Important (Core) scripts

## Overview:

Code that runs FHiRE's vacuum system which includes a backing pump, turbomolecular pump, ion pump, non evaporable getter (NEG) pump, and a wide range gauge (WRG). The backing pump, turbo pump and WRG are all controlled through serial communication with an Edwards Turbo Instrument Controller (TIC). The ion and NEG pumps are controlled through serial communication with a NEXTorr NIOPS-03 pump controller which also has an internal gauge. The backing pump gets the enclosure down to mTorr pressures, at which point the turbo pump can be turned on and drops the system to ~10^-5 Torr. The NEG pump can be activated once below 10^-4 Torr and should be run for an hour. After activation, the NEG pump is turned off (it absorbs gases at room temp in high vacuum and doesn't need power to operate) and the ion pump can be turned if below 10^-5 Torr for achieving final vacuum pressure. System should come to ~10^-6 or 10^-7 Torr. Currently, the pump down and vent processes are manual but once they have been tested they should be automated within the TIC class. The GUI automatically checks on the status of each pump and gauge every 10 seconds and updates text fields and switches. It can also plot current pressure and save a .dat pressure log with 'Auto Plot', and import previous .dat logs through the dropdown menu Options>Import Pressure Log. Graphs open in a new window and can switch between plotting Pressure and Log Pressure using the Options drop down. Most manual buttons can be removed for the user version of the GUI but should be included in the admin GUI. The main future update that is required is incorporating the linear actuator valve that seals the vacuum enclosure after pump down so the pumps can be turned off for observations. Right now pumps have pressure conditions in place so they cannot but turned on or off at incompatible pressures; these conditions will need to be modified so pumps can be turned off if the valve is closed and the vacuum system is sealed. Then, after testing, automated pump down and vent procedues can be finalized.  

## List of files:

__*vacuum_control.py__:  
	Main code that controls FHiRE's vacuum system. Run with Python 2 (type 'python vacuum_control.py' in terminal)  

*adminGUI.ui:  
	Admin GUI design made with PyQt4 designer.  

__adminGUI.py__:  
	Imported into vacuum_control.py to set GUI layout. Created with Qt4 Designer. Converted from adminGUI.ui via the command 'pyuic4 adminGUI.ui -o adminGUI.py'.   

TIC.log:  
	Log file made by vacuum_control.py. Logs button presses, information, warnings, and errors. If deleted a new log file will be made.  

.dat files:  
	Saved pressure logs. Made by vacuum_control.py and can be imported and graphed at a later date.   

## Other folders: 

Old:  
	Previous versions of the software. Once the vacuum system software is finalized these can all be deleted.  

## To do:

[]Add linear actuator valve control (or might be separate PDU?)  
[]Add LN2 valve control (most likely separate PDU)  
[]Modify pump conditions so pumps can be turned off if valve closed  
[]Automate pump down and vent procedures  
[]Make two GUIs for admin and user  
