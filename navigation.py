import numpy as np
import cv2
import math
from typing import Tuple, Optional

class NavigationSystem:
    def __init__(self, waypoints):
        """
        Initialize the navigation system with a list of waypoints.
        Each waypoint is a tuple of (x, y) coordinates on the map.
        """
        self.waypoints = waypoints
        self.current_waypoint_idx = 0
        self.reached_destination = False
        self.waypoint_threshold = 25  # pixels - tighter for precision
        
        # Visual odometry parameters
        self.orb = cv2.ORB_create(nfeatures=1000)
        self.prev_features = None
        self.prev_descriptors = None
        self.position_estimate = np.array([0.0, 0.0])  # Cumulative position estimate
        
        # Navigation state
        self.navigation_mode = "WAYPOINT"  # WAYPOINT, VISUAL_ODOMETRY, LANDING
        self.visual_odometry_confidence = 0.0
        
        print(f"Navigation system initialized with {len(waypoints)} waypoints")
        
    def update_position(self, current_pos, visual_features=None):
        """
        Update the drone's position and determine the next movement command.
        
        Args:
            current_pos: Tuple of (x, y) current position
            visual_features: Optional visual features for visual odometry
            
        Returns:
            command: String indicating the movement command
            target_pos: The current target waypoint
        """
        if self.reached_destination:
            return "HOLD", None
            
        target_pos = self.waypoints[self.current_waypoint_idx]
        
        # Check if we've reached the current waypoint
        distance = math.dist(current_pos, target_pos)
        if distance < self.waypoint_threshold:
            self.current_waypoint_idx += 1
            if self.current_waypoint_idx >= len(self.waypoints):
                self.reached_destination = True
                print(f"Reached final waypoint! Switching to landing mode.")
                return "REACHED_DESTINATION", None
            target_pos = self.waypoints[self.current_waypoint_idx]
            print(f"Reached waypoint {self.current_waypoint_idx}, moving to next: {target_pos}")
        
        # Calculate direction to the next waypoint
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        
        # Convert to movement command with improved precision
        if abs(dx) > abs(dy):
            if dx > 0:
                command = "MOVE RIGHT"
            else:
                command = "MOVE LEFT"
        else:
            if dy < 0:  # Y is inverted in image coordinates
                command = "MOVE FORWARD"
            else:
                command = "MOVE BACKWARD"
        
        return command, target_pos
    
    def get_visual_odometry(self, prev_frame, current_frame):
        """
        Enhanced visual odometry using feature tracking.
        
        Args:
            prev_frame: Previous camera frame (grayscale)
            current_frame: Current camera frame (grayscale)
            
        Returns:
            dx, dy: Estimated movement in x and y directions
            confidence: Confidence in the movement estimate
        """
        if prev_frame is None:
            return 0, 0, 0.0
        
        # Find keypoints and descriptors
        kp1, des1 = self.orb.detectAndCompute(prev_frame, None)
        kp2, des2 = self.orb.detectAndCompute(current_frame, None)
        
        if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
            return 0, 0, 0.0
            
        # Match features using FLANN
        FLANN_INDEX_LSH = 6
        index_params = dict(algorithm=FLANN_INDEX_LSH,
                           table_number=6,
                           key_size=12,
                           multi_probe_level=1)
        search_params = dict(checks=50)
        matcher = cv2.FlannBasedMatcher(index_params, search_params)
        
        try:
            matches = matcher.knnMatch(des1, des2, k=2)
        except:
            return 0, 0, 0.0
        
        # Apply ratio test for better quality matches
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
        
        if len(good_matches) < 5:
            return 0, 0, 0.0
            
        # Get matching keypoints
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # Estimate movement using RANSAC for robustness
        try:
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if M is not None:
                # Extract translation from homography matrix
                dx = M[0, 2]
                dy = M[1, 2]
                confidence = len(good_matches) / 100.0  # Normalize confidence
                return dx, dy, min(confidence, 1.0)
        except:
            pass
        
        # Fallback to simple average if homography fails
        movement = np.mean(dst_pts - src_pts, axis=0)[0]
        confidence = len(good_matches) / 100.0
        return movement[0], movement[1], min(confidence, 1.0)
    
    def get_navigation_info(self):
        """Get current navigation status information."""
        if self.reached_destination:
            return {
                "mode": "COMPLETED",
                "waypoint": f"{self.current_waypoint_idx}/{len(self.waypoints)}",
                "status": "Destination reached"
            }
        
        target = self.waypoints[self.current_waypoint_idx]
        return {
            "mode": "WAYPOINT",
            "waypoint": f"{self.current_waypoint_idx + 1}/{len(self.waypoints)}",
            "target": target,
            "status": "Navigating to waypoint"
        }
    
    def reset_visual_odometry(self):
        """Reset visual odometry state."""
        self.prev_features = None
        self.prev_descriptors = None
        self.position_estimate = np.array([0.0, 0.0])
        self.visual_odometry_confidence = 0.0
