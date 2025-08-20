# test_movement.py

import pygame
import sys
from drone import Drone # We will use the same Drone class

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Movement Test")
font = pygame.font.SysFont("Arial", 30)
clock = pygame.time.Clock()

# --- Objects ---
# Create a drone instance. Its starting position is (100, 300)
drone = Drone(start_pos=(100, 300), start_alt=0)
print("--- Starting Movement Test ---")
print(f"Initial Position: ({drone.x}, {drone.y})")

# --- Main Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- CORE TEST LOGIC ---
    # On every single frame, we unconditionally tell the drone to move right.
    drone.move("RIGHT")
    
    # --- Drawing ---
    screen.fill((0, 0, 0)) # Black background

    # Draw the drone's current position as text
    pos_text = f"Position: ({drone.x}, {drone.y})"
    text_surface = font.render(pos_text, True, (255, 255, 255)) # White text
    screen.blit(text_surface, (50, 50))
    
    # Draw a simple red circle to represent the drone
    pygame.draw.circle(screen, (255, 0, 0), (drone.x, drone.y), 20)

    # Update the display
    pygame.display.flip()
    
    # Limit the frame rate to 60 FPS to ensure smooth motion
    clock.tick(60)

# --- Cleanup ---
print(f"--- Test Finished ---")
print(f"Final Position: ({drone.x}, {drone.y})")
pygame.quit()
sys.exit()