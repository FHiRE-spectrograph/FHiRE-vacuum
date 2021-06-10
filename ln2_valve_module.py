#Code started by Donovan
#Program for operation of the LN2 valve with relay
import RPi.GPIO as GPIO
from PyQt4 import QtGui,QtCore
import sys

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

	def initUI(self):
		self.col = QtGui.QColor(0,0,0)

		valveb = QtGui.QPushButton("Valve",self)
		valveb.setCheckable(True)
		valveb.move(10,10)
		valveb.clicked[bool].connect(self.BPress)

		self.square = QtGui.QFrame(self)
		self.square.setGeometry(150,20,100,100)
		self.square.setStyleSheet("QWidget { background-color: %s }" % self.col.name())
	
		self.setGeometry(300,300,280,170)
		self.setWindowTitle("Valve Toggle Button")
		self.show()

	#Method to run when the button is pressed
	def BPress(self,pressed):
		if pressed:
			val = 255
			self.ln2v.Open() #Running the method to open the valve
			Status = self.ln2v.Status #Get the status of the valve
			print(Status) #print status to terminal
		else: 
			val = 0
			self.ln2v.Close() #method to close the valve
			Status = self.ln2v.Status #get the status of the valve
			print(Status)#print status to terminal

		self.col.setRed(val)
		#square will be red when the valve is open and black when closed
		self.square.setStyleSheet("QFrame { background-color: %s }" % self.col.name())
	
	#When window is closed
	def closeEvent(self,event):
		#GPIO.cleanup()
		pass


#method to control and launch the window
#def window():
#	app = QtGui.QApplication(sys.argv)
#	ex = LN2_ValveGUI()
#	sys.exit(app.exec_())
#
#if __name__ == '__main__':
#	
#	#set default variables
#	PinValve = 17 #GPIO17, pin 11
#	#Create the valve object
#	LN2 = ValveControl(PinValve)
#	#Launch the window
#	window()


