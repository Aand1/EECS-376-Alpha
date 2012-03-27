#!/bin/usr/env python
'''
Created on Mar 23, 2012

@author: Devin Schwab
'''

from msg_alpha.msg._PathSegment import PathSegment as PathSegmentMsg
from geometry_msgs.msg._Twist import Twist as TwistMsg
from geometry_msgs.msg._Point import Point as PointMsg
from geometry_msgs.msg._Quaternion import Quaternion as QuaternionMsg
from geometry_msgs.msg._Vector3 import Vector3 as Vector3Msg

from tf.transformations import quaternion_from_euler,euler_from_quaternion # used to convert between the two representations
from math import cos,sin,tan,sqrt,pi,acos,asin

class State:
    """
    This class is responsible for keeping track of the robot's progress along the
    specified path segments.  It does so by integrating velocity commands with the
    assumption the robot is perfectly following the specified path.  It then uses the
    provided position information to calculate the actual path vector.  The projection
    of the actual path vector along the desired path vector is used to determine the
    current position on the path.
    
    Calculating the path in this way means that steering corrections and other perturbations
    shouldn't have a major effect on where velocity profiler thinks it is along a path.
    """
        
    def __init__(self, pathSeg=None, point = None, psi=None, dt=1/20.0):
        """
        Responsible for initializing the State class
        
        Inputs
        ------
        pathSeg is of type PathSegmentMsg
        point is of type PointMsg
        dt is a floating point
        """
        self.pathSeg = pathSeg
        if(pathSeg is not None): # a path segment is already specified
            self.pathPoint = pathSeg.ref_point # the point the robot is projected on the path
            if(point is not None): # a starting point was given
                self.point = point # so set the point to that point
            else: # no starting point was given
                self.point = pathSeg.ref_point # set assume the robot is starting from the path segments beginning
            if(psi is not None): # a starting heading was given
                self.psi = psi
            else:
                self.psi = State.getYaw(pathSeg.init_tan_angle) # assume the robot is aligned with the path
            
            self.v = pathSeg.min_speeds.linear.x
            self.o = pathSeg.min_speeds.angular.z
        else:
            self.psi = psi # doesn't matter if psi is None or defined
            self.point = point # doesn't matter if point is None or defined
            self.pathPoint = None # there is no point along the path because there is no path
            self.v = 0.0
            self.o = 0.0
            
        self.segDistDone = 0.0 # by default the distance done must be zero
        self.dt = dt # set the timestep
        self.segDone = False
        
    
    def newPathSegment(self, pathSeg = None, point = None, psi = None):
        """
        Updates the internal path segment that State is integrating against
        
        Inputs
        ------
        pathSeg is expected to be of type PathSegment
        point is expected to be of type Point
        
        Returns
        -------
        Nothing
        """

        if(point is not None): # if a new point is specified
            self.point = point # then set the state with that point, otherwise leave the point alone
        else: # no point was originally specified
            if(pathSeg is not None): # the new path segment exists
                self.point = pathSeg.ref_point # so assume that the point is at the start of the path segment
        if(psi is not None):
            self.psi = psi
        else:
            if(pathSeg is not None):
                self.psi = State.getYaw(pathSeg.init_tan_angle)
        self.pathSeg = pathSeg # this will be None when
        if(pathSeg is not None): # as long as a path is specified
            self.pathPoint=pathSeg.ref_point # a pathPoint can be assumed
        self.segDistDone = 0.0 # new segment so completion is 0 
        
        print "self.pathSeg: " + str(self.pathSeg)
        print "self.point: " + str(self.point)
        print "self.psi: " + str(self.psi)
        
    
    def updateState(self, vel_cmd, point, psi):
        """
        Integrates along the desired path vector and projects the actual path 
        vector onto the desired vector
        
        Inputs
        ------
        vel_cmd is expected to be of type Twist
        point is expected to be of type Point
        
        Returns
        -------
        True if everything went okay
        False if an error occurred
        """
        
        if(self.pathSeg.seg_type == PathSegmentMsg.LINE):
            # find the normal vector to the line segment
            angle = State.getYaw(self.pathSeg.init_tan_angle)
            normVec = Vector3Msg()
            normVec.x = cos(angle+pi/2.0)
            normVec.y = sin(angle+pi/2.0)
            
            tanVec = Vector3Msg()
            tanVec.x = cos(angle)
            tanVec.y = sin(angle)
            
            # using the point and the normal vector find the intersection of the line through the point and the line
            p0 = self.pathSeg.ref_point
            
            if(normVec.y != 0.0):
                normRatio = normVec.x/normVec.y
                numerator = p0.x - point.y - normRatio*p0.y + normRatio*point.y
                denominator = normRatio*tanVec.y - tanVec.x
                s = numerator/denominator
            else:
                normRatio = normVec.y/normVec.x
                numerator = p0.y - point.y + normRatio*point.x - normRatio*p0.x
                denominator = normRatio*tanVec.x - tanVec.y
                s = numerator/denominator
            
            self.pathPoint = PointMsg()
            self.pathPoint.x = p0.x + tanVec.x*s
            self.pathPoint.y = p0.y + tanVec.y*s
            self.pathPoint.z = 0.0
            
            # using the intersection find the segDistDone
            if(angle % pi != pi/2 or angle % pi != 0.0):
                d1 = (self.pathPoint.x - p0.x)/cos(angle)
                d2 = (self.pathPoint.y - p0.y)/sin(angle)
            elif(angle % pi != pi/2):
                d2 = (self.pathPoint.y - p0.y)/sin(angle)
                d1 = d2
            else:
                d1 = (self.pathPoint.x - p0.x)/cos(angle)
                d2 = d1

            d = (d1+d2)/2.0
                        
            self.segDistDone = d/self.pathSeg.seg_length
       
        # need to redo these
        elif(self.pathSeg.seg_type == PathSegmentMsg.ARC):
            p = point
            rhoDes = self.pathSeg.curvature
            r = 1/abs(rhoDes) # turn radius is inverse of curvature
            angle = State.getYaw(self.pathSeg.init_tan_angle)
            center = PointMsg()
            if(rhoDes >= 0):
                if(angle > 0.0 and angle <= pi/2.0):
                    center.x = -r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = -r*sin(angle) + self.pathSeg.ref_point.y
                elif(angle > pi/2.0 and angle <= pi):
                    center.x = r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = -r*sin(angle) + self.pathSeg.ref_point.y
                elif(angle > pi and angle <= 3.0*pi/2.0):
                    center.x = r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = r*sin(angle) + self.pathSeg.ref_point.y
                else:
                    center.x = -r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = r*sin(angle) + self.pathSeg.ref_point.y
            else:
                if(angle > 0.0 and angle <= pi/2.0):
                    center.x = r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = r*sin(angle) + self.pathSeg.ref_point.y
                elif(angle > pi/2.0 and angle <= pi):
                    center.x = -r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = r*sin(angle) + self.pathSeg.ref_point.y
                elif(angle > pi and angle <= 3.0*pi/2.0):
                    center.x = -r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = -r*sin(angle) + self.pathSeg.ref_point.y
                else:
                    center.x = -r*cos(angle) + self.pathSeg.ref_point.x
                    center.y = r*sin(angle) + self.pathSeg.ref_point.y
                
            # calculate the terms of the quadratic
            a = pow(center.x,2) - 2.0*center.x*p.x + pow(p.x,2) + pow(center.y,2) - 2.0*center.y*p.y + pow(p.y,2)
            b = 2.0*pow(center.x,2) - 4.0*center.x*p.x + 2.0*pow(p.x,2) + 2.0*pow(center.y,2) - 4.0*center.y*p.y + 2.0*pow(p.y,2)
            c = pow(center.x,2) - 2.0*center.x*p.x + pow(p.x,2) + pow(center.y,2) - 2.0*center.y*p.y + pow(p.y,2) - pow(r,2)
            
            # get the two solutions using the quadratic formula
            s1 = (-b + sqrt(pow(b,2) - 4*a*c))/(2*a)
            s2 = (-b - sqrt(pow(b,2) - 4*a*c))/(2*a)
            
            # calculate the point using s1
            p1 = PointMsg()
            p1.x = (p.x - center.x)*s1 + p.x
            p1.y = (p.y - center.y)*s1 + p.y
            
            # calculate the point using s2
            p2 = PointMsg()
            p2.x = (p.x - center.x)*s2 + p.x
            p2.y = (p.y - center.y)*s2 + p.y
            
            # calculate the distance from the point on the circle to the robot position
            s1Dist = sqrt(pow(p1.x-p.x,2) + pow(p1.y-p.y,2))
            s2Dist = sqrt(pow(p2.x-p.x,2) + pow(p2.y-p.y,2))
            
            # set the parameter to the one that minimizes the distance between the circle and the robot position
            if(s1Dist < s2Dist):
                s = s1
                p = p1
            else:
                s = s2
                p = p2
                
            if(rhoDes >= 0):
                arcAngStart = angle-pi/2
            else:
                arcAngStart = angle+pi/2
                
            d1 = (acos((p.x - self.pathSeg.ref_point.x)/r) - arcAngStart)/rhoDes
            d2 = (asin((p.y - self.pathSeg.ref_point.y)/r) - arcAngStart)/rhoDes
            
            d = (d1+d2)/2.0
            
            self.segDistDone = d/self.pathSeg.seg_length
            
        elif(self.pathSeg.seg_type == PathSegmentMsg.SPIN_IN_PLACE):
            yaw = State.getYaw(self.pathSeg.init_tan_angle)
            self.segDistDone = psi - yaw # distance done is the current heading minus the starting heading
        else:
            pass # should probably throw an unknown segment type error
        
        # update the current velocity
        self.v = vel_cmd.linear.x
        self.o = vel_cmd.angular.z
        
        # update the current point and heading
        self.point= point
        self.psi = psi
        
    def stop(self):
        """
        Called when Estop is activated.  Instantly sets the last velocities to 0
        
        Inputs
        ------
        Nothing
        
        Returns
        -------
        Nothing
        """
        self.v = 0.0
        self.o = 0.0
    
    @staticmethod
    def getYaw(quat):
        try:
            return euler_from_quaternion([quat.x,quat.y,quat.z, quat.w])[2]
        except AttributeError:
            return euler_from_quaternion(quat)[2]
    
    @staticmethod
    def createQuat(x,y,z):
        quatList = quaternion_from_euler(x,y,z)
        quat = QuaternionMsg()
        quat.x = quatList[0]
        quat.y = quatList[1]
        quat.z = quatList[2]
        quat.w = quatList[3]
        return quat
    
    @staticmethod
    def createVector(p0,p1):
        vector = Vector3Msg()
        vector.x = p1[0] - p0[0]
        vector.y = p1[1] - p0[1]
        vector.z = p1[2] - p0[2]
        return vector
    
    @staticmethod
    def getUnitVector(vector):
        e = Vector3Msg()
        magnitude = sqrt(pow(vector.x,2) + pow(vector.y,2) + pow(vector.z,2))
        try:
            e.x = vector.x/magnitude
            e.y = vector.y/magnitude
            e.z = vector.z/magnitude
        except ZeroDivisionError:
            e.x = 0.0
            e.y = 0.0
            e.z = 0.0
        return e
    
    @staticmethod
    def dotProduct(vec1, vec2):
        result = 0.0
        result += vec1.x*vec2.x
        result += vec1.y*vec2.y
        result += vec1.z*vec2.z
        return result
    
    
        
