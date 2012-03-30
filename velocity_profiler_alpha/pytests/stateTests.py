'''
Created on Mar 24, 2012

@author: Devin Schwab
'''
import unittest
from state import State
from msg_alpha.msg._PathSegment import PathSegment as PathSegmentMsg
from geometry_msgs.msg._Point import Point as PointMsg
from geometry_msgs.msg._Twist import Twist as TwistMsg
from tf.transformations import euler_from_quaternion,quaternion_from_euler

import math

class Test(unittest.TestCase):

    def test_init_NoArgs(self):
        testState = State()
        self.assertEqual(testState.pathSeg, None, str(testState.pathSeg) + " is not None")
        self.assertEqual(testState.pathPoint, None, str(testState.pathPoint) + " is not None")
        self.assertEqual(testState.point, None, str(testState.point) + " is not None")
        self.assertEqual(testState.segDistDone, 0.0, str(testState.segDistDone) + " is not 0.0")
        self.assertEqual(testState.dt, 1/20.0, str(testState.dt) + " is not " + str(1/20.0))

    def test_init_PathSeg(self):
        pathSeg = PathSegmentMsg()
        testState = State(pathSeg)
        self.assertEqual(testState.pathSeg, pathSeg, str(testState.pathSeg) + " is not equal to " + str(pathSeg))
        self.assertEqual(testState.pathPoint, pathSeg.ref_point, str(testState.pathPoint) + " is not equal to " + str(pathSeg.ref_point))
        self.assertEqual(testState.point, pathSeg.ref_point, str(testState.point) + " is not equal to " + str(pathSeg.ref_point))
        self.assertEqual(testState.segDistDone, 0.0, str(testState.segDistDone) + " is not 0.0")
        self.assertEqual(testState.dt, 1/20.0, str(testState.dt) + " is not " + str(1/20.0))
    
    def test_init_PathSegAndPoint(self):
        pathSeg = PathSegmentMsg()
        point = PointMsg()
        testState = State(pathSeg, point)
        self.assertEqual(testState.pathSeg, pathSeg, str(testState.pathSeg) + " is not equal to " + str(pathSeg))
        self.assertEqual(testState.pathPoint, pathSeg.ref_point, str(testState.pathPoint) + " is not equal to " + str(pathSeg.ref_point))
        self.assertEqual(testState.point, point, str(testState.point) + " is not equal to " + str(point))
        self.assertEqual(testState.segDistDone, 0.0, str(testState.segDistDone) + " is not 0.0")
        self.assertEqual(testState.dt, 1/20.0, str(testState.dt) + " is not " + str(1/20.0))
        
    def test_init_dt(self):
        testState = State(dt=1/100.0)
        self.assertEqual(testState.pathSeg, None, str(testState.pathSeg) + " is not None")
        self.assertEqual(testState.pathPoint, None, str(testState.pathPoint) + " is not None")
        self.assertEqual(testState.point, None, str(testState.point) + " is not None")
        self.assertEqual(testState.segDistDone, 0.0, str(testState.segDistDone) + " is not 0.0")
        self.assertEqual(testState.dt, 1/100.0, str(testState.dt) + " is not " + str(1/100.0))   
    
    def test_newSegment_None(self):
        point = PointMsg() # initial point
        testState = State(point=point)
        testState.newPathSegment() # putting in a new segment shouldn't overwrite the point by default
        self.assertEqual(testState.pathSeg, None, str(testState.pathSeg) + " is not None")
        self.assertEqual(testState.pathPoint, None, str(testState.pathPoint) + " is not None")
        self.assertEqual(testState.point, point, str(testState.pathPoint) + " is not " + str(point))
        self.assertEqual(testState.segDistDone, 0.0, str(testState.segDistDone) + " is not 0.0")
        self.assertEqual(testState.dt, 1/20.0, str(testState.dt) + " is not " + str(1/20.0))
        
    def test_newSegment_PathSeg(self):
        point = PointMsg()  # initial point
        pathSeg = PathSegmentMsg()
        testState = State(point=point)
        testState.newPathSegment(pathSeg)
        self.assertEqual(testState.pathSeg, pathSeg, str(testState.pathSeg) + " is not " + str(pathSeg))
        self.assertEqual(testState.pathPoint, pathSeg.ref_point, str(testState.pathPoint) + " is not " + str(pathSeg.ref_point))
        self.assertEqual(testState.point, point, str(testState.point) + " is not " + str(point))
        self.assertEqual(testState.segDistDone, 0.0, str(testState.segDistDone) + " is not 0.0")
        self.assertEqual(testState.dt, 1/20.0, str(testState.dt) + " is not " + str(1/20.0))
        
    def test_newSegment_PathSegWithNonZeroDistance(self):
        testState = State() 
        testState.segDistDone = 5.0
        pathSeg = PathSegmentMsg()
        testState.newPathSegment(pathSeg)
        
        self.assertEqual(testState.pathSeg, pathSeg)
        self.assertEqual(testState.pathPoint, pathSeg.ref_point)
        self.assertEqual(testState.point, pathSeg.ref_point)
        self.assertEqual(testState.segDistDone, 0.0)
        self.assertEqual(testState.dt, 1/20.0)
        
    def test_updateState_PerfectLine(self):
        '''
        Test the robot perfectly following a line
        '''
        pathSeg = PathSegmentMsg()
        pathSeg.seg_type = pathSeg.LINE
        pathSeg.seg_number = 1
        pathSeg.seg_length = math.sqrt(2)*2
        
        pathSeg.ref_point.x = 0.0
        pathSeg.ref_point.y = 0.0
        pathSeg.ref_point.z = 0.0
        
        init_quat = quaternion_from_euler(0,0,math.pi/4.0)
        pathSeg.init_tan_angle.w = init_quat[3]
        pathSeg.init_tan_angle.x = init_quat[0]
        pathSeg.init_tan_angle.y = init_quat[1]
        pathSeg.init_tan_angle.z = init_quat[2]
        
        pathSeg.curvature = 0.0
        
        maxSpeed = TwistMsg()
        maxSpeed.linear.x = 1.0
        maxSpeed.angular.z = 1.0
        pathSeg.max_speeds = maxSpeed
        
        minSpeed = TwistMsg()
        pathSeg.min_speeds = minSpeed
              
        pathSeg.accel_limit = 1.0
        pathSeg.decel_limit = -1.0

        state = State(pathSeg)
        
        vel_cmd = TwistMsg()
        vel_cmd.linear.x = 0.5
        vel_cmd.angular.z = 0.0
        
        point = PointMsg()
        
        maxIter = 1000
        count = 1
        # extrapolate next point
        while(state.segDistDone < 1.0 or maxIter < count):
            # create where the robot should have moved
            point.x = pathSeg.seg_length*(count/(maxIter/2.0))*math.cos(math.pi/4.0)
            point.y = pathSeg.seg_length*(count/(maxIter/2.0))*math.sin(math.pi/4.0)
            state.updateState(vel_cmd, point, 0.0)
            count += 1
        
        self.assertTrue(count < maxIter)
        self.assertTrue(state.segDistDone >= 1.0)
    
    def test_updateState_PerfectPosSpin(self):
        '''
        Test the robot perfectly following a spin in place
        with a positive angle
        '''
        self.assertTrue(False)
        
    def test_updateState_PerfectNegSpin(self):
        '''
        Test the robot perfectly following a spin in place
        with a positive angle
        '''
        self.assertTrue(False)
        
    def test_updateState_PerfectPosArc(self):
        '''
        Test the robot perfectly following a positive
        curvature arc
        '''
        pathSeg = PathSegmentMsg()
        pathSeg.seg_type = pathSeg.ARC
        pathSeg.seg_number = 1
        pathSeg.seg_length = math.pi/2
        
        pathSeg.ref_point.x = 0.0
        pathSeg.ref_point.y = 0.0
        
        init_quat = quaternion_from_euler(0,0,3*math.pi/4.0)
        pathSeg.init_tan_angle.w = init_quat[3]
        pathSeg.init_tan_angle.x = init_quat[0]
        pathSeg.init_tan_angle.y = init_quat[1]
        pathSeg.init_tan_angle.z = init_quat[2]
        
        pathSeg.curvature = 1.0
        
        maxSpeed = TwistMsg()
        maxSpeed.linear.x = 1.0
        maxSpeed.angular.z = 1.0
        pathSeg.max_speeds = maxSpeed
        
        minSpeed = TwistMsg()
        pathSeg.min_speeds = minSpeed
              
        pathSeg.accel_limit = 1.0
        pathSeg.decel_limit = -1.0

        state = State(pathSeg)
        
        vel_cmd = TwistMsg()
        vel_cmd.linear.x = 0.5
        vel_cmd.angular.z = 0.0
        
        point = PointMsg()
        
        maxIter = 1000
        count = 1
        
        rhoDes = pathSeg.curvature
        angle = State.getYaw(pathSeg.init_tan_angle)
        r=1/abs(rhoDes)
        startAngle = angle - math.pi/2

        
        # extrapolate next point
        while(state.segDistDone < 1.0 or maxIter < count):
            # create where the robot should have moved
            dAng = pathSeg.seg_length*(count/(maxIter/2.0))*rhoDes
            arcAng = startAngle+dAng
            point.x = pathSeg.ref_point.x + r*math.cos(arcAng)
            point.y = pathSeg.ref_point.y + r*math.sin(arcAng)
            state.updateState(vel_cmd, point, 0.0)
            count += 1
        
        self.assertTrue(count < maxIter)
        self.assertTrue(state.segDistDone >= 1.0)
    
    def test_updateState_PerfectNegArc(self):
        '''
        Test the robot perfectly following a negative
        curvature arc
        '''
        self.assertTrue(False)
        pathSeg = PathSegmentMsg()
        pathSeg.seg_type = pathSeg.ARC
        pathSeg.seg_number = 1
        pathSeg.seg_length = 2*math.pi
        
        pathSeg.ref_point.x = 0.0
        pathSeg.ref_point.y = 0.0
        
        init_quat = quaternion_from_euler(0,0,math.pi/4.0)
        pathSeg.init_tan_angle.w = init_quat[3]
        pathSeg.init_tan_angle.x = init_quat[0]
        pathSeg.init_tan_angle.y = init_quat[1]
        pathSeg.init_tan_angle.z = init_quat[2]
        
        pathSeg.curvature = -1.0
        
        maxSpeed = TwistMsg()
        maxSpeed.linear.x = 1.0
        maxSpeed.angular.z = 1.0
        pathSeg.max_speeds = maxSpeed
        
        minSpeed = TwistMsg()
        pathSeg.min_speeds = minSpeed
              
        pathSeg.accel_limit = 1.0
        pathSeg.decel_limit = -1.0

        state = State(pathSeg)
        
        vel_cmd = TwistMsg()
        vel_cmd.linear.x = 0.5
        vel_cmd.angular.z = 0.0
        
        point = PointMsg()
        
        maxIter = 1000
        count = 1
        
        rhoDes = pathSeg.curvature
        angle = State.getYaw(pathSeg.init_tan_angle)
        r=1/abs(rhoDes)
        if(rhoDes >= 0):
            startAngle = angle - math.pi/2
        else:
            startAngle = angle + math.pi/2

        
        # extrapolate next point
        while(state.segDistDone < 1.0 or maxIter < count):
            # create where the robot should have moved
            dAng = pathSeg.seg_length*(count/(maxIter/2.0))*rhoDes
            arcAng = startAngle+dAng
            point.x = pathSeg.ref_point.x + r*math.cos(arcAng)
            point.y = pathSeg.ref_point.y = r*math.sin(arcAng)
            state.updateState(vel_cmd, point, 0.0)
            count += 1
        
        self.assertTrue(count < maxIter)
        self.assertTrue(state.segDistDone >= 1.0)
        
    def test_updateState_PosOffsetLine(self):
        '''
        Test the robot following a path starting with a positive
        offset and crossing over the path
        '''
        pathSeg = PathSegmentMsg()
        pathSeg.seg_type = pathSeg.LINE
        pathSeg.seg_number = 1
        pathSeg.seg_length = math.sqrt(2)*2
        
        pathSeg.ref_point.x = 0.0
        pathSeg.ref_point.y = 0.0
        pathSeg.ref_point.z = 0.0
        
        init_quat = quaternion_from_euler(0,0,math.pi/4.0)
        pathSeg.init_tan_angle.w = init_quat[3]
        pathSeg.init_tan_angle.x = init_quat[0]
        pathSeg.init_tan_angle.y = init_quat[1]
        pathSeg.init_tan_angle.z = init_quat[2]
        
        pathSeg.curvature = 0.0
        
        maxSpeed = TwistMsg()
        maxSpeed.linear.x = 1.0
        maxSpeed.angular.z = 1.0
        pathSeg.max_speeds = maxSpeed
        
        minSpeed = TwistMsg()
        pathSeg.min_speeds = minSpeed
              
        pathSeg.accel_limit = 1.0
        pathSeg.decel_limit = -1.0

        state = State(pathSeg)
        
        vel_cmd = TwistMsg()
        vel_cmd.linear.x = 0.5
        vel_cmd.angular.z = 0.0
        
        point = PointMsg()
        
        actSegLength = 2.0*math.sqrt(2)+1.0
        
        maxIter = 1000
        count = 1
        # extrapolate next point
        while(state.segDistDone < 1.0 or maxIter < count):
            # create where the robot should have moved
            point.x = actSegLength*(count/(maxIter/2.0))*math.cos(math.pi/8.0)
            point.y = actSegLength*(count/(maxIter/2.0))*math.sin(math.pi/8.0) + 1.0
            state.updateState(vel_cmd, point, 0.0)
            count += 1
        
        self.assertTrue(count < maxIter)
        self.assertTrue(state.segDistDone >= 1.0)
        
    def test_updateState_NegOffsetLine(self):
        '''
        Test the robot following a path starting with a negative
        offset and crossing over the path
        '''
        pathSeg = PathSegmentMsg()
        pathSeg.seg_type = pathSeg.LINE
        pathSeg.seg_number = 1
        pathSeg.seg_length = math.sqrt(2)*2
        
        pathSeg.ref_point.x = 0.0
        pathSeg.ref_point.y = 0.0
        pathSeg.ref_point.z = 0.0
        
        init_quat = quaternion_from_euler(0,0,math.pi/4.0)
        pathSeg.init_tan_angle.w = init_quat[3]
        pathSeg.init_tan_angle.x = init_quat[0]
        pathSeg.init_tan_angle.y = init_quat[1]
        pathSeg.init_tan_angle.z = init_quat[2]
        
        pathSeg.curvature = 0.0
        
        maxSpeed = TwistMsg()
        maxSpeed.linear.x = 1.0
        maxSpeed.angular.z = 1.0
        pathSeg.max_speeds = maxSpeed
        
        minSpeed = TwistMsg()
        pathSeg.min_speeds = minSpeed
              
        pathSeg.accel_limit = 1.0
        pathSeg.decel_limit = -1.0

        state = State(pathSeg)
        
        vel_cmd = TwistMsg()
        vel_cmd.linear.x = 0.5
        vel_cmd.angular.z = 0.0
        
        point = PointMsg()
        
        actSegLength = 2.0*math.sqrt(2)+1.0
        
        maxIter = 1000
        count = 1
        # extrapolate next point
        while(state.segDistDone < 1.0 or maxIter < count):
            # create where the robot should have moved
            point.x = actSegLength*(count/(maxIter/2.0))*math.cos(3*math.pi/4.0) + 1.0
            point.y = actSegLength*(count/(maxIter/2.0))*math.sin(3*math.pi/4.0)
            state.updateState(vel_cmd, point, 0.0)
            count += 1
        
        self.assertTrue(count < maxIter)
        self.assertTrue(state.segDistDone >= 1.0)
        
    def test_updateState_PosOffsetSpin(self):
        '''
        Test the robot following a path starting from an angle with
        a positive offset
        '''
        self.assertTrue(False)
        
    def test_updateState_NegOffsetSpin(self):
        '''
        Test the robot following a path starting from an angle with
        a positive offset
        '''
        self.assertTrue(False)
        
    def test_updateState_PosOffsetArc(self):
        '''
        Test the robot following a path starting from the same angle
        but with a positive offset and larger radius
        '''
        self.assertTrue(False)
        
    def test_updateState_NegOffsetArc(self):
        '''
        Test the robot following a path starting from the same angle
        but with a negative offset and a smaller radius
        '''
        self.assertTrue(False)
        
    def test_stop(self):
        '''
        Test the stop method
        '''
        self.assertTrue(False)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()