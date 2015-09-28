#!/usr/bin/env python
from __future__ import division
import rospy
import numpy as np
import scipy.signal as sg
from std_msgs.msg import Float64MultiArray,String
num_channels=1

W_lda = np.matrix([1]*349)

msg_to_send = Float64MultiArray()

def callback(msg_received):
	X_lda = np.matrix(msg_received.data)
	X_lda.shape = (num_channels,X_lda.size/num_channels)
	Y_lda = W_lda*X_lda.T
	print(Y_lda)
	#msg_to_send.data=Y_lda.A1
	if Y_lda.A1 < -6:
		pub.publish(data='right')
	else:
		pub.publish(data='up')
	
def lda():
	global pub
	rospy.init_node('lda', anonymous=True)
	rospy.Subscriber('canal4',Float64MultiArray,callback,queue_size=1)
	pub=rospy.Publisher('canal5', String, queue_size=1)
	rospy.spin()

lda()


