import cv2
import numpy as np
import pygame
from typing import Dict, Any

class VisionSystem:
    def __init__(self, landmark_image_path):
        self.landmark_img = cv2.imread(landmark_image_path, 0)
        if self.landmark_img is None:
            raise ValueError(f"Could not load landmark image: {landmark_image_path}")
        
        # Enhanced ORB detector with more features for better matching
        self.orb = cv2.ORB_create(
            nfeatures=2000,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=31,
            firstLevel=0,
            WTA_K=2,
            patchSize=31
        )
        
        # Detect keypoints and compute descriptors for the landmark
        self.kp_landmark, self.des_landmark = self.orb.detectAndCompute(self.landmark_img, None)
        if self.des_landmark is None:
            raise ValueError("No features detected in landmark image")
        
        # Use FLANN matcher for better performance
        FLANN_INDEX_LSH = 6
        index_params: Dict[str, Any] = {
            "algorithm": FLANN_INDEX_LSH,
            "table_number": 6,
            "key_size": 12,
            "multi_probe_level": 1
        }
        search_params: Dict[str, Any] = {"checks": 50}
        self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        
        # Store landmark dimensions for better bounding box calculation
        self.landmark_h, self.landmark_w = self.landmark_img.shape
        
        # Confidence tracking
        self.confidence_threshold = 0.6
        self.min_matches = 15
        
        print(f"Landmark loaded: {self.landmark_w}x{self.landmark_h} pixels")
        print(f"Features detected: {len(self.kp_landmark)}")

    def find_landmark(self, camera_feed_surface):
        """
        Find the landmark in the camera feed using enhanced feature matching.
        
        Returns:
            processed_frame: Frame with bounding box and features drawn
            landmark_pos: (x, y) center position of detected landmark
            confidence: Confidence score of the detection
        """
        # Convert pygame surface to numpy array for OpenCV
        view = pygame.surfarray.array3d(camera_feed_surface)
        view = view.transpose([1, 0, 2])
        view = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)
        gray_view = cv2.cvtColor(view, cv2.COLOR_BGR2GRAY)
        
        # Detect keypoints and compute descriptors
        kp_view, des_view = self.orb.detectAndCompute(gray_view, None)

        if des_view is None or len(des_view) < self.min_matches:
            return view, None, 0.0

        # Match features using FLANN
        try:
            matches = self.matcher.knnMatch(self.des_landmark, des_view, k=2)
        except:
            return view, None, 0.0

        # Apply ratio test for better quality matches
        good_matches = []
        for match_pair in matches:
            if len(match_pair) == 2:
                m, n = match_pair
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)

        if len(good_matches) < self.min_matches:
            return view, None, 0.0

        # Calculate confidence based on match quality
        avg_distance = float(np.mean([m.distance for m in good_matches]))
        confidence = max(0.0, 1.0 - avg_distance / 100.0)
        
        if confidence < self.confidence_threshold:
            return view, None, confidence

        # Get coordinates of matched keypoints
        src_pts = np.float32([self.kp_landmark[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_view[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        # Find homography with RANSAC for robust estimation
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        if M is None:
            return view, None, confidence

        # Transform landmark corners to find bounding box
        pts = np.float32([[0, 0], [0, self.landmark_h - 1], 
                         [self.landmark_w - 1, self.landmark_h - 1], 
                         [self.landmark_w - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        
        # Draw enhanced bounding box and features
        frame_with_box = view.copy()
        
        # Draw bounding box - convert to proper format for OpenCV
        dst_int = dst.astype(np.int32)
        cv2.polylines(frame_with_box, [dst_int], True, (0, 255, 0), 3, cv2.LINE_AA)
        
        # Draw feature matches
        for match in good_matches[:20]:  # Show top 20 matches
            pt1 = tuple(map(int, self.kp_landmark[match.queryIdx].pt))
            pt2 = tuple(map(int, kp_view[match.trainIdx].pt))
            # Draw pt1 on a transparent overlay to avoid drawing outside the image
            if 0 <= pt1[0] < frame_with_box.shape[1] and 0 <= pt1[1] < frame_with_box.shape[0]:
                cv2.circle(frame_with_box, pt1, 3, (255, 0, 0), -1)
            if 0 <= pt2[0] < frame_with_box.shape[1] and 0 <= pt2[1] < frame_with_box.shape[0]:
                cv2.circle(frame_with_box, pt2, 3, (0, 0, 255), -1)
            # Draw line only if both points are within the image
            if (0 <= pt1[0] < frame_with_box.shape[1] and 0 <= pt1[1] < frame_with_box.shape[0] and
                0 <= pt2[0] < frame_with_box.shape[1] and 0 <= pt2[1] < frame_with_box.shape[0]):
                cv2.line(frame_with_box, pt1, pt2, (0, 255, 255), 1)
        # Calculate center of the bounding box
        center_x = int(np.mean(dst[:, 0, 0]))
        center_y = int(np.mean(dst[:, 0, 1]))
        
        # Add confidence text
        cv2.putText(frame_with_box, f"Confidence: {confidence:.2f}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame_with_box, (center_x, center_y), confidence

    def get_landing_command(self, camera_center, landmark_center, threshold=15):
        """
        Generate precise landing commands based on landmark position.
        
        Args:
            camera_center: (x, y) center of camera view
            landmark_center: (x, y) center of detected landmark
            threshold: Pixel threshold for considering centered
            
        Returns:
            command: String command for drone movement
            error: (x_error, y_error) pixel errors
            distance: Distance from center
        """
        # Calculate error vector
        error_x = landmark_center[0] - camera_center[0]
        error_y = landmark_center[1] - camera_center[1]

        # Calculate distance from center
        distance = np.sqrt(error_x**2 + error_y**2)
        
        # Generate movement command with hysteresis
        command = "HOLD"
        
        if abs(error_x) > threshold:
            if error_x > 0:
                command = "MOVE RIGHT"
            else:
                command = "MOVE LEFT"
        elif abs(error_y) > threshold:
            if error_y < 0:  # Y is inverted in image coordinates
                command = "MOVE FORWARD"
            else:
                command = "MOVE BACKWARD"
        else:
            command = "DESCEND"  # We are centered
            
        return command, (error_x, error_y), distance

    def get_landmark_size(self, camera_feed_surface):
        """
        Estimate the apparent size of the landmark for altitude estimation.
        """
        processed_frame, landmark_pos, confidence = self.find_landmark(camera_feed_surface)
        
        if landmark_pos is None:
            return None, None
        
        # This would require more sophisticated processing to get actual size
        # For now, return a basic estimate
        return confidence, None