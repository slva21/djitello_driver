#!/usr/bin/env python3 

import rospy
from std_msgs.msg import String
from sensor_msgs.msg import BatteryState, Imu, Range, Image
from std_srvs.srv import Empty as EmptyService
from std_srvs.srv import EmptyResponse as EmptyServiceResponse
from geometry_msgs.msg import Twist
from geometry_msgs.msg import TwistStamped
import geometry_msgs.msg
import cv2
import numpy as np
from cv_bridge import CvBridge
import tf2_ros

from djitellopy import Tello

class TelloDriver:
    def __init__(self):
        rospy.init_node('tello_driver')

        # Initialize Tello object and connect to Tello
        self.tello = Tello()
        self.tello.connect()
        self.frame_id = "tello_base_link"

        # Initialize ROS publishers
        self.battery_pub = rospy.Publisher('tello/battery', BatteryState, queue_size=10)
        self.imu_pub = rospy.Publisher('tello/imu', Imu, queue_size=10)
        self.height_pub = rospy.Publisher('tello/height', Range, queue_size=10)
        self.velocity_pub = rospy.Publisher('tello/velocity', TwistStamped, queue_size=10)
        self.temperature_pub = rospy.Publisher('tello/temperature', String, queue_size=10)
        self.video_pub = rospy.Publisher('/tello/camera', Image, queue_size=1)

        # Create a CvBridge object to convert between ROS images and OpenCV images
        self.bridge = CvBridge()
        # Start Tello video stream
        self.tello.streamon()
        self.frame_read = self.tello.get_frame_read()


        self.command_sub = rospy.Subscriber('/tello/cmd_vel', Twist, self.command_vel_callback)

        # Create new ROS services for takeoff and land commands
        self.takeoff_srv = rospy.Service('/tello/takeoff', EmptyService, self.takeoff_callback)
        self.land_srv = rospy.Service('/tello/land', EmptyService, self.land_callback)

        # Create a TF2 broadcaster
        tf_broadcaster = tf2_ros.StaticTransformBroadcaster()

        # Create a transform message between the "map" and "tello_base" frames
        transform = geometry_msgs.msg.TransformStamped()
        transform.header.frame_id = "world"
        transform.child_frame_id = self.frame_id
        transform.transform.translation.x = 0.0
        transform.transform.translation.y = 0.0
        transform.transform.translation.z = 0.0
        transform.transform.rotation.x = 0.0
        transform.transform.rotation.y = 0.0
        transform.transform.rotation.z = 0.0
        transform.transform.rotation.w = 1.0

        # Publish the transform message
        tf_broadcaster.sendTransform(transform)

        # Set up ROS timer to publish state information at a fixed rate
        self.rate = rospy.Rate(30)  # 10 Hz
       

    def publish_state(self):
        # Get Tello state information
        battery = self.tello.get_battery()
        imu_data_x = self.tello.get_acceleration_x()
        imu_data_y = self.tello.get_acceleration_y()
        imu_data_z = self.tello.get_acceleration_z()
        height = self.tello.get_height()
        velocity_x = self.tello.get_speed_x()
        velocity_y = self.tello.get_speed_y()
        velocity_z = self.tello.get_speed_z()
        temperature = self.tello.get_temperature()
        frame = self.frame_read.frame

        # Publish state information as ROS messages
        battery_msg = BatteryState()
        battery_msg.voltage = battery
        self.battery_pub.publish(battery_msg)

        imu_msg = Imu()
        imu_msg.header.stamp = rospy.Time.now()
        imu_msg.header.frame_id = self.frame_id
        imu_msg.orientation_covariance[0] = -1  # Orientation data not available
        imu_msg.linear_acceleration.x = imu_data_x
        imu_msg.linear_acceleration.y = imu_data_y
        imu_msg.linear_acceleration.z = imu_data_z
        self.imu_pub.publish(imu_msg)

        height_msg = Range()
        height_msg.header.stamp = rospy.Time.now()
        height_msg.header.frame_id = self.frame_id
        height_msg.radiation_type = Range.INFRARED
        height_msg.min_range = 0.1  # Not used for height measurements
        height_msg.max_range = 3.0  # Convert height to meters
        height_msg.range = height / 100.0  # Convert height to meters
        self.height_pub.publish(height_msg)

        velocity_msg = TwistStamped()
        velocity_msg.header.stamp = rospy.Time.now()
        velocity_msg.header.frame_id = self.frame_id
        velocity_msg.twist.linear.x = velocity_x
        velocity_msg.twist.linear.y = velocity_y
        velocity_msg.twist.linear.z = velocity_z
        self.velocity_pub.publish(velocity_msg)

        temperature_msg = String()
        temperature_msg.data = str(temperature)
        self.temperature_pub.publish(temperature_msg)

        # Convert the frame to a ROS image message using CvBridge
        img_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        # Set the timestamp of the image message to the current time
        img_msg.header.stamp = rospy.Time.now()
        # Publish the image message to the video topic
        self.video_pub.publish(img_msg)


    def command_vel_callback(self, twist_msg):
        # Parse the incoming twist message and send the corresponding commands to the Tello
        x = twist_msg.linear.x
        y = twist_msg.linear.y
        z = twist_msg.linear.z
        yaw = twist_msg.angular.z

        self.tello.send_rc_control(int(x*100), int(y*100), int(z*100), int(yaw*100))

    
    def takeoff_callback(self, empty_service):
        self.tello.takeoff()
        return EmptyServiceResponse()

    def land_callback(self, empty_service):
        self.tello.land()
        return EmptyServiceResponse()

    def run(self):
        while not rospy.is_shutdown():
            self.publish_state()
            self.rate.sleep()

        # Stop the video stream and exit the thread
        self.frame_read.stop()


if __name__ == '__main__':
    try:
        driver = TelloDriver()
        driver.run()
    except rospy.ROSInterruptException:
        pass
