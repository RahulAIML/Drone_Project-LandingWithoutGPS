import pygame
import sys
import cv2
import numpy as np
from environment import Environment
from drone import Drone
from vision_system import VisionSystem
from navigation import NavigationSystem

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 1400, 900
CAMERA_WIDTH, CAMERA_HEIGHT = 640, 480
MAP_IMG = 'assets/map.png'
LANDMARK_IMG = 'assets/landmark.png'

# Enhanced navigation waypoints for Phase 2 demonstration
WAYPOINTS = [
    (100, 100),    # Start point
    (300, 100),    # First waypoint
    (300, 300),    # Second waypoint
    (500, 300),    # Third waypoint
    (500, 380),    # Landmark approach waypoint (very close to landmark)
    (500, 400)     # Final landmark position
]

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Autonomous Drone Navigation & Landing Simulation - Phase 1 & 2")
font = pygame.font.SysFont("Arial", 20)
clock = pygame.time.Clock()

# --- Objects ---
env = Environment(MAP_IMG, LANDMARK_IMG)
start_pos = WAYPOINTS[0]
drone = Drone(start_pos=start_pos, start_alt=150)
print(f"Drone initialized at: ({drone.x}, {drone.y}), Alt: {drone.z}")

# Place landmark on the map (you can change this position)
landmark_pos = (500, 400)  # Place landmark at a strategic location
env.place_landmark(landmark_pos)
print(f"Landmark placed at: {landmark_pos}")

# Initialize enhanced systems
vision = VisionSystem(LANDMARK_IMG)
navigation = NavigationSystem(WAYPOINTS)

# State machine states
STATE_NAVIGATION = 0
STATE_LANDING = 1
STATE_COMPLETED = 2
current_state = STATE_NAVIGATION

# For visual odometry
prev_frame = None
odometry_data = []

# Performance tracking
frame_count = 0
start_time = pygame.time.get_ticks()

# --- Main Loop ---
running = True
while running:
    frame_count += 1
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Reset simulation
                drone.reset_position(start_pos, 150)
                navigation.reset_visual_odometry()
                current_state = STATE_NAVIGATION
                odometry_data = []
                print("Simulation reset!")

    try:
        # Get camera feed from environment
        camera_feed_surface = env.get_camera_view(
            (drone.x, drone.y), (CAMERA_WIDTH, CAMERA_HEIGHT), drone.z)
    except ValueError:
        print("Drone is out of bounds!")
        running = False
        continue
    
    # Convert surface to numpy array for processing
    camera_feed = pygame.surfarray.array3d(camera_feed_surface)
    camera_feed = camera_feed.transpose([1, 0, 2])
    gray_frame = cv2.cvtColor(camera_feed, cv2.COLOR_RGB2GRAY)
    
    command_text = ""
    processed_frame = None
    landmark_detected = False
    
    # State machine for navigation and landing
    if current_state == STATE_NAVIGATION:
        # Phase 2: Long-Range Visual Navigation
        command, target_pos = navigation.update_position((drone.x, drone.y))
        
        if command == "REACHED_DESTINATION":
            print("Reached final waypoint, switching to landing mode")
            current_state = STATE_LANDING
            command_text = "LANDING MODE: Searching for landmark..."
        else:
            # Move drone based on navigation command
            next_x, next_y = drone.get_next_position(command)
            drone.x, drone.y = next_x, next_y
            command_text = f"NAV: {command} | Target: {target_pos}"
            
            # Enhanced visual odometry for Phase 2
            if prev_frame is not None:
                dx, dy, confidence = navigation.get_visual_odometry(prev_frame, gray_frame)
                if confidence > 0.3:  # Only use high-confidence estimates
                    odometry_data.append((dx, dy, confidence))
                    if len(odometry_data) > 10:  # Keep last 10 estimates
                        odometry_data.pop(0)
            
            # Check if we can see the landmark on the map (primary method)
            landmark_distance = env.get_landmark_distance((drone.x, drone.y))
            if landmark_distance < 100:  # Landmark is close enough to switch to landing
                print(f"Landmark detected on map at distance: {landmark_distance:.1f}")
                current_state = STATE_LANDING
                command_text = "LANDING MODE: Landmark detected on map!"
            
            # Also check if we can see the landmark in camera feed during navigation (secondary method)
            processed_frame, landmark_pos, confidence = vision.find_landmark(camera_feed_surface)
            if landmark_pos and confidence > 0.6:
                camera_center = (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2)
                _, error, distance = vision.get_landing_command(camera_center, landmark_pos)
                if distance < 80:  # Landmark is close enough to switch to landing
                    print("Landmark detected in camera during navigation, switching to landing mode")
                    current_state = STATE_LANDING
    
    elif current_state == STATE_LANDING:
        # Phase 1: Precision Landing Prototype
        processed_frame, landmark_pos, confidence = vision.find_landmark(camera_feed_surface)
        
        if landmark_pos and confidence > 0.5:
            landmark_detected = True
            camera_center = (CAMERA_WIDTH // 2, CAMERA_HEIGHT // 2)
            command, error, distance = vision.get_landing_command(camera_center, landmark_pos)
            command_text = f"LANDING: {command} | Error: ({error[0]:.1f}, {error[1]:.1f}) | Dist: {distance:.1f}"
            
            # Move drone based on landing command
            next_x, next_y = drone.get_next_position(command)
            drone.x, drone.y = next_x, next_y
            
            # Descend if we're centered
            if command == "DESCEND":
                drone.z -= drone.descent_speed
                if drone.z <= drone.landing_altitude:
                    current_state = STATE_COMPLETED
                    print("LANDING COMPLETED SUCCESSFULLY!")
        else:
            # If we can't see the landmark in camera, use map-based guidance
            landmark_distance = env.get_landmark_distance((drone.x, drone.y))
            if landmark_distance < 50:  # Very close to landmark
                command_text = "LANDING: Very close to landmark - attempting final approach..."
                # Try to center over the landmark using map coordinates
                landmark_pos = env.get_landmark_position()
                if landmark_pos:
                    dx = landmark_pos[0] - drone.x
                    dy = landmark_pos[1] - drone.y
                    if abs(dx) > 5:
                        command = "MOVE RIGHT" if dx > 0 else "MOVE LEFT"
                        next_x, next_y = drone.get_next_position(command)
                        drone.x, drone.y = next_x, next_y
                    elif abs(dy) > 5:
                        command = "MOVE FORWARD" if dy < 0 else "MOVE BACKWARD"
                        next_x, next_y = drone.get_next_position(command)
                        drone.x, drone.y = next_x, next_y
                    else:
                        # We're centered, descend
                        drone.z -= drone.descent_speed
                        if drone.z <= drone.landing_altitude:
                            current_state = STATE_COMPLETED
                            print("LANDING COMPLETED SUCCESSFULLY!")
            else:
                command_text = f"LANDING: Lost sight of landmark - searching... Distance: {landmark_distance:.1f}"
                # Try to reacquire landmark by moving slowly towards last known position
                if drone.velocity > drone.min_velocity:
                    drone.velocity = drone.min_velocity
                
                # Move towards landmark if we know where it is
                landmark_pos = env.get_landmark_position()
                if landmark_pos:
                    dx = landmark_pos[0] - drone.x
                    dy = landmark_pos[1] - drone.y
                    if abs(dx) > abs(dy):
                        command = "MOVE RIGHT" if dx > 0 else "MOVE LEFT"
                    else:
                        command = "MOVE FORWARD" if dy < 0 else "MOVE BACKWARD"
                    
                    next_x, next_y = drone.get_next_position(command)
                    drone.x, drone.y = next_x, next_y
    
    elif current_state == STATE_COMPLETED:
        command_text = "MISSION COMPLETED: Drone successfully landed on target!"
        if drone.is_landed:
            command_text += " - DRONE LANDED!"
    
    # Store current frame for next iteration's visual odometry
    prev_frame = gray_frame

    # --- Drawing ---
    screen.fill((25, 25, 35))
    
    # Draw camera feed (left panel)
    screen.blit(camera_feed_surface, (10, 10))
    
    # Draw processed frame with vision data (right panel)
    if processed_frame is not None:
        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        processed_surface = pygame.surfarray.make_surface(processed_frame.transpose([1, 0, 2]))
        screen.blit(processed_surface, (10 + CAMERA_WIDTH + 20, 10))
    
    # Draw drone status panel (bottom)
    drone_status = drone.get_status()
    nav_info = navigation.get_navigation_info()
    
    # Get landmark information
    landmark_distance = env.get_landmark_distance((drone.x, drone.y))
    landmark_pos = env.get_landmark_position()
    
    status_lines = [
        f"State: {'NAVIGATION' if current_state == STATE_NAVIGATION else 'LANDING' if current_state == STATE_LANDING else 'COMPLETED'}",
        f"Position: ({drone_status['position'][0]}, {drone_status['position'][1]})",
        f"Altitude: {drone_status['position'][2]}",
        f"Velocity: {drone_status['velocity']}",
        f"Battery: {drone_status['battery']}% ({drone_status['battery_status']})",
        f"Waypoint: {nav_info['waypoint']}",
        f"Status: {nav_info['status']}",
        f"Landmark: {landmark_pos if landmark_pos else 'Not placed'}",
        f"Distance to Landmark: {landmark_distance:.1f} pixels" if landmark_pos else "Landmark: Not available",
        f"Command: {command_text[:50]}"  # Truncate long commands
    ]
    
    for i, line in enumerate(status_lines):
        color = (255, 255, 255) if i < 4 else (200, 200, 200)
        text_surface = font.render(line, True, color)
        screen.blit(text_surface, (10, CAMERA_HEIGHT + 20 + i * 25))
    
    # Draw visual odometry data (if available)
    if odometry_data:
        vo_text = f"Visual Odometry: {len(odometry_data)} samples"
        vo_surface = font.render(vo_text, True, (0, 255, 255))
        screen.blit(vo_surface, (10, CAMERA_HEIGHT + 200))
    
    # Draw waypoints on the map (for debugging)
    for i, (x, y) in enumerate(WAYPOINTS):
        color = (0, 255, 0) if i == 0 else (255, 0, 0)
        pygame.draw.circle(screen, color, (int(x * 0.5 + 10), int(y * 0.5 + 10)), 5)
        if i > 0:
            pygame.draw.line(screen, (255, 0, 0), 
                           (int(WAYPOINTS[i-1][0] * 0.5 + 10), int(WAYPOINTS[i-1][1] * 0.5 + 10)),
                           (int(x * 0.5 + 10), int(y * 0.5 + 10)), 1)
    
    # Draw minimap in top-right corner
    minimap_size = (200, 150)
    minimap_pos = (SCREEN_WIDTH - minimap_size[0] - 10, 10)
    
    # Update drone heading for minimap
    env.drone_heading = drone.heading
    
    env.draw_minimap(screen, minimap_pos, minimap_size, (drone.x, drone.y), WAYPOINTS)
    
    # Draw performance info
    fps = clock.get_fps()
    elapsed = (current_time - start_time) / 1000.0
    perf_text = f"FPS: {fps:.1f} | Time: {elapsed:.1f}s | Frames: {frame_count}"
    perf_surface = font.render(perf_text, True, (150, 150, 150))
    screen.blit(perf_surface, (SCREEN_WIDTH - 300, 10))
    
    # Draw instructions
    instructions = [
        "Controls: R = Reset, ESC = Quit",
        "Phase 1: Precision Landing | Phase 2: Visual Navigation"
    ]
    for i, instruction in enumerate(instructions):
        inst_surface = font.render(instruction, True, (100, 100, 100))
        screen.blit(inst_surface, (10, SCREEN_HEIGHT - 40 + i * 20))
    
    pygame.display.flip()
    clock.tick(60)

# --- Cleanup ---
pygame.quit()
sys.exit()