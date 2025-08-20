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

# City coordinates on the map (you can add more cities here)
CITY_COORDINATES = {
    'Mumbai': (150, 200),
    'Pune': (250, 250),
    'Nagpur': (400, 300),
    'Kolkata': (600, 400),
    'Delhi': (300, 100),
    'Bangalore': (200, 400),
    'Chennai': (300, 450),
    'Hyderabad': (350, 350),
    'Ahmedabad': (200, 150),
    'Jaipur': (250, 120),
    'Lucknow': (350, 180),
    'Patna': (450, 250),
    'Guwahati': (550, 200),
    'Surat': (180, 180),
    'Indore': (280, 220),
    'Bhopal': (320, 240),
    'Raipur': (380, 280),
    'Bhubaneswar': (500, 320),
    'Ranchi': (480, 280),
    'Varanasi': (420, 220),
    'Kanpur': (380, 200),
    'Agra': (320, 160),
    'Jodhpur': (220, 140),
    'Udaipur': (240, 160),
    'Bikaner': (200, 120),
    'Amritsar': (280, 80),
    'Chandigarh': (300, 90),
    'Dehradun': (320, 110),
    'Shimla': (310, 100),
    'Srinagar': (290, 70),
    'Leh': (270, 60)
}

# Predefined popular routes
PREDEFINED_ROUTES = {
    'Mumbai to Pune': ['Mumbai', 'Pune'],
    'Mumbai to Delhi': ['Mumbai', 'Delhi'],
    'Mumbai to Kolkata': ['Mumbai', 'Pune', 'Nagpur', 'Kolkata'],
    'Delhi to Mumbai': ['Delhi', 'Mumbai'],
    'Delhi to Kolkata': ['Delhi', 'Lucknow', 'Patna', 'Kolkata'],
    'Bangalore to Delhi': ['Bangalore', 'Hyderabad', 'Nagpur', 'Delhi'],
    'Chennai to Mumbai': ['Chennai', 'Bangalore', 'Mumbai'],
    'Kolkata to Mumbai': ['Kolkata', 'Nagpur', 'Pune', 'Mumbai']
}

class CityNavigationSimulation:
    def __init__(self):
        self.current_route = ['Mumbai', 'Pune']  # Default route
        self.waypoints = self.create_waypoints_from_cities(self.current_route)
        
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("City-to-City Drone Navigation Simulation")
        self.font = pygame.font.SysFont("Arial", 20)
        self.clock = pygame.time.Clock()
        
        # Initialize simulation objects
        self.env = Environment(MAP_IMG, LANDMARK_IMG)
        self.start_pos = self.waypoints[0] if self.waypoints else (100, 100)
        self.drone = Drone(start_pos=self.start_pos, start_alt=150)
        self.vision = VisionSystem(LANDMARK_IMG)
        self.navigation = NavigationSystem(self.waypoints) if self.waypoints else None
        
        # Simulation state
        self.current_state = 0  # 0: Navigation, 1: Landing, 2: Completed
        self.prev_frame = None
        self.gray_frame = None
        self.odometry_data = []
        self.running = True
        
        # Place landmark at destination
        if self.waypoints:
            destination_pos = self.waypoints[-1]
            self.env.place_landmark(destination_pos)
            print(f"Destination landmark placed at: {destination_pos}")
    
    def create_waypoints_from_cities(self, city_list):
        """Convert a list of city names to coordinate waypoints"""
        waypoints = []
        for city in city_list:
            if city in CITY_COORDINATES:
                waypoints.append(CITY_COORDINATES[city])
            else:
                print(f"Warning: City '{city}' not found in coordinates. Skipping.")
        
        if len(waypoints) < 2:
            print("Error: Need at least 2 valid cities for a route")
            return None
        
        return waypoints
    
    def change_route(self, new_cities):
        """Change the current route to a new list of cities"""
        if len(new_cities) < 2:
            print("Error: Route must have at least 2 cities")
            return False
        
        # Validate cities exist
        for city in new_cities:
            if city not in CITY_COORDINATES:
                print(f"Error: City '{city}' not found")
                return False
        
        self.current_route = new_cities.copy()
        self.waypoints = self.create_waypoints_from_cities(new_cities)
        
        if self.waypoints:
            # Reset drone to new start position
            self.start_pos = self.waypoints[0]
            self.drone.reset_position(self.start_pos, 150)
            
            # Place landmark at new destination
            destination_pos = self.waypoints[-1]
            self.env.place_landmark(destination_pos)
            
            # Create new navigation system
            self.navigation = NavigationSystem(self.waypoints)
            
            # Reset simulation state
            self.current_state = 0
            
            print(f"Route changed to: {' → '.join(new_cities)}")
            print(f"New waypoints: {self.waypoints}")
            return True
        
        return False
    
    def show_help(self):
        """Display available routes and controls"""
        print("\n=== AVAILABLE ROUTES ===")
        for i, (route_name, cities) in enumerate(PREDEFINED_ROUTES.items(), 1):
            print(f"{i}: {route_name} ({' → '.join(cities)})")
        
        print("\n=== CUSTOM ROUTE ===")
        print("C: Enter custom route")
        print("Example: Mumbai,Pune,Nagpur,Kolkata")
        
        print("\n=== CONTROLS ===")
        print("R: Reset simulation")
        print("H: Show this help")
        print("ESC: Exit simulation")
        print("=====================")
    
    def get_custom_route(self):
        """Get custom route input from user"""
        print("\nEnter custom route (comma-separated cities):")
        print("Available cities:", ", ".join(sorted(CITY_COORDINATES.keys())))
        
        # For simulation purposes, we'll use a default custom route
        # In a real application, you'd get input from the user
        custom_input = "Mumbai,Pune,Nagpur,Kolkata"  # Default example
        print(f"Using example: {custom_input}")
        
        cities = [city.strip() for city in custom_input.split(',')]
        return cities
    
    def handle_events(self):
        """Handle pygame events and user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    # Reset simulation
                    if self.waypoints:
                        self.drone.reset_position(self.waypoints[0], 150)
                        self.navigation.reset_visual_odometry()
                        self.current_state = 0
                        self.odometry_data = []
                        print("Simulation reset!")
                elif event.key == pygame.K_h:
                    # Show help
                    self.show_help()
                elif event.key == pygame.K_c:
                    # Custom route
                    custom_cities = self.get_custom_route()
                    self.change_route(custom_cities)
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                    # Number keys for predefined routes
                    route_index = event.key - pygame.K_1
                    route_names = list(PREDEFINED_ROUTES.keys())
                    if route_index < len(route_names):
                        route_name = route_names[route_index]
                        cities = PREDEFINED_ROUTES[route_name]
                        self.change_route(cities)
    
    def update_navigation(self):
        """Update navigation state and drone movement"""
        if not self.navigation or not self.waypoints:
            return
        
        if self.current_state == 0:  # Navigation
            if not self.navigation.reached_destination:
                # Get navigation command
                command, target_pos = self.navigation.update_position((self.drone.x, self.drone.y))
                
                if command == "REACHED_DESTINATION":
                    self.current_state = 1  # Switch to landing
                    print("Reached final waypoint, switching to landing mode")
                else:
                    # Execute movement command
                    if command in ["MOVE RIGHT", "MOVE LEFT", "MOVE FORWARD", "MOVE BACKWARD"]:
                        new_x, new_y = self.drone.get_next_position(command)
                        self.drone.x, self.drone.y = new_x, new_y
                    
                    # Visual odometry update
                    if self.prev_frame is not None and self.gray_frame is not None:
                        dx, dy, confidence = self.navigation.get_visual_odometry(self.prev_frame, self.gray_frame)
                        if confidence > 0.3:
                            self.odometry_data.append((dx, dy, confidence))
                            if len(self.odometry_data) > 50:
                                self.odometry_data.pop(0)
            else:
                self.current_state = 1  # Switch to landing
        
        elif self.current_state == 1:  # Landing
            if self.env.is_landmark_visible((self.drone.x, self.drone.y), (CAMERA_WIDTH, CAMERA_HEIGHT), self.drone.z):
                # Landmark detected, perform precision landing
                landmark_pos = self.env.get_landmark_position()
                distance = self.env.get_landmark_distance((self.drone.x, self.drone.y))
                
                if distance < 30:  # Very close to landmark
                    if self.drone.z > 10:
                        new_x, new_y = self.drone.get_next_position("DESCEND")
                        self.drone.x, self.drone.y = new_x, new_y
                    else:
                        self.current_state = 2  # Completed
                else:
                    # Approach landmark
                    dx = landmark_pos[0] - self.drone.x
                    dy = landmark_pos[1] - self.drone.y
                    
                    if abs(dx) > 5:
                        if dx > 0:
                            new_x, new_y = self.drone.get_next_position("MOVE RIGHT")
                            self.drone.x, self.drone.y = new_x, new_y
                        else:
                            new_x, new_y = self.drone.get_next_position("MOVE LEFT")
                            self.drone.x, self.drone.y = new_x, new_y
                    elif abs(dy) > 5:
                        if dy < 0:
                            new_x, new_y = self.drone.get_next_position("MOVE FORWARD")
                            self.drone.x, self.drone.y = new_x, new_y
                        else:
                            new_x, new_y = self.drone.get_next_position("MOVE BACKWARD")
                            self.drone.x, self.drone.y = new_x, new_y
                    else:
                        new_x, new_y = self.drone.get_next_position("DESCEND")
                        self.drone.x, self.drone.y = new_x, new_y
            else:
                # Landmark not visible, fall back to navigation
                self.current_state = 0
    
    def draw_interface(self):
        """Draw the simulation interface"""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Draw environment
        self.env.draw(self.screen, (self.drone.x, self.drone.y), self.drone.z)
        
        # Draw drone
        self.drone.draw(self.screen)
        
        if self.navigation:
            nav_info = self.navigation.get_navigation_info()
            
            # Display information
            info_texts = [
                f"Route: {' → '.join(self.current_route)}",
                f"Current City: {self.current_route[self.navigation.current_waypoint_idx] if self.navigation.current_waypoint_idx < len(self.current_route) else 'Destination'}",
                f"Next City: {self.current_route[self.navigation.current_waypoint_idx + 1] if self.navigation.current_waypoint_idx + 1 < len(self.current_route) else 'None'}",
                f"Waypoint: {nav_info['waypoint']}",
                f"Position: ({self.drone.x:.1f}, {self.drone.y:.1f})",
                f"Altitude: {self.drone.z:.1f}",
                f"Speed: {self.drone.velocity:.1f}",
                f"State: {['Navigation', 'Landing', 'Completed'][self.current_state]}"
            ]
            
            # Draw info panel
            y_offset = 10
            for text in info_texts:
                if text:
                    text_surface = self.font.render(text, True, (255, 255, 255))
                    self.screen.blit(text_surface, (10, y_offset))
                    y_offset += 25
            
            # Draw waypoints and city names
            for i, (x, y) in enumerate(self.waypoints):
                color = (0, 255, 0) if i == self.navigation.current_waypoint_idx else (255, 0, 0)
                pygame.draw.circle(self.screen, color, (int(x * 0.5 + 10), int(y * 0.5 + 10)), 5)
                
                # Draw city names
                if i < len(self.current_route):
                    city_name = self.current_route[i]
                    text_surface = self.font.render(city_name, True, (255, 255, 255))
                    self.screen.blit(text_surface, (int(x * 0.5 + 15), int(y * 0.5 + 15)))
                
                # Draw path between waypoints
                if i > 0:
                    pygame.draw.line(self.screen, (0, 255, 255), 
                        (int(self.waypoints[i-1][0] * 0.5 + 10), int(self.waypoints[i-1][1] * 0.5 + 10)),
                        (int(x * 0.5 + 10), int(y * 0.5 + 10)), 2)
            
            # Draw minimap
            minimap_pos = (SCREEN_WIDTH - 200, 10)
            minimap_size = (180, 120)
            self.env.draw_minimap(self.screen, minimap_pos, minimap_size, (self.drone.x, self.drone.y), self.waypoints)
            
            # Draw controls info
            controls_text = [
                "Controls:",
                "1-8: Predefined routes",
                "C: Custom route",
                "R: Reset, H: Help",
                "ESC: Exit"
            ]
            
            y_offset = SCREEN_HEIGHT - 150
            for text in controls_text:
                text_surface = self.font.render(text, True, (200, 200, 200))
                self.screen.blit(text_surface, (SCREEN_WIDTH - 200, y_offset))
                y_offset += 20
    
    def run(self):
        """Main simulation loop"""
        print("=== City-to-City Drone Navigation Simulation ===")
        print("Press H for help and available routes")
        
        while self.running:
            # Handle events
            self.handle_events()
            
            if not self.running:
                break
            
            if not self.navigation or not self.waypoints:
                print("No valid route configured!")
                break
            
            try:
                # Get camera feed from environment
                camera_feed_surface = self.env.get_camera_view(
                    (self.drone.x, self.drone.y), (CAMERA_WIDTH, CAMERA_HEIGHT), self.drone.z)
            except ValueError:
                print("Drone is out of bounds!")
                break
            
            # Convert surface to numpy array for processing
            camera_feed = pygame.surfarray.array3d(camera_feed_surface)
            camera_feed = camera_feed.transpose([1, 0, 2])
            self.gray_frame = cv2.cvtColor(camera_feed, cv2.COLOR_RGB2GRAY)
            
            # Update navigation
            self.update_navigation()
            
            # Update drone physics
            self.drone.update_physics()
            
            # Draw interface
            self.draw_interface()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)
            
            # Update previous frame for visual odometry
            self.prev_frame = self.gray_frame.copy()
        
        # Cleanup
        pygame.quit()
        sys.exit()

def main():
    """Main function to run the simulation"""
    simulation = CityNavigationSimulation()
    simulation.run()

if __name__ == "__main__":
    main() 