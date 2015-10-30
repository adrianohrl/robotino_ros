from enum import *
import rospy
from robotino_leds.srv import *

def ligandoLeds2(colors, terminou, num):
		
	if terminou:
		sinalize = rospy.ServiceProxy('sinalize', Sinalize)
		resp = sinalize(0, colors, num, 2)
	else:
		sinalize = rospy.ServiceProxy('sinalize', Sinalize)
		resp = sinalize(1, colors, num, 2)
	
	rospy.logwarn('Liguei led %s', colors)

def ligandoLeds(colors, terminou):
	
	if terminou:
		sinalize = rospy.ServiceProxy('sinalize', Sinalize)
		resp = sinalize(0, colors, 0, 2)
	else:
		sinalize = rospy.ServiceProxy('sinalize', Sinalize)
		if colors[0] == colors[1]:
			resp = sinalize(1, colors, 2, 2)
		else:
			resp = sinalize(1, colors, 1, 2)
	
	rospy.logwarn('Liguei led %s', colors)

def desligandoLeds():
	
	stop_sinalization = rospy.ServiceProxy('stop_sinalization', Trigger)
	resp = stop_sinalization()
	
	rospy.logwarn('Desliguei led')
