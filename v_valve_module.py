#Code started by Donovan
#Program for operation of the vacuum valve with relay and solenoid to press the red button
import RPi.GPIO as GPIO
from PyQt4 import QtGui,QtCore
import sys
from time import sleep

class V_Valve:
	def __init__(self,s_pin,c_pin,o_pin):
		self.__solenoid = s_pin
		self.__open = o_pin
		self.__closed = c_pin
		self.__status = 0

		GPIO.setwarnings(False)
		
		#initialize gpio output and set to low for solenoid to be retracted
		GPIO.setmode(GPIO.BCM)
        	GPIO.setup(self.__solenoid,GPIO.OUT)
        	self.sol_pwm = GPIO.PWM(self.__solenoid,100)
        	self.sol_pwm.start(0)
		
		#initialize the gpio input from the micro switches
		GPIO.setup(self.__open,GPIO.IN,pull_up_down = GPIO.PUD_UP) #other end connected to ground since pull up
		GPIO.setup(self.__closed,GPIO.IN,pull_up_down = GPIO.PUD_UP) #other end connected to ground since pull up
		
	#Method to open the Vacuum Valve
	def Push(self):
		#set the solenoid pin to high to extend the solenoid
		self.sol_pwm.ChangeDutyCycle(100)
		#sleep for 1s to allow the button to be pushed (solenoid can not be energized for more than 2s)
		sleep(1)
		#Set the solenoid pin to low to retract the solenoid
		self.sol_pwm.ChangeDutyCycle(0)
		#sleep to wait for the valve to move
		sleep(10)
		
	#method to get the status of the valve
	def Status(self):
		if GPIO.input(self.__open) == 1 and GPIO.input(self.__closed) == 1:
			return 1
		elif GPIO.input(self.__open) == 0 and GPIO.input(self.__closed) == 0:
			return 2
		elif GPIO.input(self.__open) == 0:
			return 3
		elif GPIO.input(self.__closed) == 0:
			return 4
		else:
			pass

	
	
	#set default variables
	#PinSol = 27 #GPIO27
	#PinClose = 5 #GPIO5 Pin 29 pull up
	#PinOpen = 6 #GPIO6 Pin 31 pull up
	#Create the valve object
	#vvalve = V_Valve(PinSol,PinClose,PinOpen)

