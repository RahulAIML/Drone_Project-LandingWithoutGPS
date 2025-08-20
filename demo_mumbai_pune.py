#!/usr/bin/env python3
"""
Quick Demo: Mumbai to Pune Route
This script demonstrates the route planning for Mumbai to Pune
"""

from route_planner import RoutePlanner

def main():
    print("=== 🚁 Mumbai to Pune Route Demo ===")
    
    # Create route planner
    planner = RoutePlanner()
    
    # Plan Mumbai to Pune route
    route = ['Mumbai', 'Pune']
    
    print(f"\nPlanning route: {' → '.join(route)}")
    
    # Get route information
    info = planner.get_route_info(route)
    
    if info['valid']:
        print(f"\n✅ Route is valid!")
        print(f"📍 Waypoints: {info['waypoint_count']}")
        print(f"📏 Distance: {info['distance_pixels']:.1f} pixels")
        print(f"🌍 Estimated real distance: {info['distance_km']:.1f} km")
        
        if info['estimated_time_hours']:
            hours = int(info['estimated_time_hours'])
            minutes = int((info['estimated_time_hours'] - hours) * 60)
            print(f"⏱️  Estimated flight time: {hours}h {minutes}m")
        
        print("\n📍 Waypoint details:")
        for i, city in enumerate(route):
            x, y = planner.cities[city]
            print(f"  {i+1}. {city} at coordinates ({x}, {y})")
            
            if i < len(route) - 1:
                next_city = route[i + 1]
                distance = planner.calculate_distance(city, next_city)
                real_distance = planner.estimate_real_distance(distance) if distance else 0
                print(f"     → {next_city}: {distance:.1f} pixels ({real_distance:.1f} km)")
        
        print("\n🚀 To run this route in simulation:")
        print("1. Run: python city_navigation.py")
        print("2. Press '1' for Mumbai → Pune route")
        print("3. Or press 'C' for custom route and enter: Mumbai,Pune")
        
    else:
        print(f"❌ Route error: {info['message']}")

if __name__ == "__main__":
    main() 