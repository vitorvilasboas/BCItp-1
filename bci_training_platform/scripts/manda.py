#!/usr/bin/env python
from __future__ import division
import rospy
import numpy as np
from std_msgs.msg import Float64MultiArray, MultiArrayDimension

def manda():
	rospy.init_node('manda', anonymous=True)
	pub=rospy.Publisher('mecanico', Float64MultiArray, queue_size=1)
	rate = rospy.Rate(1)
	
	m = np.matrix([[1,2,3],[1,1,1]])
	m1=np.array(m).ravel()

	msg = Float64MultiArray()
	msg.data=m1
	#msg.layout.dim.append(dim)
		
	while not rospy.is_shutdown():
		pub.publish(msg)
		
		rate.sleep()

manda()
