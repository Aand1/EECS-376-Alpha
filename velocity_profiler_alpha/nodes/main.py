#!/usr/bin/env python
'''
Created on Mar 22, 2012

@author: Devin Schwab
'''

# Standard ros commands to make a node
import roslib; roslib.load_manifest('velocity_profiler_alpha');
import rospy

# message data types
from geometry_msgs.msg._Twist import Twist as TwistMsg
from geometry_msgs.msg._Point import Point as PointMsg
from std_msgs.msg._Bool import Bool as BoolMsg
from msg_alpha.msg._PathSegment import PathSegment as PathSegmentMsg 
from msg_alpha.msg._Obstacles import Obstacles as ObstaclesMsg 
from msg_alpha.msg._SegStatus import SegStatus as SegStatusMsg
from geometry_msgs.msg._PoseStamped import PoseStamped as PoseStampedMsg

from math import sqrt
from Queue import Queue
from Queue import Empty as QueueEmpty

from state import State

RATE = 20.0 # set the rate of refresh

stopped = False # stores the value of the E-stop

# stores the values of obstacles in the way
obsExists = False
obsDist = 0.0

lastVCmd = 0.0
lastOCmd = 0.0

dV = 0.0

seg_number = 0

pose = PoseStampedMsg()

currState = State()

# true when currSeg and nextSeg have actual values we want to follow
segments = Queue()
currSeg = None
nextSeg = None

ping_angle = 0

def eStopCallback(eStop):
    global stopped
    stopped = not eStop.data

def obstaclesCallback(obsData):
    global obs
    global obsDist
    global obsExists
    global ping_angle
    
    obsExists = obsData.exists
    obsDist = obsData.distance
    ping_angle = obsData.ping_angle

def pathSegmentCallback(seg):
    global segments
    print "received new segment"
    print "\ttype: %i" % seg.seg_type
    print "\tref_point: %s" % seg.ref_point
    print "\t curvature: %s" % seg.curvature
    segments.put(seg,True)

def velCmdCallback(vel):
    global lastVCmd
    global lastOCmd
    lastVCmd = vel.linear.x
    lastOCmd = vel.angular.z

def poseCallback(poseData):
    global pose
    pose = poseData
    #rospy.loginfo("x: %f, y: %f, psi: %f" % (pose.pose.position.x,pose.pose.position.y,State.getYaw(pose.pose.orientation)))

def max_v_w(maxV,maxW,rho):
    v_cmd = abs(maxV);
    w_cmd = abs(rho*v_cmd)
    
    if(abs(w_cmd) > abs(maxW)):
        w_cmd = abs(maxW)
        v_cmd = abs(w_cmd/rho)
        
    v_cmd = cmp(maxV,0)*v_cmd
    w_cmd = cmp(maxW,0)*v_cmd
    return (v_cmd,w_cmd)

def stopForEstop(desVelPub,segStatusPub):
    global RATE
    global currState
    
    currState.stop() # make sure currentState knows the robot is stopped
    
    rospy.loginfo("E-Stop enabled. Pausing...")
    
    des_vel = TwistMsg() # publish 0's for velocity
    desVelPub.publish(des_vel)
    
    publishSegStatus(segStatusPub) # publish the segment status
    
    naptime = rospy.Rate(RATE)

    while(stopped): # stay here until the robot is no longer stopped
        desVelPub.publish(des_vel)
        publishSegStatus(segStatusPub)
        naptime.sleep()
    rospy.loginfo("E-Stop disabled. Taking a quick nap...")
    rospy.sleep(rospy.Duration(1.0)) # sleep for 1 more second to ensure motor controllers are back online
    rospy.loginfo("Good Morning!")

def stopForObs(desVelPub,segStatusPub):
    global obsExists
    global obsDist
    global currState
    global currSeg
    global nextSeg
    global RATE
    global segments
    # calculate the stopping acceleration
    # this is allowed to override the segment constraints, because its more important
    # to not crash than to follow the speed limit

    print "Obstacle detected!"
    dt = 1.0/RATE
    decel_rate = pow(currState.v,2)/(2*(obsDist-1.2))

    
    naptime = rospy.Rate(RATE)
    
    des_vel = TwistMsg()
    
    if(decel_rate > 0):
        while(currState.v-.0001 > 0 or currState.v+.0001 < 0):
            if(not obsExists):
                return # if the obstacle went away then resume without fully stopping
            
            # this should take care of negatives
            if(currState.v > 0):
                v_test = currState.v - decel_rate*dt
                des_vel.linear.x = max(v_test,0.0)
                desVelPub.publish(des_vel)
                currState.updateState(des_vel,pose.pose.position,State.getYaw(pose.pose.orientation))
            
            publishSegStatus(segStatusPub) # let everyone else know the status of the segment
            naptime.sleep()
        des_vel.linear.x = 0.0
        desVelPub.publish(des_vel)
        currState.stop()
    else: # should already be stopped
        desVelPub.publish(des_vel)
        currState.stop()
        publishSegStatus(segStatusPub)
        naptime.sleep()
    
    print "Waiting for obstacle to move..."
    startTime = rospy.Time.now()
    waitPeriod = rospy.Duration(3.0)
    while(obsExists):
        if(rospy.Time.now() - startTime > waitPeriod):
            print "Aborting"
            segments = Queue() # flush the queue, the callback thread probably won't appreciate this
            publishSegStatus(segStatusPub,True) # send the abort flag
            currSeg = None
            nextSeg = None
            break
        else:
            publishSegStatus(segStatusPub)
        naptime.sleep()
    return
            
        

def computeTrajectory(currSeg,nextSeg=None):
    """
    Uses information from the current segment definition and the next segment definition
    to compute the maximum time to accelerate and the maximum time to decelerate.
    The rest of this program will use the trajectories to compute the desired velocity
    and omega commands that best follow the trajectory.
    """
    global RATE
    global dV
    
    dt = 1.0/RATE
    
    if(currSeg.seg_type == PathSegmentMsg.LINE):
        tVAccel = currSeg.max_speeds.linear.x/currSeg.accel_limit
        distVAccel = 0.5*abs(currSeg.accel_limit)*pow(tVAccel,2)
        sVAccel = distVAccel/currSeg.seg_length # the percentage along the path to stop accelerating
        sWAccel = 0.0;
    elif(currSeg.seg_type == PathSegmentMsg.ARC):
        (maxVCmd,maxWCmd) = max_v_w(currSeg.max_speeds.linear.x,currSeg.max_speeds.angular.z,currSeg.curvature)
        
        tVAccel = maxVCmd/currSeg.accel_limit
        distVAccel = 0.5*abs(currSeg.accel_limit)*pow(tVAccel,2)
        sVAccel = distVAccel/currSeg.seg_length
        
        tWAccel = maxWCmd/currSeg.accel_limit
        distWAccel = 0.5*abs(currSeg.accel_limit)*pow(tWAccel,2)
        sWAccel = distWAccel/(currSeg.seg_length/abs(currSeg.curvature))
        
        # velocity and omega have to stay in sync
        # they need to stop accelerating at the same time
        if(sVAccel < sWAccel):
            sWAccel = sVAccel
        else:
            sVAccel = sWAccel
    elif(currSeg.seg_type == PathSegmentMsg.SPIN_IN_PLACE):
        sVAccel = 0.0;
        tWAccel = currSeg.max_speeds.angular.z/currSeg.accel_limit
        distWAccel = 0.5*abs(currSeg.accel_limit)*pow(tWAccel,2)
        sWAccel = distWAccel/currSeg.seg_length
    else: # should maybe make this throw an exception
        return (0.0,0.0,0.0,0.0)
    
    if(nextSeg is None): # if the next seg is None then assume the robot should stop at the end of the segment
        if(currSeg.seg_type == PathSegmentMsg.LINE):
            dV = currSeg.max_speeds.linear.x
            tVDecel = abs(currSeg.max_speeds.linear.x/currSeg.decel_limit)
            distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
            sVDecel = 1-distVDecel/currSeg.seg_length
            
            dW = 0.0
            sWDecel = 1.0
        elif(currSeg.seg_type == PathSegmentMsg.ARC):
            (maxVCmd,maxWCmd) = max_v_w(currSeg.max_speeds.linear.x,currSeg.max_speeds.angular.z,currSeg.curvature)
            
            dV = maxVCmd
            tVDecel = abs(maxVCmd/currSeg.decel_limit)
            distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
            sVDecel = 1.0-distVDecel/currSeg.seg_length
            
            dW = maxWCmd
            tWDecel = abs(maxWCmd/currSeg.decel_limit)
            distWDecel = 0.5*abs(currSeg.decel_limit)*pow(tWDecel,2)
            sWDecel = 1.0-distWDecel/(currSeg.seg_length/abs(currSeg.curvature))
        elif(currSeg.seg_type == PathSegmentMsg.SPIN_IN_PLACE):
            dV = 0.0
            sVDecel = 1.0;
            
            dW = currSeg.max_speeds.angular.z
            tWDecel = abs(currSeg.max_speeds.angular.z/currSeg.decel_limit)
            distWDecel = 0.5*abs(currSeg.decel_limit)*pow(tWDecel,2)
            sWDecel = 1.0-distWDecel/currSeg.seg_length # spin seg lengths are in radians, so no need to divide by the curvature
            #print "dW: %f" % (dW)
        else:
            return (0.0,0.0,0.0,0.0)
    elif(currSeg.seg_type == PathSegmentMsg.LINE and nextSeg.seg_type == PathSegmentMsg.LINE):
        # dV is how much velocity has to change from max to next segment
        if(cmp(currSeg.max_speeds.linear.x,0) >= 0): # positive velocity
            if(currSeg.max_speeds.linear.x <= nextSeg.max_speeds.linear.x):
                dV = 0.0
            elif(cmp(currSeg.max_speeds.linear.x,0) == cmp(nextSeg.max_speeds.linear.x,0)): # if they are the same sign
                dV = currSeg.max_speeds.linear.x - nextSeg.max_speeds.linear.x
            else:
                dV = currSeg.max_speeds.linear.x
        else: # negative velocity
            if(currSeg.max_speeds.linear.x >= nextSeg.max_speeds.linear.x):
                dV = 0.0
            elif(cmp(currSeg.max_speeds.linear.x,0) == cmp(nextSeg.max_speeds.linear.x,0)): # if they are the same sign
                dV = currSeg.max_speeds.linear.x - nextSeg.max_speeds.linear.x
            else:
                dV = currSeg.max_speeds.linear.x
                
        tVDecel = abs(dV/currSeg.decel_limit)
        distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
        sVDecel = 1.0 - distVDecel/currSeg.seg_length
        
        sWDecel = 1.0
    elif(currSeg.seg_type == PathSegmentMsg.LINE and nextSeg.seg_type == PathSegmentMsg.ARC):
        # figure out the maximum v so that w constraint in next segment is not violated
        # currently assuming that a line will not allow any omega
        (maxVCmd,maxWCmd) = max_v_w(nextSeg.max_speeds.linear.x,cmp(nextSeg.max_speeds.angular.z,0)*nextSeg.accel_limit*dt,nextSeg.curvature)
        
        if(abs(maxWCmd) > abs(nextSeg.max_speeds.angular.z)):
            (maxVCmd,maxWCmd) = max_v_w(nextSeg.max_speeds.linear.x,nextSeg.max_speeds.angular.z,nextSeg.curvature)
            
        # dV is how much velocity has to change from max to next segment
        if(currSeg.max_speeds.linear.x <= maxVCmd):
            dV = 0.0
        else:
            if(cmp(maxVCmd,0) == cmp(currSeg.max_speeds.linear.x,0)):
                dV = currSeg.max_speeds.linear.x - maxVCmd
            else:
                dV = currSeg.max_speeds.linear.x
                
        tVDecel = abs(dV/currSeg.decel_limit)
        distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
        sVDecel = 1.0 - distVDecel/currSeg.seg_length
        
        sWDecel = 1.0
    elif(currSeg.seg_type == PathSegmentMsg.ARC and nextSeg.seg_type == PathSegmentMsg.ARC):
        (currVCmd,currWCmd) = max_v_w(currSeg.max_speeds.linear.x, currSeg.max_speeds.angular.z, currSeg.curvature)
        (nextVCmd,nextWCmd) = max_v_w(nextSeg.max_speeds.linear.x, nextSeg.max_speeds.angular.z, nextSeg.curvature)
        
        if(currVCmd <= nextVCmd):
            dV = 0.0
        else:
            if(cmp(currVCmd,0) == cmp(nextVCmd,0)):
                dV = currVCmd - nextVCmd
            else:
                dV = currVCmd
                
        tVDecel = abs(dV/currSeg.decel_limit)
        distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
        sVDecel = 1.0-distVDecel/currSeg.seg_length
        
        if(currWCmd <= nextWCmd):
            dW = 0.0
        else:
            if(cmp(currSeg.curvature,0) == cmp(nextSeg.curvature,0)):
                dW = currWCmd - nextWCmd
            else:
                dW = currWCmd
                
        tWDecel = abs(dW/currSeg.decel_limit)
        distWDecel = 0.5*abs(currSeg.decel_limit)*pow(tWDecel,2)
        sWDecel = 1.0-distWDecel/(currSeg.seg_length/abs(currSeg.curvature))
        
        if(sVDecel > sWDecel):
            sVDecel = sWDecel
        else:
            sWDecel = sVDecel  
    elif(currSeg.seg_type == PathSegmentMsg.ARC and nextSeg.seg_type == PathSegmentMsg.LINE):
        (currVCmd,currWCmd) = max_v_w(currSeg.max_speeds.linear.x, currSeg.max_speeds.angular.z, currSeg.curvature)
        
        if(currVCmd <= nextSeg.max_speeds.linear.x):
            dV = 0.0
        else:
            if(cmp(currVCmd,0) == cmp(nextSeg.max_speeds.linear.x)):
                dV = currVCmd - nextSeg.max_speeds.linear.x
            else:
                dV = currVCmd
                
        tVDecel = abs(dV/currSeg.decel_limit)
        distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
        sVDecel = 1.0-distVDecel/currSeg.seg_length
        
        tWDecel = abs(currWCmd/currSeg.decel_limit)
        distWDecel = 0.5*abs(currSeg.decel_limit)*pow(tWDecel,2)
        sWDecel = 1.0-distWDecel/(currSeg.seg_length/abs(currSeg.curvature))
        
        if(sVDecel > sWDecel):
            sVDecel = sWDecel
        else:
            sWDecel = sVDecel
    elif(currSeg.seg_type == PathSegmentMsg.SPIN_IN_PLACE and nextSeg.seg_type == PathSegmentMsg.SPIN_IN_PLACE):
        
        if(cmp(currSeg.curvature,0) >= 0):
            if(cmp(nextSeg.curvature,0) <= 0):
                dW = currSeg.max_speeds.angular.z
            else:
                if(currSeg.max_speeds.angular.z <= nextSeg.max_speeds.angular.z):
                    dW = 0.0
                else:
                    dW = currSeg.max_speeds.angular.z - nextSeg.max_speeds.angular.z
        else:
            if(cmp(nextSeg.curvature,0) > 0):
                dW = currSeg.max_speeds.angular.z
            else:
                if(currSeg.max_speeds.angular.z >= nextSeg.max_speeds.angular.z):
                    dW = currSeg.max_speeds.angular.z - nextSeg.max_speeds.angular.z
                else:
                    dW = currSeg.max_speeds.angular.z
        
        tWDecel = abs(dW/currSeg.decel_limit)
        distWDecel = 0.5*abs(currSeg.decel_limit)*pow(tWDecel,2)
        sWDecel = 1.0-distWDecel/currSeg.seg_length
        
        dV = 0.0
        sVDecel = 1.0
    else:
        if(currSeg.seg_type == PathSegmentMsg.LINE):
            dV = currSeg.max_speeds.linear.x
            tVDecel = abs(currSeg.max_speeds.linear.x/currSeg.decel_limit)
            distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
            sVDecel = 1-distVDecel/currSeg.seg_length
            
            dW = 0.0
            sWDecel = 1.0
        elif(currSeg.seg_type == PathSegmentMsg.ARC):
            (maxVCmd,maxWCmd) = max_v_w(currSeg.max_speeds.linear.x,currSeg.max_speeds.angular.z,currSeg.curvature)
            
            dV = maxVCmd
            tVDecel = abs(currSeg.max_speeds.linear.x/currSeg.decel_limit)
            distVDecel = 0.5*abs(currSeg.decel_limit)*pow(tVDecel,2)
            sVDecel = 1.0-distVDecel/currSeg.seg_length
            
            dW = maxWCmd
            tWDecel = abs(currSeg.max_speeds.angular.z/currSeg.decel_limit)
            distWDecel = 0.5*abs(currSeg.decel_limit)*pow(tWDecel,2)
            sWDecel = 1.0-distWDecel/(currSeg.seg_length/abs(currSeg.curvature))
        elif(currSeg.seg_type == PathSegmentMsg.SPIN_IN_PLACE):
            dV = 0.0
            sVDecel = 1.0;
            
            dW = currSeg.max_speeds.angular.z
            tWDecel = abs(currSeg.max_speeds.angular.z/currSeg.decel_limit)
            distWDecel = 0.5*abs(currSeg.decel_limit)*pow(tWDecel,2)
            sWDecel = 1-distWDecel/currSeg.seg_length # spin seg lengths are in radians, so no need to divide by the curvature
        else:
            return (0.0,0.0,0.0,0.0)
        
    return (sVAccel,sVDecel,sWAccel,sWDecel)
            

def getVelCmd(sVAccel, sVDecel, sWAccel, sWDecel):
    global currState
    global RATE
    global currSeg
    global dV
    
    dt = 1.0/RATE
    a_max = currState.pathSeg.accel_limit
    d_max = currState.pathSeg.decel_limit
    v_max = currState.pathSeg.max_speeds.linear.x
    w_max = currState.pathSeg.max_speeds.angular.z
    segLength = currState.pathSeg.seg_length
    segDistDone = currState.segDistDone
    
    des_vel = TwistMsg()
    
    if(currState.segDistDone < 1.0):
        if(currState is None):
            return des_vel
        
        #print "seg_type: %i" % (currState.pathSeg.seg_type)
        if(currState.pathSeg.seg_type == PathSegmentMsg.ARC):
            #print "This is an arc"
            (v_max,w_max) = max_v_w(v_max,w_max,currState.pathSeg.curvature)
            
        # figure out the v_cmd
        if(segDistDone < sVDecel):
            #print "V is accelerating or const"
            if(currState.v < v_max):
                #print "V is less than max"
                v_test = currState.v + a_max*dt
                des_vel.linear.x = min(v_test,v_max)
            elif(currState.v > v_max):
                #print "V is greater than max"
                v_test = currState.v - d_max*dt # NOTE: This assumes the d_max is opposite sign of velocity
                des_vel.linear.x = max(v_test,v_max)
            else:
                #print "V is same as max"
                des_vel.linear.x = currState.v
        else:
            #print "V is decelerating"
            v_i = currSeg.max_speeds.linear.x - dV
            v_scheduled = sqrt(2*(1.0-segDistDone)*segLength*d_max + pow(v_i,2))
            if(currState.v > v_scheduled):
                #print "V is greater than scheduled"
                v_test = currState.v - d_max*dt
                des_vel.linear.x = max(v_test,v_max)
            elif(currState.v < v_scheduled):
                #print "v is less than scheduled"
                v_test = currState.v + a_max*dt
                des_vel.linear.x = min(v_test,v_max)
            else:
                #print "v is same as scheduled"
                des_vel.linear.x = currState.v
                
        #print "max_v: %f, max_w: %f" % (v_max,w_max)
        #print "accel_limit: %f, decel_limit: %f" % (currSeg.accel_limit, currSeg.decel_limit)
        #print "sWAccel: %f, sWDecel: %f" % (sWAccel,sWDecel)    
        #print "sVAccel: %f, sVDecel: %f" % (sVAccel,sVDecel)
        #print "segDistDone: %f" % (currState.segDistDone)   
        #print "curvature: %f" % (currSeg.curvature) 
        # figure out the w_cmd
        if(segDistDone < sWDecel):
            #print "Accelerating or Const Velocity"
            if(currSeg.curvature >=0):
                #print "Curvature is positive"
                if(currState.w < w_max):
                    w_test = currState.w + a_max*dt
                    des_vel.angular.z = min(w_test,w_max)
                elif(currState.w > w_max):
                    w_test = currState.w + d_max*dt
                    des_vel.angular.z = max(w_test,w_max)
                else:
                    des_vel.angular.z = currState.w
            else:
                #print "Curvature is negative"
                if(currState.w > -w_max):
                    #print "Going slower than maximum"
                    w_test = currState.w - a_max*dt
                    des_vel.angular.z = max(w_test,-w_max)
                elif(currState.w < -w_max):
                    #print "Going faster than maximum"
                    w_test = currState.w + d_max*dt
                    des_vel.angular.z = min(w_test,-w_max)
                else:
                    #print "Going same speed as maximum"
                    des_vel.angular.z = currState.w
                    
        else:
            #print "Decelerating"
            w_scheduled = sqrt(2*(1.0-segDistDone)*(abs(currState.pathSeg.curvature)/segLength)*d_max)
            if(currSeg.curvature >= 0):
                #print "Curvature is positive"
                if(currState.w > w_scheduled):
                    #print "Going faster than w_scheduled"
                    w_test = currState.w - d_max*dt
                    des_vel.angular.z = min(w_test,w_max)
                elif(currState.w < w_scheduled):
                    #print "Going slower than w_scheduled"
                    w_test = currState.w + a_max*dt
                    des_vel.angular.z = max(w_test,w_max)
                else:
                    #print "Going same speed as w_scheduled"
                    des_vel.angular.z = currState.w
            else:
                #print "Curvature is negative"
                w_scheduled = -w_scheduled
                if(currState.w < w_scheduled):
                    #print "Going faster than w_scheduled"
                    w_test = currState.w - a_max*dt
                    des_vel.angular.z = max(w_test,w_scheduled)
                elif(currState.w > w_scheduled):
                    #print "Going slower than w_scheduled"
                    w_test = currState.w + d_max*dt
                    des_vel.angular.z = min(w_test,w_scheduled)
                else:
                    #print "Going same speed as w_scheduled"
                    des_vel.angular.z = currState.w

    #print des_vel
    return des_vel
        

def publishSegStatus(segStatusPub,abort=False):
    global currState
    
    status = SegStatusMsg()

    if(currState.pathSeg is not None):
        status.seg_number = currState.pathSeg.seg_number
        status.abort = abort
        status.progress_made = currState.segDistDone
        
        if(currState.segDistDone < 1.0):
            status.segComplete = False
        else:
            status.segComplete = True   
        
    segStatusPub.publish(status)

"""
This function is responsible for velocity profiling.  

In general velocity profiler takes in path segments from path publisher
and creates a trajectory based on the segments. The trajectory will smooth
the segments into each other based on the acceleration and velocity 
constraints of the current path segment and the future line segments. 
The velocity and acceleration constraints of the path segment are assumed 
to be slow enough to not cause wheel slip.

Velocity profiler is also in charge of keeping track of how far along the
trajectory the robot actually is.  It creates velocity commands based on where
along the trajectory the robot is. It publishes these commands to the steering node.

Velocity profiler reads in the Obstacles message and checks for obstacles.  If an
obstacle is detected velocity publisher will slow down and stop before hitting the
obstacle.  It will then wait a specified amount of time.  If the obstacle persists
it will send an abort signal through the segStatus message and wait until a new
set of pathSegments is published. If the obstacle is moving after it has completely
stopped it will stay in place until the obstacle starts moving for the specified
time or it moves out of the way.  If the obstacle moves out of the way the
velocity profiler will continue the segments it has.

Velocity Profiler will also stop for an E-stop message.  After the E-stop is 
disabled Velocity Profiler will continue along the specified path segments.
"""
def main():
    global RATE
    global lastVCmd
    global lastOCmd
    global obs
    global obsDist
    global obsExists
    global stopped
    global seg_number
    global currSeg
    global nextSeg
    global pose
    global ping_angle
    
    rospy.init_node('velocity_profiler_alpha')
    desVelPub = rospy.Publisher('des_vel',TwistMsg) # Steering reads this and adds steering corrections on top of the desired velocities
    segStatusPub = rospy.Publisher('seg_status', SegStatusMsg) # Lets the other nodes know what path segment the robot is currently executing
    rospy.Subscriber("motors_enabled", BoolMsg, eStopCallback) # Lets velocity profiler know the E-stop is enabled
    rospy.Subscriber("obstacles", ObstaclesMsg, obstaclesCallback) # Lets velocity profiler know where along the path there is an obstacle 
    rospy.Subscriber("cmd_vel", TwistMsg, velCmdCallback) # 
    rospy.Subscriber("path_seg", PathSegmentMsg, pathSegmentCallback)
    rospy.Subscriber("map_pos", PoseStampedMsg, poseCallback)
    
    naptime = rospy.Rate(RATE)
    
    vel_cmd = TwistMsg()
    point = PointMsg()

    
    # while(not ros.Time.isValid()):
        #pass
    
    print "Entering main loop"
    
    while not rospy.is_shutdown():
        if(currSeg is not None):
         #   print "seg type %i " % currSeg.seg_type
          #  print "ref_point %s " % currSeg.ref_point
           # print "curv %f" % currSeg.curvature
           print "dist done %f" % currState.segDistDone
        if stopped:
            stopForEstop(desVelPub,segStatusPub)
            continue
        if(currSeg is not None):
            # Eventually this should work with arcs, spins and lines, but right
            # now its only working with lines
            if(currSeg.seg_type == PathSegmentMsg.LINE):
                # if there is an obstacle and the obstacle is within the segment length
                print ping_angle
                if(obsExists and obsDist/currSeg.seg_length < 1.0-currState.segDistDone and ping_angle > 60 and ping_angle < 140):
                    stopForObs(desVelPub,segStatusPub)
                    continue
            
            vel_cmd.linear.x = lastVCmd
            vel_cmd.angular.z = lastOCmd
            
            point.x = pose.pose.position.x
            point.y = pose.pose.position.y
            point.z = pose.pose.position.z
            
            currState.updateState(vel_cmd, point, State.getYaw(pose.pose.orientation)) # update where the robot is at
            (sVAccel, sVDecel, sWAccel, sWDecel) = computeTrajectory(currSeg,nextSeg) # figure out the switching points in the trajectory
            
            #print "sVAccel: %f sVDecel: %f" % (sVAccel,sVDecel)
            #print "sWAccel: %f, sWDecel: %f" % (sWAccel,sWDecel)
            
            des_vel = getVelCmd(sVAccel, sVDecel, sWAccel, sWDecel) # figure out the robot commands given the current state and the desired trajectory
            desVelPub.publish(des_vel) # publish the commands
            
            publishSegStatus(segStatusPub) # let everyone else know the status of the segment
            
            # see if its time to switch segments yet
            if(currState.segDistDone > 1.0):
                print "Finished segment type %i" % (currState.pathSeg.seg_type)
                print "currState.segDistDone %f" % (currState.segDistDone)
                currSeg = None
        else:
            # try and get new segments
            if(nextSeg is not None):
                currSeg = nextSeg # move the nextSegment up in line
                nextSeg = None # assume no segment until code below is run
            else: # didn't have a next segment before
                try: # so try and get a new one from the queue
                    currSeg = segments.get(False)
                except QueueEmpty: # if the queue is still empty then 
                    currSeg = None # just set it to None
                
            try: # see if a next segment is specified
                nextSeg = segments.get(False) # try and get it
            except QueueEmpty: # if nothing specified
                nextSeg = None # set to None
            
            point = PointMsg()
            point.x = pose.pose.position.x
            point.y = pose.pose.position.y
            point.z = pose.pose.position.z
            
            currState.newPathSegment(currSeg, point, pose.pose.orientation)
            des_vel = TwistMsg()
            desVelPub.publish(des_vel) # publish all zeros for the des_vel
            publishSegStatus(segStatusPub) # publish that there is no segment
            if(currSeg is not None):
                rospy.logwarn("Starting a new segment, type %i" %currSeg.seg_type)
                rospy.logwarn("\tcurvature: %f" % currSeg.curvature)
                rospy.logwarn("\tref_point: %s" % currSeg.ref_point)
        naptime.sleep()
        continue

    
if __name__ == "__main__":
    main()
    
    
