# drone.py - Enhanced Drone Physics and Control

import math
import numpy as np

class Drone:
    def __init__(self, start_pos, start_alt):
        """
        Initialize the drone's state with enhanced physics.
        
        Args:
            start_pos: Tuple of (x, y) starting position
            start_alt: Starting altitude (z-coordinate)
        """
        self.x, self.y = start_pos
        self.z = start_alt
        
        # Movement parameters
        self.velocity = 2.0  # Base velocity (pixels per frame)
        self.max_velocity = 5.0
        self.min_velocity = 0.5
        
        # Altitude control
        self.descent_speed = 1.5
        self.ascent_speed = 2.0
        self.max_altitude = 150
        self.min_altitude = 5
        self.landing_altitude = 10
        
        # Flight characteristics
        self.heading = 0  # in degrees, 0 is facing right, 90 is up
        self.battery = 100  # Battery percentage
        self.battery_drain_rate = 0.005  # Per frame
        
        # Control parameters
        self.position_tolerance = 3  # Pixels for precise positioning
        self.altitude_tolerance = 2  # Pixels for altitude control
        
        # State tracking
        self.is_landing = False
        self.is_landed = False
        self.last_command = "HOLD"
        
        print(f"Drone initialized at: ({self.x}, {self.y}), Alt: {self.z}")

    def get_next_position(self, command):
        """
        Calculate the drone's next position based on a command with enhanced physics.
        
        Args:
            command: String command for movement
            
        Returns:
            Tuple of (new_x, new_y) coordinates
        """
        new_x, new_y = self.x, self.y
        
        # Handle movement commands with improved precision
        if command == "MOVE FORWARD":
            new_y -= self.velocity
            self.heading = 90
        elif command == "MOVE BACKWARD":
            new_y += self.velocity
            self.heading = 270
        elif command == "MOVE LEFT":
            new_x -= self.velocity
            self.heading = 180
        elif command == "MOVE RIGHT":
            new_x += self.velocity
            self.heading = 0
        elif command == "DESCEND":
            if not self.is_landed:
                self.z = max(self.min_altitude, self.z - self.descent_speed)
                if self.z <= self.landing_altitude:
                    self.is_landing = True
        elif command == "ASCEND":
            self.z = min(self.max_altitude, self.z + self.ascent_speed)
            self.is_landing = False
        elif command == "HOLD":
            # Maintain current position
            pass
        
        # Update battery
        self.battery = max(0, self.battery - self.battery_drain_rate)
        
        # Adaptive velocity based on altitude and mission phase
        self._update_velocity()
        
        # Store last command
        self.last_command = command
        
        # Check if landed
        if self.z <= self.min_altitude and self.is_landing:
            self.is_landed = True
            print("DRONE HAS LANDED SUCCESSFULLY!")
        
        return new_x, new_y
    
    def _update_velocity(self):
        """Update velocity based on current conditions."""
        # Slow down as we get lower for more precise landing
        if self.z < 30:
            self.velocity = max(self.min_velocity, self.velocity * 0.95)
        elif self.z < 80:
            self.velocity = min(self.max_velocity, self.velocity * 1.02)
        else:
            self.velocity = min(self.max_velocity, self.velocity * 1.01)
            
        # Ensure velocity stays within bounds
        self.velocity = max(self.min_velocity, min(self.max_velocity, self.velocity))
        
    def get_battery_status(self):
        """Return the current battery level and status."""
        if self.battery > 50:
            return self.battery, "OK"
        elif self.battery > 20:
            return self.battery, "LOW"
        elif self.battery > 5:
            return self.battery, "CRITICAL"
        else:
            return self.battery, "EMERGENCY"
            
    def get_position(self):
        """Return the current position as a tuple (x, y, z)."""
        return (self.x, self.y, self.z)
        
    def get_altitude(self):
        """Return the current altitude."""
        return self.z
    
    def get_status(self):
        """Get comprehensive drone status."""
        battery_level, battery_status = self.get_battery_status()
        
        return {
            "position": (int(self.x), int(self.y), int(self.z)),
            "heading": self.heading,
            "velocity": round(self.velocity, 2),
            "battery": round(battery_level, 1),
            "battery_status": battery_status,
            "is_landing": self.is_landing,
            "is_landed": self.is_landed,
            "last_command": self.last_command
        }
    
    def set_velocity(self, new_velocity):
        """Set the drone's velocity."""
        self.velocity = max(self.min_velocity, min(self.max_velocity, new_velocity))
    
    def emergency_land(self):
        """Emergency landing procedure."""
        self.is_landing = True
        self.velocity = self.min_velocity
        print("EMERGENCY LANDING INITIATED!")
    
    def reset_position(self, new_pos, new_alt):
        """Reset drone position (for testing)."""
        self.x, self.y = new_pos
        self.z = new_alt
        self.is_landing = False
        self.is_landed = False
        print(f"Drone position reset to: ({self.x}, {self.y}), Alt: {self.z}")