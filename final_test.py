# final_test.py

import pygame
import sys
from environment import Environment
from drone import Drone
from vision_system import VisionSystem
import cv2

# --- Initialization ---
print("--- Initializing Pygame and objects... ---")
pygame.init()
screen = pygame.display.set_mode((1200, 800))
font = pygame.font.SysFont("Arial", 24)
try:
    env = Environment('assets/map.png')
    drone = Drone(start_pos=(env.width // 2, env.height // 2), start_alt=150)
    vision = VisionSystem('assets/landmark.png')
except Exception as e:
    print(f"FATAL ERROR during initialization: {e}")
    pygame.quit()
    sys.exit()

print("--- Starting Final Diagnostic Test ---")

# --- Main Loop (will only run for 20 frames) ---
running = True
frame = 0
while running and frame < 20:
    frame += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    print(f"\n--- FRAME {frame} ---")
    
    # 1. Get Camera View
    try:
        camera_feed = env.get_camera_view((drone.x, drone.y), (640, 480), drone.z)
    except ValueError:
        print("ERROR: Drone went out of bounds.")
        running = False
        continue

    # 2. Run Vision System
    processed_frame, landmark_pos = vision.find_landmark(camera_feed)

    # 3. Get Command and Move Drone
    if landmark_pos:
        command, error = vision.get_landing_command((320, 240), landmark_pos)
        print(f"Vision Command Received: '{command}'")
        
        # Check position BEFORE the move call
        print(f"Position BEFORE move: ({drone.x}, {drone.y})")
        
        # Call the move function
        drone.move(command)
        
        # Check position IMMEDIATELY AFTER the move call
        print(f"Position AFTER move:  ({drone.x}, {drone.y})")
    else:
        print("Landmark not found in this frame.")

# --- Cleanup ---
print("\n--- Test complete. ---")
pygame.quit()
sys.exit()