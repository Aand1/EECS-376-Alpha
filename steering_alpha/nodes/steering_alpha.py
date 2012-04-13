#!/usr/bin/env python
# encoding: utf-8

import roslib; roslib.load_manifest('steering_alpha')
import rospy
import tf

from msg_alpha.msg._PathSegment import PathSegment as PathSegmentMsg
from msg_alpha.msg._Obstacles import Obstacles as ObstaclesMsg
from msg_alpha.msg._SegStatus import SegStatus as SegStatusMsg
from geometry_msgs.msg._PoseStamped import PoseStamped as PoseStampedMsg
from geometry_msgs.msg._Twist import Twist as TwistMsg
from nav_msgs.msg._Odometry import Odometry as OdometryMsg

obsExists = False
obsDist = 0
lastOdom = OdometryMsg()
lastMapPose = PoseStampedMsg()
tfl = tf.TransformListener()

def obstaclesCallback(obsData):
    global obsExists, obsDist
    obsExists = obsData.exists
    obsDist = obsData.distance

def odomCallback(odomData):
    global lastOdom,tfl,lastMapPose
    lastOdom = odomData
    temp = PoseStampedMsg()
    temp.pose = lastOdom.pose.pose
    temp.header = lastOdom.header
    try:
        tfl.transformPose("map",temp,lastMapPose)
except tf.TransformException:
        rospy.roserror("Transform Error")

def velCallback(velData):


def pathSegCallback(pathData):


def segStatusCallback(statusData):


if __name__ == '__main__':
    main()

def main():
    rospy.init_node('steering_alpha')
    rospy.Publisher('cmd_vel',TwistMsg)
    rospy.Subscriber('obstacles',ObstaclesMsg,obstaclesCallback)
    rospy.Subscriber('odom',OdometryMsg,odomCallback)
    rospy.Subscriber('des_vel',TwistMsg,velCallback)
    rospy.Subscriber('path_seg',PathSegmentMsg,pathSegCallback)
    rospy.Subscriber('seg_status',SegStatusMsg,segStatusCallback)
    rospy.spin()