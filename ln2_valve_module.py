#Code started by Donovan
#Program for operation of the LN2 valve with relay
import RPi.GPIO as GPIO
from PyQt4 import QtGui,QtCore
import sys
import threading
from pexpect import pxssh
import time

#class for valve controlling
class LN2_Valve:
	def __init__(self,PinValve):
		GPIO.setwarnings(False)
		
		self.__pin = PinValve
		self.LN2ValveStatus = False #valve closed, no power through relay
		
		#initialize gpio output and set to low for closed valve
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.__pin,GPIO.OUT)
		GPIO.output(self.__pin,GPIO.LOW)

	#method to open valve
	def Open(self):
		GPIO.output(self.__pin,GPIO.HIGH)
		self.LN2ValveStatus = True #Valve is open

	#Method to close valve
	def Close(self):
		GPIO.output(self.__pin,GPIO.LOW)
		self.LN2ValveStatus = False

	#getter method for valve status
	@property
	def Status(self):
		if self.LN2ValveStatus == True:
			message = 'LN2 Valve is Open'
		else:
			message = 'LN2 Valve is Closed'
		return message

#class to impliment GUI
class LN2_ValveGUI(QtGui.QWidget):
	def __init__(self):
		super(LN2_ValveGUI,self).__init__()
		self.initUI()
		self.ln2v = LN2_Valve(17)
		
		#Temperature sensor
		self.TempThread = QtCore.QThread()
		self.Temp = Temperature()
		self.Temp.moveToThread(self.TempThread)
		self.TempThread.started.connect(self.Temp.run)
		self.TempThread.start()	
		
		self.set_temperature = 20
		#Create thread for overflow
		self.of_event = threading.Event()
		self.overflowThread = threading.Thread(target=self.OverflowThread)
		self.overflowThread.setDaemon(True)
		self.overflowThread.start()

	def initUI(self):
		self.col = QtGui.QColor(0,0,0)

		self.valveb = QtGui.QPushButton("Valve",self)
		self.valveb.setCheckable(True)
		self.valveb.move(10,10)
		self.valveb.clicked[bool].connect(self.BPress)

		self.square = QtGui.QFrame(self)
		self.square.setGeometry(150,20,100,100)
		self.square.setStyleSheet("QWidget { background-color: %s }" % self.col.name())
	
		self.setGeometry(300,300,280,170)
		self.setWindowTitle("Valve Toggle Button")
		self.show()

	#Method to run when the button is pressed
	def BPress(self,pressed):
		if pressed:
			msg = QtGui.QMessageBox.warning(QtGui.QWidget(),'LN2 Message','Please wait for tank to fill. Indicator will change color when complete')
			val = 255
			self.ln2v.Open() #Running the method to open the valve
			Status = self.ln2v.Status #Get the status of the valve
			print(Status) #print status to terminal
			self.of_event.set()
		else: 
			val = 0
			self.ln2v.Close() #method to close the valve
			Status = self.ln2v.Status #get the status of the valve
			print(Status)#print status to terminal
			self.of_event.clear()

		self.col.setRed(val)
		#square will be red when the valve is open and black when closed
		self.square.setStyleSheet("QFrame { background-color: %s }" % self.col.name())

	#Method to close the valve if overflow
	def OverflowThread(self):
		while True:
			self.of_event.wait()
			while self.of_event.isSet():
				temp = self.Temp.get_temp()
				if temp == self.set_temperature:
					if of_event.isSet():
						self.valveb.setChecked(False)
						self.ln2v.Close()
						self.of_event.clear()
						Status = self.ln2v.Status #get the status of the valve
						print(Status)#print status to terminal
	
	#When window is closed
	def closeEvent(self,event):
		self.ln2v.Close()
		pass

class Temperature(QtCore.QThread):
	def __init__(self,parent=None):
		super(Temperature,self).__init__(parent)
		
	def run(self):
		start = time.time()
		self.lnk = pxssh.pxssh()
		hostname = '10.212.212.70'
		username = 'fhire'
		password = 'WIROfhire17'
		self.lnk.login(hostname,username,password)
		end = time.time()
		print('TCMS RPi connected. Time elapsed: '+str('%.2f'%(end-start))+" seconds")
		self.lnk.sendline("cd ~/Desktop/FHiRE-TCS/")
		self.lnk.sendline("python LN2_temp.py")
		
	def end_link(self):
		self.lnk.sendcontrol('c')
		self.lnk.logout()
		
	def get_temp(self):
		self.lnk.sendline('scp LN2Temp.dat fhire@10.212.212.49:/home/fhire/Desktop/FHiRE-vacuum')
		time.sleep(3)
		i = self.lnk.expect('fhire@10.212.212.49\'s password:')
		if i == 0:
			self.lnk.sendline(password)
			time.sleep(3)
		elif i == 1:
			pass
		temp = np.loadtxt('LN2Temp.dat')
		return temp

