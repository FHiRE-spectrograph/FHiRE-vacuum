import serial, io, sys, os, logging, time, datetime, threading, Queue, subprocess

# Plotting imports.
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as mtick
import numpy as np

# GUI imports.
from PyQt4 import QtGui,QtCore
import adminGUI

#import modules to run the gate valve.
from v_valve_module import V_Valve
import RPi.GPIO as GPIO

#Import module for LN2 Valve
from ln2_valve_module import LN2_Valve,LN2_ValveGUI

	
# Set up logging. Change level=logging.INFO to level=logging.DEBUG to show raw 
# serial communication.
LOG_FILENAME = './TIC_logs/generalLog_' + \
	       datetime.datetime.now().strftime('%Y%m%d') + \
	       '.log'
	
logging.basicConfig(
	format='%(asctime)s, %(levelname)s, %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S',
	filename=LOG_FILENAME)

logr = logging.getLogger(LOG_FILENAME)

# Link printed and logging messages.
def printInfo(message):
	logr.info(message)
	print message

def printWarning(message):
	logr.warning(message)
	print message

def printError(message):
	logr.error(message)
	print message

def printDebug(message):
	logr.debug(message)
	if logr.getEffectiveLevel() == 10:	
		print message
	else:
		pass

# Set display options for navigation toolbar.
class NavigationToolbar(NavigationToolbar2QT):
	def __init__(self, *args, **kwargs):
		super(NavigationToolbar, self).__init__(*args, **kwargs)
		# Removes weird edit parameters button.
		self.layout().takeAt(6)  

	# Only display the buttons we need.
	toolitems = [t for t in NavigationToolbar2QT.toolitems if t[0] in (
				'Home', 'Forward', 'Back', 'Pan', 'Zoom', 'Save')]

# Set terminal output to GUI textBox.
class EmittingStream(QtCore.QObject):
	textWritten=QtCore.pyqtSignal(str) 
	
	def write(self,text):
		self.textWritten.emit(str(text))

#--------------------------------------------------------------------
# GUI CLASSES
#--------------------------------------------------------------------

# Graphing window GUI class.
class SecondUiClass(QtGui.QMainWindow):	
	Log_pressure = False
	Import = False
	filepath = None
	import_filepath = None

	def __init__(self, parent=None):
		super(SecondUiClass, self).__init__(parent)
		# Create the window.
		self.main = QtGui.QWidget()
		self.setCentralWidget(self.main)
		self.layout = QtGui.QVBoxLayout(self.main)
		self.setGeometry(100, 100, 1000, 600)
		self.setWindowTitle('FHiRE Vacuum Controller - Graphing Window')

		# Set up the action menu.
		actionPressure = QtGui.QAction('Graph Pressure', self)
		actionLog_Pressure = QtGui.QAction('Graph Log Pressure', self)	
		actionPressure.triggered.connect(self.PlotPressure)
		actionLog_Pressure.triggered.connect(self.PlotLogPressure)

		mainMenu = self.menuBar()
		fileMenu = mainMenu.addMenu('&Options')
		fileMenu.addAction(actionPressure)
		fileMenu.addAction(actionLog_Pressure)

		# Set up the figure.
		self.figure = Figure()
		self.canvas = FigureCanvas(self.figure)
		self.layout.addWidget(self.canvas)
		self.toolbar=NavigationToolbar(self.canvas, self)
		self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
		
	# Main plotting process.
	def Plot(self, importing):
		# Set up the graph.
		self.ax = self.figure.add_subplot(111)	
		self.ax.hold(False)

		#printInfo("self.filepath: %s" %self.filepath)
		#printInfo("self.import_filepath: %s" %self.import_filepath)
		
		# Check if importing or using live data.
		self.importing = importing
		if self.importing == False:
			open_file = self.filepath
		else:
			open_file = self.import_filepath
			if self.import_filepath == None:
				printInfo("Please import a pressure log file.")

		# Graph pressure vs. time. 
		try:
			date, pressure = np.loadtxt(open_file, unpack=True, skiprows=1)
		except ValueError:
			printInfo("Error: Need more values to graph.")
			return
		self.ax.plot(date, pressure, 'r-')
		filename = open_file.split('/')[-1]
		
		# Format axes.
		self.ax.set_title("Graphing: %s" %filename)
		self.ax.set_xlabel('Time (h:m:s)')
		self.ax.set_ylabel('Pressure (mbar)')
		myFmt = mdates.DateFormatter('%H:%M:%S')
		self.ax.xaxis.set_major_formatter(myFmt)
		self.ax.xaxis.set_minor_locator(AutoMinorLocator())
		self.ax.yaxis.set_minor_locator(AutoMinorLocator())
		y_formatter = mtick.ScalarFormatter(useOffset=True)
		self.ax.yaxis.set_major_formatter(y_formatter)
		self.ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.3e'))
		self.ax.grid()

		# Display the graph.
		self.canvas.draw()
		self.canvas.flush_events()

	# Modify the plot to show pressure or log pressure.
	def PlotPressure(self):
		self.Log_pressure = False
		self.updateThread()	

	def PlotLogPressure(self):
		self.Log_pressure = True
		self.updateThread()

	# This thread allows updates to be made to the graph after creation.
	# Used for updating y axis. 
	def updateThread(self):	
		update_thread = threading.Thread(target=self.UpdatePlot)
		update_thread.setDaemon(True)
		update_thread.start()

	# Update the graph. Used for autoplotting.
	def UpdatePlot(self):
		date, pressure = np.loadtxt(self.filepath, unpack=True, skiprows=1)

		if self.Log_pressure == True:
			pressure = np.log10(pressure)
			self.ax.set_ylabel('Log Pressure (mbar)')
		else:
			self.ax.set_ylabel('Pressure (mbar)')

		self.ax.plot(date, pressure, 'r-')
		filename = self.filepath.split('/')[-1]

		self.ax.set_title("Graphing: %s" %filename)
		self.ax.set_xlabel('Time (h:m:s)')
		myFmt = mdates.DateFormatter('%I:%M:%S')
		self.ax.xaxis.set_major_formatter(myFmt)
		self.ax.xaxis.set_minor_locator(AutoMinorLocator())

		self.ax.yaxis.set_minor_locator(AutoMinorLocator())
		y_formatter = mtick.ScalarFormatter(useOffset=True)
		self.ax.yaxis.set_major_formatter(y_formatter)
		self.ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.3e'))
		self.ax.grid()
		self.ax.relim()
		self.ax.autoscale_view()
		self.toolbar.update()

		self.canvas.draw()
		self.canvas.flush_events()

# Main window GUI class (inherits from qt designer's adminGUI.ui or userGUI.ui).
# Change adminGUI to userGUI to switch interfaces.
class MainUiClass(QtGui.QMainWindow, adminGUI.Ui_MainWindow):

	def __init__(self):
		super(MainUiClass,self).__init__()
		self.setupUi(self)

		self.importing = False

		# Creates instance of the graphing window class.
		self.graph_window = SecondUiClass()

		# Start queue capability (adds button presses to a queue 
		# and calls functions one at a time so the GUI doesn't freeze up.)
		self.q = Queue.Queue()
		self.queueThread()

		# Showing that the manual ON and OFF pump buttons are no longer
		# being used, they're obsolete. They've been replaced by 
		# checkable buttons at the top of the GUI. 
		self.pump_button_on.setText('')
		self.pump_button_off.setText('')
		self.ion_button_on.setText('')
		self.ion_button_off.setText('')
		self.neg_button_on.setText('')
		self.neg_button_off.setText('')
		self.turbo_button_on.setText('')
		self.turbo_button_off.setText('')

		# Send terminal outputs to the GUI textBox.
		sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
		# Comment out to send errors to terminal for troublshooting.
		#sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)

		printInfo("...\n...\n...\nWindow opened.")

		# Start threads and connect buttons.
		self.createTICThread()
		self.connectSignals()	
		
		# Turn off following lines to run code without connection 
		# to controllers. All function calls but self.cycleThread() 
		# are called once at startup here to avoid the delays in 
		# self.cycleThread.
		time.sleep(1)
		self.Create_dat()
		self.Collect_data()
		self.Backing_check()
		self.Ion_check()
		self.Turbo_check()

		self.cycleThread()

		# Instantiate the V_Valve object to control the gate valve
		self.vac_valve = V_Valve(27,5,6)
		self.GateValveCheck()
		
		
	# Functionality to disable printing.
	def blockPrint(self):
		sys.stdout = open(os.devnull, 'w')

	# Functionality to restore printing.
	def enablePrint(self):
		sys.stdout=EmittingStream(textWritten=self.normalOutputWritten)

	#
	# Threading setup.
	#

	# Connect buttons not realated to workers.
	def connectSignals(self):
		# Set up pump switches.
		self.ion_switch.setCheckable(True)
		self.ion_switch.setStyleSheet(
				'QPushButton#ion_switch {background-color : ' \
				'#e57373; border-style: inset; border-width: ' \
				'2px; border-radius: 10px; padding: 6px;}' \
				'QPushButton#ion_switch:checked ' \
				'{background-color: #8bc34a; border-style: outset;}')  

		self.neg_switch.setCheckable(True)
		self.neg_switch.setStyleSheet(
				'QPushButton#neg_switch {background-color : ' \
				'#e57373; border-style: inset; border-width: ' \
				'2px; border-radius: 10px; padding: 6px;}' \
				'QPushButton#neg_switch:checked ' \
				'{background-color: #8bc34a; border-style: outset;}')  

		self.backing_switch.setCheckable(True)
		self.backing_switch.setStyleSheet(
				'QPushButton#backing_switch {background-color : ' \
				'#e57373; border-style: inset; border-width: ' \
				'2px; border-radius: 10px; padding: 6px;}' \
				'QPushButton#backing_switch:checked ' \
				'{background-color: #8bc34a; border-style: outset;}')  

		self.turbo_switch.setCheckable(True)		
		self.turbo_switch.setStyleSheet(
				'QPushButton#turbo_switch {background-color : ' \
				'#e57373; border-style: inset; border-width: ' \
				'2px; border-radius: 10px; padding: 6px;}' \
				'QPushButton#turbo_switch:checked ' \
				'{background-color: #8bc34a; border-style: outset;}')  

		# Setup functionality to buttons and options.
		self.ion_switch.clicked.connect(lambda: self.q.put(self.ionSwitch))
		self.neg_switch.clicked.connect(lambda: self.q.put(self.negSwitch))
		self.backing_switch.clicked.connect(lambda: self.q.put(self.backingSwitch))
		self.turbo_switch.clicked.connect(lambda: self.q.put(self.turboSwitch))
		
		self.graph.clicked.connect(self.create_new_window)
		
		self.actionImport.triggered.connect(self.importFile)
		self.pump_down.clicked.connect(self.pumpDownDialog)
		self.vent.clicked.connect(self.ventDialog)
		self.seal_button.clicked.connect(self.GateValve)

		#Setup connections to change style sheet for gate valve
		self.connect(self, QtCore.SIGNAL('#e3c652'), \
							self.GateValveStyleA)
		self.connect(self, QtCore.SIGNAL('#8bc34a'), \
							self.GateValveStyleB)
		self.connect(self, QtCore.SIGNAL('#e57373'), \
							self.GateValveStyleC)

	def GateValveStyleA(self):
		self.seal_button.setStyleSheet('QPushButton#seal_button {background-color : ' \
			'#e3c652;}')
	def GateValveStyleB(self):
		self.seal_button.setStyleSheet('QPushButton#seal_button {background-color : ' \
			'#8bc34a;}')
	def GateValveStyleC(self):
		self.seal_button.setStyleSheet('QPushButton#seal_button {background-color : ' \
			'#e57373;}')
	
	# Setup the TIC worker object and the tic_thread.
	def createTICThread(self):
		self.tic = TIC()
		self.tic_thread = QtCore.QThread()
		self.tic.moveToThread(self.tic_thread)
		self.tic_thread.start()

		# Connect worker signals for the TIC controller.
		self.gauge_button.clicked.connect(
					lambda: self.q.put(self.Collect_data))	
		self.auto_plot.clicked.connect(lambda: self.q.put(self.autoPlotThreader))
		self.stop_plot.clicked.connect(lambda: self.q.put(self.stop_plotting))
		self.connect(self.tic, QtCore.SIGNAL('block_print'), self.blockPrint)
		self.connect(self.tic, QtCore.SIGNAL('enable_print'), self.enablePrint)
		self.connect(self, QtCore.SIGNAL('create_new_window'), \
							self.create_new_window)
		self.connect(self, QtCore.SIGNAL('update_window'), \
							self.graph_window.UpdatePlot)
		#self.connect(
		self.connect(self.tic, QtCore.SIGNAL('backing_on'), self.setBackingTextOn)
		self.connect(self.tic, QtCore.SIGNAL('backing_off'), self.setBackingTextOff)
		self.connect(self.tic, QtCore.SIGNAL('turbo_on'), self.setTurboTextOn)
		self.connect(self.tic, QtCore.SIGNAL('turbo_off'), self.setTurboTextOff)

		# Connect worker signals for the ion pump.
		self.connect(self.tic, QtCore.SIGNAL('block_print'), self.blockPrint)
		self.connect(self.tic, QtCore.SIGNAL('enable_print'), self.enablePrint)
		self.connect(self.tic, QtCore.SIGNAL('ion_on'), self.setIonTextOn)
		self.connect(self.tic, QtCore.SIGNAL('ion_off'), self.setIonTextOff)
		self.connect(self.tic, QtCore.SIGNAL('neg_on'), self.setNegTextOn)
		self.connect(self.tic, QtCore.SIGNAL('neg_off'), self.setNegTextOff)
	
	# Thread that runs the queue.
	def queueThread(self):
		queueWorker = threading.Thread(target=self.queueRunner)
		# Daemon threads will close when application is closed.
		queueWorker.setDaemon(True)
		queueWorker.start()

	# Checks queue and calls functions at turn. Runs indefinitely.
	def queueRunner(self):
		while True:
			f = self.q.get()
			f()
			self.q.task_done()

	# Thread that checks pump states and pressure.
	def cycleThread(self):
		cycle_thread = threading.Thread(target=self.cycleCheck)
		cycle_thread.setDaemon(True)
		cycle_thread.start()

	# Pump down and vent threads.
	def pumpDownThread(self):
		self.Collect_data()
		pumpdown_thread = threading.Thread(target=self.tic.Pump_down)
		pumpdown_thread.setDaemon(True)
		pumpdown_thread.start()

	def ventThread(self):	
		self.Collect_data()
		vent_thread = threading.Thread(target=self.tic.Vent)
		vent_thread.setDaemon(True)
		vent_thread.start()

	# Auto plotting thread.
	def autoPlotThreader(self):
		plot_thread = threading.Thread(target=self.Auto_plotter)
		plot_thread.setDaemon(True)
		plot_thread.start()	

	#
	# Etc. Methods.
	#

	# Setup live plotting.
	# Since Auto_plotter is run within a thread, signals need to be used
	# to communicate with the main class. 
	def Auto_plotter(self):
		self.autoplotting = True
		n = 1
		while self.autoplotting == True:
			time.sleep(3)
			if n == 1:
				self.importing = False
				self.emit(QtCore.SIGNAL('create_new_window'))
			else:
				self.emit(QtCore.SIGNAL('update_window'))

			n += 1
			printDebug('Sleeping...')
			time.sleep(30)

	def stop_plotting(self):
		self.autoplotting = False

	# Pulls up new graphing window.
	def create_new_window(self):
		printInfo('Plotting...')
		self.graph_window.show()
		self.graph_window.Plot(self.importing)

	#
	# On/off pump switch configurations.
	# If a pump is sucessfully turned  on or off, the tic thread will 
	# send a signal to change the checkable button accordingly. 
	# ON = green, OFF = red.
	#
	def backingSwitch(self):
		if self.backing_switch.isChecked(): 
			self.tic.Backing_on()
		else: 
			self.tic.Backing_off()

	def setBackingTextOn(self):
		self.backing_switch.setChecked(True)
		self.backing_switch.setText('ON')

	def setBackingTextOff(self):
		self.backing_switch.setChecked(False)
		self.backing_switch.setText('OFF')

	def turboSwitch(self):
		if self.turbo_switch.isChecked(): 
			self.tic.Turbo_on()
		else: 
			self.tic.Turbo_off()

	def setTurboTextOn(self):
		self.turbo_switch.setChecked(True)
		self.turbo_switch.setText('ON')

	def setTurboTextOff(self):
		self.turbo_switch.setChecked(False)
		self.turbo_switch.setText('OFF')

	def ionSwitch(self):
		if self.ion_switch.isChecked():  
			self.tic.Ion_on()
		else: 
			self.tic.Ion_off()

	def setNegTextOn(self):
		self.neg_switch.setChecked(True)
		self.neg_switch.setText('ON')

	def setNegTextOff(self):
		self.neg_switch.setChecked(False)
		self.neg_switch.setText('OFF')

	def setIonTextOn(self):
		self.ion_switch.setChecked(True)
		self.ion_switch.setText('ON')

	def setIonTextOff(self):
		self.ion_switch.setChecked(False)
		self.ion_switch.setText('OFF')

	def negSwitch(self):
		if self.neg_switch.isChecked():  
			self.tic.Neg_on()
		else: 
			self.tic.Neg_off()

	# Pump status checks.
	def Backing_check(self):
		status = self.tic.Backing_status()
		if status == '4':
			printInfo('Backing pump is on.')
			self.setBackingTextOn()
		elif status == '0':
			printInfo('Backing pump is off.') 
			self.setBackingTextOff()
		elif status == '1':
			printInfo('Backing pump is turning on.')
			self.setBackingTextOn()
		elif status == '2' or status == '3':
			printInfo('Backing pump is turning off.') 
			self.setBackingTextOff()
		else:
			printError('Backing pump state unknown.')

	def Ion_check(self):
		ion_status, neg_status = self.tic.Ion_status()
		if ion_status == 'IP ON':
			printInfo('Ion pump is on.')
			self.setIonTextOn()
			# Check if pressure is low enough for ion pump to be on.
			if self.tic.pressure_reading > 1e-5 * 1.333:
				printWarning('Pressure is too high (> 1.3e-5 mbar) ' \
					     'for ion pump to function')
				# Turn off pump if pressure too high.
				self.q.put(self.tic.Ion_off)
		elif ion_status == 'IP OFF':
			printInfo('Ion pump is off.')
			self.setIonTextOff()
		else:
			printError('Ion pump state unknown.')

		if any('NP ON' in s for s in neg_status):
			printInfo('NEG pump is on.')
			self.setNegTextOn()
			# Checks if pressure is low enough for neg pump to be on.
			if self.tic.pressure_reading > 1e-4 * 1.333:
				printWarning('Pressure is too high (> 1.3e-4 mbar) ' \
					     'for NEG pump to function')
				self.q.put(self.tic.Neg_off)
		elif any('NP OFF' in s for s in neg_status):
			printInfo('NEG pump is off.')
			self.setNegTextOff()
		else:
			printError('NEG pump state unknown.')

	def Turbo_check(self):
		status = self.tic.Turbo_status()
		if status == '4':
			printInfo('Turbo pump is on.')
			self.setTurboTextOn()
		elif status == '0':
			printInfo('Turbo pump is off.')
			self.setTurboTextOff()
		elif status == '6' or status == '7':
			printInfo('Turbo pump is braking.') 
			self.setTurboTextOff()
		elif status == '5':
			printInfo('Turbo pump is accelerating.')
			self.setTurboTextOn()
		elif status == '1':
			printInfo('Turbo pump is starting with delay.')
			self.setTurboTextOn()
		elif status == '2' or status == '3':
			printInfo('Turbo pump is stopping with delay.')
			self.setTurboTextOff()
		else:
			printError('Turbo pump state unknown.')

	# Loop that checks status of each pump and checks pressure every 10 seconds. 
	# Can change sleep times to optimize GUI when finialized.
	def cycleCheck(self):
		while True:
			time.sleep(5)
			self.q.put(self.Collect_data)
			time.sleep(10)
			self.q.put(self.Backing_check)
			time.sleep(10)
			self.q.put(self.Turbo_check)
			time.sleep(10)
			self.q.put(self.Ion_check)
			time.sleep(5)
			self.q.put(self.GateValveCheck)
			
	# Vent warning message.
	def ventDialog(self):
		msg = QtGui.QMessageBox(self.centralwidget)
		msg.setIcon(QtGui.QMessageBox.Warning)
		ion_status, neg_status = self.tic.Ion_status()
		if ion_status == 'IP OFF' and any('NP OFF' in s for s in neg_status):
			msg.setText('Are you sure you want to vent the system? ' \
			    'This will take approximately 4 hours. There is ' \
			    'no way to abort a vent procedure.')
			msg.setWindowTitle('Vent Warning')
			msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
			msg.setDefaultButton(QtGui.QMessageBox.Cancel)
			ret = msg.exec_();

			if ret == QtGui.QMessageBox.Ok:
				printInfo('Starting vent procedure...')			
				self.ventThread()
				self.vent.setStyleSheet('QPushButton#vent {background-color : ' \
				'#f7d95e;}')
				self.pump_down.setStyleSheet('QPushButton#pump_down {background-color : ' \
				'#ffffff;}')
			elif ret == QtGui.QMessageBox.Cancel:
				printInfo('Vent procedure canceled...')
		
		else:
			msg.setText('Turn off NEG and Ion Pumps before vent down')
			msg.setWindowTitle('Vent Warning')
			msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)


	# Pump down warning message.
	def pumpDownDialog(self):
		msg = QtGui.QMessageBox(self.centralwidget)
		msg.setIcon(QtGui.QMessageBox.Warning)
		msg.setText('Are you sure you want to pump down the system? ' \
			    'This will take approximately 36 hours. You can ' \
			    'abort a pump down procedure if needed.')
		msg.setWindowTitle('Pump Down Warning')
		msg.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
		msg.setDefaultButton(QtGui.QMessageBox.Cancel)
		ret = msg.exec_();

		if ret == QtGui.QMessageBox.Ok:
			printInfo('Starting pump down procedure...')			
			self.pumpDownThread()
			self.pump_down.setStyleSheet('QPushButton#pump_down {background-color : ' \
				'#f7d95e;}')
		elif ret == QtGui.QMessageBox.Cancel:
			printInfo('Pump down canceled...')

	# Importing data from a .dat file.
	def importFile(self):
		printInfo('Select a .dat file to import a pressure log...')
		dialog = QtGui.QFileDialog		
		self.import_filepath = dialog.getOpenFileName(
				self, 'Select dat file', '.', 'DAT files(*.dat)')
		import_filename = str(self.import_filepath.split('/')[-1])

		# Need to have path to file in reference to the current directory.
		self.import_filepath = './pressure_logs/' + import_filename

		self.importing = True
		self.graph_window.import_filepath = self.import_filepath
		print("Importing pressure log file: %s." %import_filename)
	
	# Create pressure data log.
	def Create_dat(self):
		filepath = './pressure_logs/pressureLog_' + \
				datetime.datetime.now().strftime('%Y%m%d')
		i = 1
		while True:
			if os.path.isfile("%s-%s.dat" %(filepath, i)):
				i += 1
			else:
				break

		self.filepath = filepath + '-%s.dat' % i
		self.graph_window.filepath = self.filepath
		self.filename = filepath.split('/')[-1]

		with open(self.filepath, 'w') as pressureLog:
			pressureLog.seek(0,0)
			pressureLog.write('Float date	Pressure (mbar)\n')
		print("Pressure log file created: %s" %self.filename)

	# Read and save gauge data.
	def Collect_data(self):
		self.tic.pressure_reading, timestamp = self.tic.Gauge_read()
		self.tic.ion_pressure_reading = self.tic.Ion_gauge()

		if None in [self.tic.pressure_reading, timestamp]:
			printInfo("No pressure measurements recorded.")
			return

		with open(self.filepath, 'a') as pressureLog:
			pressureLog.write('%.6f	%.6e\n' %(timestamp, self.tic.pressure_reading))

		self.tic_pressureText.setText(str(self.tic.pressure_reading) + ' mbar')

		if self.tic.ion_pressure_reading == 0:
			self.ion_pressureText.setText('Ion Gauge Off')
		else:
			self.ion_pressureText.setText(str(self.tic.ion_pressure_reading) + ' mbar')

	# Operation of the GateValve
	def GateValve(self):
		self.vac_valve.Push()
		self.GateValveCheck()

	def GateValveCheck(self):
		vvStat = self.vac_valve.Status()
		if vvStat == 1:
			printInfo('V_Valve Error: Both swithces read False')
			self.emit(QtCore.SIGNAL('#e3c652'))
		elif vvStat == 2:
			printInfo('V_Valve Error: Both switches read True')
		elif vvStat == 3:
			printInfo('Vacuum Valve is open')
			self.emit(QtCore.SIGNAL('#8bc34a'))
		elif vvStat == 4:
			printInfo('Vavuum Valve is closed')
			self.emit(QtCore.SIGNAL('#e57373'))
		else:
			printInfo('Did not read inputs')

	# Functionality to restore sys.stdout and sys.stderr.
	def __del__(self):
		sys.stdout=sys.__stdout__
		sys.stderr=sys.__stderr__

	# Write to textBox textEdit.
	def normalOutputWritten(self,text):		
		self.textEdit.insertPlainText(text)
		# Set scroll bar to focus on new text.
		sb = self.textEdit.verticalScrollBar()
		sb.setValue(sb.maximum() - .8 * sb.singleStep())

	# Closing procedure on exit.
	# **Find appropriate syntax for PyQt4.**
	# **Need to close any running graphs and nondameon thread.**
	def closeEvent(self, event):
		#reply = QtWidgets.QMessageBox.question(self, 'Window Close',
		#			'Are you sure you want to close the window?',
		#			QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No,
		#			QtWidgets.QMessageBox.No)
		
		#if reply == QtWidgets.QMessageBox.Yes:
			#self.tic.ser.close()  # Doesn't call anything.
		#	print("Window Closed")
		#	event.accept()
		#else:
		#	event.ignore()
		printInfo("Window closed.")
		GPIO.cleanup()

#--------------------------------------------------------------------
# SERIAL CLASSES
#--------------------------------------------------------------------

# Class that communicates with TIC controller and ion pump/neg pump controller.
class TIC(QtCore.QObject):
	# Base TIC commands.
	TERMINAL = chr(13)  # carriage return

	PRECEDING_QUERY = '?'
	PRECEDING_COMMAND = '!'
	PRECEDING_REPLY = '*'
	PRECEDING_RESPONSE = '='

	TYPE_COMMAND = 'C'
	TYPE_VALUE = 'V'
	TYPE_SETUP = 'S'

	SEPARATOR = ' '
	DATA_SEPARATOR = ';'

	ON = '1'
	OFF = '0'

	TURBO_PUMP = '904'
	BACKING_PUMP = '910'
	GAUGE_1 = '913'
	nEXT_PUMP = '852'
	nEXT_VENT = '853'

	# NEXTorr (ion/neg pump) commands - consist of command identifier, 
	# carriage return, line feed.
	STATUS = 'TS\r\n'
	PRESSURE = 'Tt\r\n'  # in torr
	IP_ON = 'G\r\n'
	IP_OFF = 'B\r\n'
	NP_ON = 'GN\r\n'
	NP_OFF = 'BN\r\n'

	def __init__(self, parent=None):
		super(self.__class__, self).__init__(parent)

		try:
			self.ser = serial.Serial(port = '/dev/ttyUSB1',
							baudrate=9600,
							bytesize=serial.EIGHTBITS,
							parity=serial.PARITY_NONE,
							stopbits=serial.STOPBITS_ONE,
								timeout=.5)   
			self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser))
			printInfo('Connected to TIC Controller.')

		except:
			printError('Could not connect to TIC Controller.')

		# Connect to the NEXTorr controller through serial port, 
		# USB0 is the top port in the middle column.
		try:
			self.serIon = serial.Serial(port = '/dev/ttyUSB0',
							baudrate=115200,
							bytesize=serial.EIGHTBITS,
							parity=serial.PARITY_NONE,
							stopbits=serial.STOPBITS_ONE,
							timeout=.5)   

			self.sioIon = io.TextIOWrapper(
					io.BufferedRWPair(self.serIon, self.serIon))
			printInfo('Connected to NEXTorr Power Supply.')

		except:
			printError('Could not connect to NEXTorr Power Supply.')

		# List of TIC commands - consist of preceding identifier, 
		# message type, object ID, space, data, cr.
		self.gauge_read = "".join([
				self.PRECEDING_QUERY,
				self.TYPE_VALUE,
				self.GAUGE_1,
				self.TERMINAL])

		self.backing_on = "".join([
				self.PRECEDING_COMMAND,
				self.TYPE_COMMAND,
				self.BACKING_PUMP,
				self.SEPARATOR,
				self.ON,
				self.TERMINAL]) 
		self.backing_off = "".join([
				self.PRECEDING_COMMAND,
				self.TYPE_COMMAND,
				self.BACKING_PUMP,
				self.SEPARATOR,
				self.OFF,
				self.TERMINAL]) 
		self.backing_check = "".join([
				self.PRECEDING_QUERY,
				self.TYPE_VALUE,
				self.BACKING_PUMP,
				self.TERMINAL])

		self.turbo_on = "".join([
				self.PRECEDING_COMMAND,
				self.TYPE_COMMAND,
				self.TURBO_PUMP,
				self.SEPARATOR,
				self.ON,
				self.TERMINAL]) 
		self.turbo_off = "".join([
				self.PRECEDING_COMMAND,
				self.TYPE_COMMAND,
				self.TURBO_PUMP,
				self.SEPARATOR,
				self.OFF,
				self.TERMINAL]) 
		self.turbo_check = "".join([
				self.PRECEDING_QUERY,
				self.TYPE_VALUE,
				self.TURBO_PUMP,
				self.TERMINAL]) 

		self.pressure_reading = None
		self.ion_pressure_reading = None

	# General TIC write message and read response.
	def write_msg(self, message):
		# Writing to the TIC prints random bites. 
		# Write outputs suppressed(?) to avoid this.
		self.emit(QtCore.SIGNAL('block_print'), '')
		time.sleep(.2)
		self.sio.write(unicode(message))
		self.sio.flush()
		self.emit(QtCore.SIGNAL('enable_print'), '')

		# Read response.
		raw_message = self.sio.readline()
		printDebug(raw_message)

		# Parse response.
		try:
			preceding = raw_message[0]
			type = raw_message[1]
			object = raw_message[2:5]
			data = str(raw_message[5:-1])
			data = data.strip()  # removes blank spaces
			terminal = raw_message[-1]

			# Possible errors.
			errors = {
				'0' : 'No error',
				'1' : 'Invalid command for object ID',
				'2' : 'Invalid query/command',
				'3' : 'Missing parameter',
				'4' : 'Parameter out of range',               
				'5' : 'Invalid command in current state',
				'6' : 'Data checksum error',
				'7' : 'EEPROM read or write error',
				'8' : 'Operation took too long',
				'9' : 'Invalid config ID'}

			# Log and print errors and updates.
			if data != '0' and preceding == self.PRECEDING_REPLY:
				if object == self.BACKING_PUMP:
					printError('Backing pump command error ' + data + \
						   ': ' + errors[data])
				elif object == self.nEXT_PUMP:
					printError('Turbo pump error code ' + data + \
						   ': ' + errors[data])
			elif data == '0' and preceding == self.PRECEDING_REPLY:
				if object == self.BACKING_PUMP:
					printInfo('Backing pump command successful.')
				elif object == self.nEXT_PUMP:
					printInfo('Turbo pump command successful.')

			# Return any necessary info.
			elif object == self.GAUGE_1:
				return data.split(';')[0]
			elif object == self.BACKING_PUMP:
				return data.split(';')[0]
			elif object == self.TURBO_PUMP:
				return data.split(';')[0]
		except: 
			printError('No response was received from the TIC Controller.')

	#
	# Pump on/off commands.
	# **Checks add to make sure pressures are within the desired range 
	# before turning off or on each pump. This will have to be changed 
	# once the actuator value is active. Add secondary conditions that 
	# check if the valve is open/closed**
	#
	def Backing_on(self):
		printInfo('Turning backing pump on...')
		self.emit(QtCore.SIGNAL('backing_on'),'')
		self.write_msg(self.backing_on)

	def Backing_off(self):
		if self.pressure_reading > 6 * 1.333 or GUI.vac_valve.Status() == 4:
			printInfo('Turning backing pump off...')
			self.emit(QtCore.SIGNAL('backing_off'),'')
			self.write_msg(self.backing_off)
			
		else:
			printWarning('Pressure too low to turn off backing pump')	
			self.emit(QtCore.SIGNAL('backing_on'),'')
		
	def Backing_status(self):
		printInfo('Checking backing pump status...')
		return self.write_msg(self.backing_check)

	def Turbo_on(self):
		if self.pressure_reading < .005 * 1.333 or GUI.vac_valve.Status() == 4:
			printInfo('Turning turbo pump on...')
			self.emit(QtCore.SIGNAL('turbo_on'),'')
			self.write_msg(self.turbo_on)
			
		else:
			printWarning('Pressure too high to turn on turbo pump, ' \
				     'wait until pressure is < 0.0067 mbar')
			self.emit(QtCore.SIGNAL('turbo_off'),'')

	def Turbo_off(self):
		print self.pressure_reading
		if self.pressure_reading > 1e-6 * 1.333:
			printInfo('Turning turbo pump off...')
			self.emit(QtCore.SIGNAL('turbo_off'),'')
			self.write_msg(self.turbo_off)
			
		else:
			printWarning('Pressure too low to turn off turbo pump, ' \
				     'wait until pressure is > 1.3e-6 mbar')
			self.emit(QtCore.SIGNAL('turbo_on'),'')

	def Turbo_status(self):
		printInfo('Checking turbo pump status...')
		return self.write_msg(self.turbo_check)

	# Read the WR gauge.
	def Gauge_read(self):
		printInfo('Checking pressure...')
		timestamp = mdates.date2num(datetime.datetime.now())
		try:
			pressure_check = self.write_msg(self.gauge_read)
			#
			# **For some reason, the pressure read here is two orders
			# of magnitude greater than what the pressure reads
			# at the controller. **
			#
			pressure_check = float(pressure_check) * 10 ** -2 
			printInfo('Gauge read: %s mbar' %pressure_check)
			return pressure_check, timestamp
		except:
			printError('No response was received from the TIC Controller.')
			pressure_check = ''
			return pressure_check, timestamp

	# Automated pump procedure.
	def Pump_down(self):
		print('Pump_down')
		self.Backing_on()
		while self.pressure_reading > 0.00133:  # ***NEED TO CHANGE TO MBAR**
			print('sleeping back.')
			time.sleep(10)
		self.Turbo_on()
		#
		# Uncomment the following to pump down automatically
		# with the ion pump. "neg pressure" and "ion pressure"
		# are stand ins and will need to be replaced by actual
		# pressure values in mbar.
		#		
		#while self.pressure_reading > neg pressure:
		#	print('sleeping turbo.')
		#	time.sleep(10)
		#self.Neg_on()
		#time.sleep(hour)  # define hour!
		#self.Neg_off()
		#while self.pressure_reading > ion pressure:
		#	print('sleeping ion.')
		#	time.sleep(10)
		#self.Ion_on()

	# Automated vent procedure.
	# To Do: Fix this to issue tic command to open solenoid to vent.
	def Vent(self):		
		self.Turbo_off()
		while self.pressure_reading < 6 * 1.33:
			print('sleeping back.')
			time.sleep(10)
		self.Backing_off()

	# General NEXTorr write message and read response.
	@QtCore.pyqtSlot()
	def write_ion(self, message):
		self.emit(QtCore.SIGNAL('block_print'), '')
		time.sleep(0.2)
		self.sioIon.write(unicode(message))
		self.sioIon.flush()
		self.emit(QtCore.SIGNAL('enable_print'), '')
	
		# Print response.
		raw_message = self.sioIon.readline()
		printDebug(raw_message)
		return raw_message

	#
	# Pump on/off commands:
	# Again, checks in place to make sure pressures are within the 
	# desired range before turning off or on each pump. This will 
	# have to be changed once the actuator value is active. Add 
	# secondary conditions that check if the valve is open/closed.
	#
	@QtCore.pyqtSlot()
	def Ion_on(self):
		if self.pressure_reading < 1e-5 * 1.333:
			printInfo('Turning ion pump on...')
			self.emit(QtCore.SIGNAL('ion_on'), '')
			check = self.write_ion(self.IP_ON)
			if '$' in check:
				printInfo('Ion pump command successful.')
			else:
				printError('Ion pump command error.')
		else:
			printWarning('Pressure too high to turn on ion pump, ' \
				     'wait until pressure is < 1.3e-5 mbar.')
			self.emit(QtCore.SIGNAL('ion_off'), '')

	@QtCore.pyqtSlot()	
	def Ion_off(self):
		print 'Turning ion pump off...'
		self.emit(QtCore.SIGNAL('ion_off'),'')
		check = self.write_ion(self.IP_OFF)
		if '$' in check:
			printInfo('Ion pump command successful.')
		else:
			printError('Ion pump command error.')

	@QtCore.pyqtSlot()
	def Neg_on(self):
		if self.pressure_reading < 1e-4 * 1.333:
			print 'Turning NEG pump on...'
			self.emit(QtCore.SIGNAL('neg_on'), '')
			check = self.write_ion(self.NP_ON)
			if '$' in check:
				printInfo('NEG pump command successful.')
			else:
				printError('NEG pump command error.')
		else:
			printWarning('Pressure too high to turn on NEG pump, ' \
				     'wait until pressure is < 1.3e-4 mbar.')
			self.emit(QtCore.SIGNAL('neg_off'), '')

	@QtCore.pyqtSlot()	
	def Neg_off(self):
		print 'Turning NEG pump off...'
		self.emit(QtCore.SIGNAL('neg_off'),'')
		check = self.write_ion(self.NP_OFF)
		print check
		if '$' in check:
			printInfo('NEG pump command successful.')
		else:
			printError('NEG pump command error.')

	# Status checks and pressure updates.
	@QtCore.pyqtSlot()
	def Ion_status(self):
		printInfo('Checking ion/NEG pump status...')
		status = self.write_ion(self.STATUS)
		ion_status = status.split(',')[0]
		split_status = status.split(',')
		return ion_status, split_status;

	def Ion_gauge(self):
		printInfo('Checking NEXTorr gauge...')
		try:
			status = self.write_ion(self.PRESSURE)
			ion_reading = float(status.rstrip())  # Torr?
			#printInfo('Ion gauge reads: ' + str(ion_reading) + ' Torr')
			ion_reading = ion_reading * 1.333  # mbar
			printInfo('Ion gauge reads: %s mbar' %ion_reading)
			return ion_reading
		except:
			printError('No response was received from the NEXTorr ' \
				   'Power Supply.')
			ion_reading = ''
			return ion_reading

#Start/Run GUI window.
if __name__=='__main__':
	app=QtGui.QApplication(sys.argv)
	GUI=MainUiClass()
	GUI.show()
	ex=LN2_ValveGUI()
	sys.exit(app.exec_())

