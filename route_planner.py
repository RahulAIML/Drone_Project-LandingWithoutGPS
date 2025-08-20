#!/usr/bin/env python3
"""
Route Planner for Drone Navigation Simulation
This utility helps plan routes between cities and calculate distances.
"""

import math
from typing import List, Tuple, Dict, Optional

# City coordinates on the map (same as in city_navigation.py)
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

# Popular route suggestions
POPULAR_ROUTES = {
    'Mumbai to Pune': ['Mumbai', 'Pune'],
    'Mumbai to Delhi': ['Mumbai', 'Delhi'],
    'Mumbai to Kolkata': ['Mumbai', 'Pune', 'Nagpur', 'Kolkata'],
    'Delhi to Mumbai': ['Delhi', 'Mumbai'],
    'Delhi to Kolkata': ['Delhi', 'Lucknow', 'Patna', 'Kolkata'],
    'Bangalore to Delhi': ['Bangalore', 'Hyderabad', 'Nagpur', 'Delhi'],
    'Chennai to Mumbai': ['Chennai', 'Bangalore', 'Mumbai'],
    'Kolkata to Mumbai': ['Kolkata', 'Nagpur', 'Pune', 'Mumbai'],
    'Mumbai to Bangalore': ['Mumbai', 'Pune', 'Bangalore'],
    'Delhi to Bangalore': ['Delhi', 'Agra', 'Bhopal', 'Nagpur', 'Hyderabad', 'Bangalore']
}

class RoutePlanner:
    def __init__(self):
        self.cities = CITY_COORDINATES
        self.popular_routes = POPULAR_ROUTES
    
    def calculate_distance(self, city1: str, city2: str) -> Optional[float]:
        """Calculate distance between two cities in pixels"""
        if city1 not in self.cities or city2 not in self.cities:
            return None
        
        x1, y1 = self.cities[city1]
        x2, y2 = self.cities[city2]
        
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def calculate_route_distance(self, route: List[str]) -> Optional[float]:
        """Calculate total distance for a route"""
        if len(route) < 2:
            return None
        
        total_distance = 0
        for i in range(len(route) - 1):
            distance = self.calculate_distance(route[i], route[i + 1])
            if distance is None:
                return None
            total_distance += distance
        
        return total_distance
    
    def estimate_real_distance(self, pixel_distance: float) -> float:
        """Estimate real-world distance in km from pixel distance"""
        # This is a rough estimation - you can adjust the scale factor
        # Based on your map scale and requirements
        scale_factor = 0.5  # km per pixel
        return pixel_distance * scale_factor
    
    def find_nearest_cities(self, city: str, count: int = 5) -> List[Tuple[str, float]]:
        """Find the nearest cities to a given city"""
        if city not in self.cities:
            return []
        
        distances = []
        for other_city in self.cities:
            if other_city != city:
                distance = self.calculate_distance(city, other_city)
                if distance is not None:
                    distances.append((other_city, distance))
        
        # Sort by distance and return top N
        distances.sort(key=lambda x: x[1])
        return distances[:count]
    
    def suggest_route(self, start_city: str, end_city: str, max_waypoints: int = 3) -> List[str]:
        """Suggest a route between two cities with optional intermediate waypoints"""
        if start_city not in self.cities or end_city not in self.cities:
            return []
        
        if max_waypoints == 1:
            return [start_city, end_city]
        
        # Find intermediate cities that could be good waypoints
        start_neighbors = self.find_nearest_cities(start_city, 10)
        end_neighbors = self.find_nearest_cities(end_city, 10)
        
        # Find cities that are roughly between start and end
        start_x, start_y = self.cities[start_city]
        end_x, end_y = self.cities[end_city]
        
        # Calculate midpoint
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # Find cities near the midpoint
        midpoint_cities = []
        for city, (x, y) in self.cities.items():
            if city not in [start_city, end_city]:
                distance_to_midpoint = math.sqrt((x - mid_x)**2 + (y - mid_y)**2)
                midpoint_cities.append((city, distance_to_midpoint))
        
        midpoint_cities.sort(key=lambda x: x[1])
        
        # Build route
        route = [start_city]
        
        # Add intermediate waypoints if needed
        for i in range(min(max_waypoints - 2, len(midpoint_cities))):
            route.append(midpoint_cities[i][0])
        
        route.append(end_city)
        return route
    
    def validate_route(self, route: List[str]) -> Tuple[bool, str]:
        """Validate if a route is valid"""
        if len(route) < 2:
            return False, "Route must have at least 2 cities"
        
        for city in route:
            if city not in self.cities:
                return False, f"City '{city}' not found in available cities"
        
        return True, "Route is valid"
    
    def get_route_info(self, route: List[str]) -> Dict:
        """Get detailed information about a route"""
        is_valid, message = self.validate_route(route)
        
        if not is_valid:
            return {
                'valid': False,
                'message': message,
                'distance': None,
                'waypoints': None,
                'estimated_time': None
            }
        
        total_distance = self.calculate_route_distance(route)
        estimated_real_distance = self.estimate_real_distance(total_distance) if total_distance else None
        
        # Estimate flight time (assuming average speed of 50 km/h)
        estimated_time = None
        if estimated_real_distance:
            estimated_time = estimated_real_distance / 50  # hours
        
        return {
            'valid': True,
            'message': 'Route is valid',
            'distance_pixels': total_distance,
            'distance_km': estimated_real_distance,
            'waypoints': route,
            'estimated_time_hours': estimated_time,
            'waypoint_count': len(route)
        }
    
    def list_all_cities(self) -> List[str]:
        """List all available cities"""
        return sorted(self.cities.keys())
    
    def list_popular_routes(self) -> Dict[str, List[str]]:
        """List all popular routes"""
        return self.popular_routes.copy()
    
    def print_route_summary(self, route: List[str]):
        """Print a summary of the route"""
        info = self.get_route_info(route)
        
        if not info['valid']:
            print(f"❌ Invalid route: {info['message']}")
            return
        
        print(f"\n🗺️  Route Summary: {' → '.join(route)}")
        print(f"📍 Waypoints: {info['waypoint_count']}")
        print(f"📏 Distance: {info['distance_pixels']:.1f} pixels")
        print(f"🌍 Estimated real distance: {info['distance_km']:.1f} km")
        
        if info['estimated_time_hours']:
            hours = int(info['estimated_time_hours'])
            minutes = int((info['estimated_time_hours'] - hours) * 60)
            print(f"⏱️  Estimated flight time: {hours}h {minutes}m")
        
        print("\n📍 Waypoint details:")
        for i, city in enumerate(route):
            x, y = self.cities[city]
            print(f"  {i+1}. {city} at coordinates ({x}, {y})")
            
            if i < len(route) - 1:
                next_city = route[i + 1]
                distance = self.calculate_distance(city, next_city)
                real_distance = self.estimate_real_distance(distance) if distance else 0
                print(f"     → {next_city}: {distance:.1f} pixels ({real_distance:.1f} km)")

def main():
    """Interactive route planner"""
    planner = RoutePlanner()
    
    print("=== 🚁 Drone Route Planner ===")
    print("Plan routes between cities for your drone simulation!")
    
    while True:
        print("\n" + "="*50)
        print("Options:")
        print("1. Plan a route between two cities")
        print("2. View popular routes")
        print("3. List all available cities")
        print("4. Calculate distance between cities")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            print(f"\nAvailable cities: {', '.join(planner.list_all_cities())}")
            start = input("Enter start city: ").strip()
            end = input("Enter destination city: ").strip()
            
            if start and end:
                route = planner.suggest_route(start, end, max_waypoints=4)
                if route:
                    planner.print_route_summary(route)
                else:
                    print("❌ Could not plan route between these cities")
            else:
                print("❌ Please enter both cities")
        
        elif choice == '2':
            print("\n📋 Popular Routes:")
            for i, (route_name, cities) in enumerate(planner.popular_routes.items(), 1):
                print(f"{i}. {route_name}")
            
            route_choice = input("\nEnter route number to view details (or press Enter to skip): ").strip()
            if route_choice.isdigit():
                route_index = int(route_choice) - 1
                route_names = list(planner.popular_routes.keys())
                if 0 <= route_index < len(route_names):
                    route_name = route_names[route_index]
                    cities = planner.popular_routes[route_name]
                    planner.print_route_summary(cities)
        
        elif choice == '3':
            cities = planner.list_all_cities()
            print(f"\n🏙️  Available Cities ({len(cities)}):")
            for i, city in enumerate(cities, 1):
                x, y = planner.cities[city]
                print(f"{i:2d}. {city:<15} at ({x:3d}, {y:3d})")
        
        elif choice == '4':
            print(f"\nAvailable cities: {', '.join(planner.list_all_cities())}")
            city1 = input("Enter first city: ").strip()
            city2 = input("Enter second city: ").strip()
            
            if city1 and city2:
                distance = planner.calculate_distance(city1, city2)
                if distance is not None:
                    real_distance = planner.estimate_real_distance(distance)
                    print(f"\n📏 Distance from {city1} to {city2}:")
                    print(f"   Pixels: {distance:.1f}")
                    print(f"   Estimated: {real_distance:.1f} km")
                else:
                    print("❌ Could not calculate distance")
            else:
                print("❌ Please enter both cities")
        
        elif choice == '5':
            print("\n👋 Goodbye! Happy flying!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main() 