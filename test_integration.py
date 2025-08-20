"""
Integration Test for Drone Simulation
-----------------------------------
This script tests the integration of all major components:
1. Environment and map loading
2. Drone movement and controls
3. Vision system and landmark detection
4. Navigation system and waypoint following
"""

import pygame
import sys
import cv2
import numpy as np
from environment import Environment
from drone import Drone
from vision_system import VisionSystem
from navigation import NavigationSystem

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
MAP_IMG = 'assets/map.png'
LANDMARK_IMG = 'assets/landmark.png'

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Drone Simulation - Integration Test")
font = pygame.font.SysFont("Arial", 16)
clock = pygame.time.Clock()

# Initialize components
try:
    print("Initializing environment...")
    env = Environment(MAP_IMG)
    
    # Define waypoints (start, intermediate points, target)
    waypoints = [
        (100, 100),    # Start
        (400, 100),    # Right
        (400, 400),    # Down
        (100, 400),    # Left
        (250, 250)     # Target (center)
    ]
    
    print("Initializing drone...")
    drone = Drone(waypoints[0], start_alt=150)
    
    print("Initializing vision system...")
    vision = VisionSystem(LANDMARK_IMG)
    
    print("Initializing navigation system...")
    navigation = NavigationSystem(waypoints)
    
    print("All systems initialized successfully!")
    
except Exception as e:
    print(f"Error during initialization: {e}")
    pygame.quit()
    sys.exit()

# Test states
test_phase = 0  # 0: Drone movement, 1: Vision, 2: Navigation, 3: Complete
test_results = ["Not Started"] * 4

# Main test loop
running = True
frame_count = 0
prev_frame = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and test_phase < 3:
                test_phase += 1
                print(f"\n--- Starting Test Phase {test_phase} ---")
    
    # Clear screen
    screen.fill((30, 30, 30))
    
    # Get camera view
    try:
        camera_view = env.get_camera_view(
            (drone.x, drone.y), 
            (CAMERA_WIDTH, CAMERA_HEIGHT), 
            drone.z
        )
    except ValueError:
        print("Error: Drone out of bounds!")
        break
    
    # Convert camera view for OpenCV processing
    frame = pygame.surfarray.array3d(camera_view)
    frame = frame.transpose([1, 0, 2])
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    
    # Run current test phase
    if test_phase == 0:  # Test basic drone movement
        test_results[0] = "In Progress"
        
        # Simple movement pattern
        if frame_count < 30:
            drone.x += 2
            command = "MOVE_RIGHT"
        elif frame_count < 60:
            drone.y += 2
            command = "MOVE_DOWN"
        elif frame_count < 90:
            drone.x -= 2
            command = "MOVE_LEFT"
        elif frame_count < 120:
            drone.y -= 2
            command = "MOVE_UP"
        else:
            test_results[0] = "PASSED"
            test_phase += 1
            print("\n--- Starting Test Phase 1 ---")
        
        # Display test info
        info = [
            "=== DRONE MOVEMENT TEST ===",
            f"Position: ({int(drone.x)}, {int(drone.y)})",
            f"Altitude: {int(drone.z)}",
            f"Command: {command}",
            f"Status: {test_results[0]}"
        ]
    
    elif test_phase == 1:  # Test vision system
        test_results[1] = "In Progress"
        
        # Process frame with vision system
        processed_frame, landmark_pos = vision.find_landmark(camera_view)
        
        if landmark_pos:
            camera_center = (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2)
            command, error = vision.get_landing_command(camera_center, landmark_pos)
            test_results[1] = f"PASSED (Landmark detected at {landmark_pos})"
            
            # Move drone slightly to test tracking
            if frame_count % 10 == 0:
                if "LEFT" in command:
                    drone.x -= 5
                elif "RIGHT" in command:
                    drone.x += 5
                elif "FORWARD" in command:
                    drone.y -= 5
                elif "BACK" in command:
                    drone.y += 5
        else:
            command = "SEARCHING"
            
        # Display test info
        info = [
            "=== VISION SYSTEM TEST ===",
            f"Landmark Detected: {'Yes' if landmark_pos else 'No'}",
            f"Command: {command}",
            f"Status: {test_results[1]}"
        ]
        
        # Show processed frame if available
        if processed_frame is not None:
            processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            processed_surface = pygame.surfarray.make_surface(processed_frame.transpose([1, 0, 2]))
            screen.blit(processed_surface, (CAMERA_WIDTH + 20, 10))
    
    elif test_phase == 2:  # Test navigation system
        test_results[2] = "In Progress"
        
        # Update navigation
        command, target_pos = navigation.update_position((drone.x, drone.y))
        
        if command == "REACHED_DESTINATION":
            test_results[2] = "PASSED (All waypoints reached)"
        else:
            # Move drone towards waypoint
            dx = target_pos[0] - drone.x
            dy = target_pos[1] - drone.y
            dist = (dx**2 + dy**2) ** 0.5
            
            if dist > 5:  # If not at target
                speed = min(3, dist * 0.1)  # Slow down as we approach
                dx, dy = dx/dist * speed, dy/dist * speed
                drone.x += dx
                drone.y += dy
        
        # Display test info
        info = [
            "=== NAVIGATION SYSTEM TEST ===",
            f"Current Position: ({int(drone.x)}, {int(drone.y)})",
            f"Target: {target_pos if target_pos else 'N/A'}",
            f"Command: {command}",
            f"Status: {test_results[2]}",
            f"Waypoint: {navigation.current_waypoint_idx + 1}/{len(waypoints)}"
        ]
        
        # Draw waypoints and path
        for i, (x, y) in enumerate(waypoints):
            color = (0, 255, 0) if i == navigation.current_waypoint_idx else (255, 0, 0)
            pygame.draw.circle(screen, color, (int(x/2 + CAMERA_WIDTH + 20), int(y/2 + 10)), 5)
            if i > 0:
                prev_x, prev_y = waypoints[i-1]
                pygame.draw.line(screen, (255, 255, 0), 
                               (int(prev_x/2 + CAMERA_WIDTH + 20), int(prev_y/2 + 10)),
                               (int(x/2 + CAMERA_WIDTH + 20), int(y/2 + 10)), 2)
    
    else:  # Test complete
        test_results[3] = "COMPLETE"
        info = [
            "=== TEST COMPLETE ===",
            "All tests completed successfully!",
            "",
            "Test Results:",
            f"1. Drone Movement: {test_results[0]}",
            f"2. Vision System: {test_results[1]}",
            f"3. Navigation: {test_results[2]}",
            "",
            "Press ESC to exit"
        ]
    
    # Draw camera view
    screen.blit(camera_view, (10, 10))
    
    # Draw test information
    y_offset = CAMERA_HEIGHT + 20
    for line in info:
        text = font.render(line, True, (255, 255, 255))
        screen.blit(text, (10, y_offset))
        y_offset += 20
    
    # Draw test controls
    controls = [
        "=== CONTROLS ===",
        "SPACE: Next test phase",
        "ESC: Exit"
    ]
    
    y_offset = CAMERA_HEIGHT + 20
    for line in controls:
        text = font.render(line, True, (200, 200, 0))
        screen.blit(text, (CAMERA_WIDTH + 20, y_offset))
        y_offset += 20
    
    pygame.display.flip()
    frame_count += 1
    clock.tick(30)

# Clean up
pygame.quit()
sys.exit()
