import pygame
import numpy as np
import cv2

class Environment:
    def __init__(self, map_image_path, landmark_image_path=None):
        """
        Initialize the environment with a map image and optional landmark.
        
        Args:
            map_image_path: Path to the map image file
            landmark_image_path: Path to the landmark image file
        """
        try:
            # Load the map image
            self.map = pygame.image.load(map_image_path).convert_alpha()
            # Create a copy for drawing
            self.original_map = self.map.copy()
            # For OpenCV processing
            self.map_cv = cv2.imread(map_image_path, cv2.IMREAD_COLOR)
            if self.map_cv is None:
                raise FileNotFoundError(f"Could not load map image: {map_image_path}")
                
        except (pygame.error, FileNotFoundError) as e:
            print(f"FATAL ERROR: Could not load map image at '{map_image_path}'")
            print(f"Error: {e}")
            print("Please make sure the file exists and is in the correct 'assets' folder.")
            pygame.quit()
            exit()
            
        self.width, self.height = self.map.get_size()
        print(f"Map loaded successfully. Dimensions: {self.width}x{self.height}")
        
        # Landmark placement and detection
        self.landmark_image = None
        self.landmark_position = None
        self.landmark_size = (50, 50)  # Default landmark size on map
        
        if landmark_image_path:
            self.load_landmark(landmark_image_path)
        
        # For visual effects
        self.fog_of_war = None
        self.initialize_fog_of_war()
        
    def load_landmark(self, landmark_image_path):
        """Load and place landmark on the map."""
        try:
            self.landmark_image = pygame.image.load(landmark_image_path).convert_alpha()
            # Scale landmark to appropriate size for the map
            self.landmark_image = pygame.transform.scale(self.landmark_image, self.landmark_size)
            print(f"Landmark loaded successfully. Size: {self.landmark_size}")
        except pygame.error as e:
            print(f"Warning: Could not load landmark image: {e}")
            self.landmark_image = None
    
    def place_landmark(self, position):
        """Place the landmark at a specific position on the map."""
        if self.landmark_image:
            self.landmark_position = position
            print(f"Landmark placed at position: {position}")
            return True
        return False
    
    def place_landmark_at_center(self):
        """Place landmark at the center of the map."""
        center_x = self.width // 2
        center_y = self.height // 2
        return self.place_landmark((center_x, center_y))
    
    def get_landmark_position(self):
        """Get the current landmark position on the map."""
        return self.landmark_position
    
    def is_landmark_visible(self, drone_position, camera_size, drone_altitude):
        """Check if the landmark is visible from the drone's current position."""
        if not self.landmark_position:
            return False
            
        # Calculate camera view area
        zoom_factor = drone_altitude / 100.0
        zoom_factor = max(0.1, min(2.0, zoom_factor))
        
        view_width = int(camera_size[0] / zoom_factor)
        view_height = int(camera_size[1] / zoom_factor)
        
        # Calculate view rectangle centered on drone
        x, y = drone_position
        view_x = max(0, min(self.width - view_width, x - view_width//2))
        view_y = max(0, min(self.height - view_height, y - view_height//2))
        
        # Check if landmark is within the camera view
        landmark_x, landmark_y = self.landmark_position
        return (view_x <= landmark_x <= view_x + view_width and 
                view_y <= landmark_y <= view_y + view_height)
    
    def get_landmark_distance(self, drone_position):
        """Calculate distance from drone to landmark."""
        if not self.landmark_position:
            return float('inf')
        
        dx = drone_position[0] - self.landmark_position[0]
        dy = drone_position[1] - self.landmark_position[1]
        return np.sqrt(dx*dx + dy*dy)
        
    def initialize_fog_of_war(self):
        """Initialize the fog of war effect."""
        # Create a black surface with some transparency
        self.fog_of_war = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.fog_of_war.fill((0, 0, 0, 200))  # Semi-transparent black
        
    def reveal_area(self, position, radius):
        """
        Reveal an area in the fog of war.
        
        Args:
            position: (x, y) center of the area to reveal
            radius: radius of the revealed area
        """
        if self.fog_of_war is None:
            return
            
        # Create a temporary surface with a hole
        temp_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(temp_surf, (0, 0, 0, 0), (radius, radius), radius)
        
        # Blit the hole onto the fog of war
        x, y = int(position[0] - radius), int(position[1] - radius)
        self.fog_of_war.blit(temp_surf, (x, y), special_flags=pygame.BLEND_RGBA_MULT)

    def get_camera_view(self, drone_position, camera_size, drone_altitude):
        """
        Generate a camera view from the drone's perspective.
        
        Args:
            drone_position: (x, y) position of the drone
            camera_size: (width, height) of the camera view
            drone_altitude: current altitude of the drone
            
        Returns:
            pygame.Surface: The camera view
        """
        # Ensure altitude is reasonable
        if drone_altitude < 10:
            drone_altitude = 10
            
        # Calculate zoom factor based on altitude (higher altitude = wider view)
        zoom_factor = drone_altitude / 100.0
        zoom_factor = max(0.1, min(2.0, zoom_factor))  # Clamp zoom factor
        
        # Calculate view size (inverse of zoom)
        view_width = int(camera_size[0] / zoom_factor)
        view_height = int(camera_size[1] / zoom_factor)
        
        # Calculate view rectangle centered on drone
        x, y = drone_position
        view_x = max(0, min(self.width - view_width, x - view_width//2))
        view_y = max(0, min(self.height - view_height, y - view_height//2))
        
        # Create the view rectangle
        view_rect = pygame.Rect(view_x, view_y, view_width, view_height)
        
        try:
            # Get the subsurface and scale it to camera size
            cropped = self.map.subsurface(view_rect)
            camera_feed = pygame.transform.scale(cropped, camera_size)
            
            # Add landmark to the camera view if it's visible
            if self.landmark_image and self.landmark_position:
                # Calculate landmark position in camera view coordinates
                landmark_x, landmark_y = self.landmark_position
                if (view_x <= landmark_x <= view_x + view_width and 
                    view_y <= landmark_y <= view_y + view_height):
                    
                    # Convert map coordinates to camera view coordinates
                    cam_x = int((landmark_x - view_x) * camera_size[0] / view_width)
                    cam_y = int((landmark_y - view_y) * camera_size[1] / view_height)
                    
                    # Scale landmark for camera view
                    landmark_cam_size = (int(self.landmark_size[0] * camera_size[0] / view_width),
                                       int(self.landmark_size[1] * camera_size[1] / view_height))
                    landmark_cam = pygame.transform.scale(self.landmark_image, landmark_cam_size)
                    
                    # Position landmark in camera view
                    landmark_rect = landmark_cam.get_rect()
                    landmark_rect.center = (cam_x, cam_y)
                    camera_feed.blit(landmark_cam, landmark_rect)
                    
                    # Draw a highlight circle around the landmark
                    pygame.draw.circle(camera_feed, (0, 255, 0), (cam_x, cam_y), 
                                     max(landmark_cam_size) // 2 + 5, 3)
            
            # Apply visual effects based on altitude
            if drone_altitude < 50:  # Low altitude effects
                # Darken the edges (vignette)
                vignette = pygame.Surface(camera_size, pygame.SRCALPHA)
                center_x, center_y = camera_size[0] // 2, camera_size[1] // 2
                max_dist = (center_x**2 + center_y**2) ** 0.5
                
                for i in range(camera_size[0]):
                    for j in range(camera_size[1]):
                        dist = ((i - center_x)**2 + (j - center_y)**2) ** 0.5
                        alpha = min(200, int(150 * (dist / max_dist)))
                        vignette.set_at((i, j), (0, 0, 0, alpha))
                
                camera_feed.blit(vignette, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
            return camera_feed
            
        except ValueError as e:
            print(f"Error generating camera view: {e}")
            # Return a black screen if something goes wrong
            return pygame.Surface(camera_size)
    
    def draw_minimap(self, surface, position, size, drone_pos, waypoints=None):
        """
        Draw a minimap showing the drone's position, waypoints, and landmark.
        
        Args:
            surface: The surface to draw the minimap on
            position: (x, y) position of the minimap
            size: (width, height) of the minimap
            drone_pos: (x, y) position of the drone
            waypoints: List of (x, y) waypoints to draw
        """
        # Create a background for the minimap
        minimap_bg = pygame.Surface((size[0] + 4, size[1] + 4))
        minimap_bg.fill((50, 50, 50))
        pygame.draw.rect(minimap_bg, (200, 200, 200), (0, 0, size[0] + 4, size[1] + 4), 1)
        
        # Scale the map to fit the minimap
        map_ratio = min(size[0] / self.width, size[1] / self.height)
        map_width = int(self.width * map_ratio)
        map_height = int(self.height * map_ratio)
        
        # Position the map in the center of the minimap
        map_x = (size[0] - map_width) // 2 + 2
        map_y = (size[1] - map_height) // 2 + 2
        
        # Draw the map
        scaled_map = pygame.transform.scale(self.map, (map_width, map_height))
        minimap_bg.blit(scaled_map, (map_x, map_y))
        
        # Draw landmark if present
        if self.landmark_position and self.landmark_image:
            landmark_x, landmark_y = self.landmark_position
            lm_px = int(landmark_x * map_ratio) + map_x
            lm_py = int(landmark_y * map_ratio) + map_y
            
            # Draw landmark with a distinctive color and size
            pygame.draw.circle(minimap_bg, (255, 255, 0), (lm_px, lm_py), 6)  # Yellow circle
            pygame.draw.circle(minimap_bg, (255, 165, 0), (lm_px, lm_py), 8, 2)  # Orange border
            
            # Add "L" label for landmark
            font = pygame.font.SysFont("Arial", 12)
            label = font.render("L", True, (0, 0, 0))
            label_rect = label.get_rect(center=(lm_px, lm_py))
            minimap_bg.blit(label, label_rect)
        
        # Draw waypoints if provided
        if waypoints:
            for i, (wx, wy) in enumerate(waypoints):
                px = int(wx * map_ratio) + map_x
                py = int(wy * map_ratio) + map_y
                color = (0, 255, 0) if i == 0 else (255, 0, 0)
                pygame.draw.circle(minimap_bg, color, (px, py), 3)
                if i > 0:
                    prev_wx, prev_wy = waypoints[i-1]
                    prev_px = int(prev_wx * map_ratio) + map_x
                    prev_py = int(prev_wy * map_ratio) + map_y
                    pygame.draw.line(minimap_bg, (255, 255, 0), (prev_px, prev_py), (px, py), 1)
        
        # Draw drone position
        drone_px = int(drone_pos[0] * map_ratio) + map_x
        drone_py = int(drone_pos[1] * map_ratio) + map_y
        pygame.draw.circle(minimap_bg, (0, 0, 255), (drone_px, drone_py), 4)
        
        # Draw a border around the drone
        pygame.draw.circle(minimap_bg, (255, 255, 255), (drone_px, drone_py), 5, 1)
        
        # Draw drone direction indicator
        if hasattr(self, 'drone_heading'):
            heading_rad = np.radians(self.drone_heading)
            end_x = drone_px + int(8 * np.cos(heading_rad))
            end_y = drone_py - int(8 * np.sin(heading_rad))  # Y is inverted
            pygame.draw.line(minimap_bg, (255, 255, 255), (drone_px, drone_py), (end_x, end_y), 2)
        
        # Blit the minimap onto the target surface
        surface.blit(minimap_bg, position)