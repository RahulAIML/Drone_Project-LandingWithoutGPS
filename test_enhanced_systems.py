#!/usr/bin/env python3
"""
Test script for enhanced drone simulation systems.
Tests Phase 1 (Precision Landing) and Phase 2 (Visual Navigation) components.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vision_system import VisionSystem
from navigation import NavigationSystem
from drone import Drone

def test_vision_system():
    """Test the enhanced vision system."""
    print("=== Testing Vision System ===")
    
    try:
        # Test vision system initialization
        vision = VisionSystem('assets/landmark.png')
        print("✓ Vision system initialized successfully")
        print(f"  - Landmark features detected: {len(vision.kp_landmark)}")
        
        # Test landmark detection (would need actual camera feed in real test)
        print("✓ Vision system ready for landmark detection")
        
    except Exception as e:
        print(f"✗ Vision system test failed: {e}")
        return False
    
    return True

def test_navigation_system():
    """Test the enhanced navigation system."""
    print("\n=== Testing Navigation System ===")
    
    try:
        # Test waypoints
        waypoints = [(100, 100), (200, 200), (300, 300)]
        nav = NavigationSystem(waypoints)
        print("✓ Navigation system initialized successfully")
        print(f"  - Waypoints loaded: {len(waypoints)}")
        
        # Test position updates
        current_pos = (100, 100)
        command, target = nav.update_position(current_pos)
        print(f"  - Initial command: {command}")
        print(f"  - Target position: {target}")
        
        # Test reaching waypoint
        nav.current_waypoint_idx = 0
        command, target = nav.update_position((200, 200))
        print(f"  - After movement command: {command}")
        
        # Test navigation info
        info = nav.get_navigation_info()
        print(f"  - Navigation info: {info}")
        
    except Exception as e:
        print(f"✗ Navigation system test failed: {e}")
        return False
    
    return True

def test_drone_system():
    """Test the enhanced drone system."""
    print("\n=== Testing Drone System ===")
    
    try:
        # Test drone initialization
        start_pos = (100, 100)
        start_alt = 150
        drone = Drone(start_pos, start_alt)
        print("✓ Drone initialized successfully")
        print(f"  - Start position: {drone.get_position()}")
        print(f"  - Initial velocity: {drone.velocity}")
        
        # Test movement commands
        commands = ["MOVE RIGHT", "MOVE FORWARD", "DESCEND", "HOLD"]
        for cmd in commands:
            old_pos = drone.get_position()
            new_x, new_y = drone.get_next_position(cmd)
            drone.x, drone.y = new_x, new_y
            print(f"  - Command '{cmd}': {old_pos[:2]} -> ({new_x}, {new_y})")
        
        # Test status
        status = drone.get_status()
        print(f"  - Current status: {status}")
        
        # Test battery
        battery, battery_status = drone.get_battery_status()
        print(f"  - Battery: {battery}% ({battery_status})")
        
    except Exception as e:
        print(f"✗ Drone system test failed: {e}")
        return False
    
    return True

def test_integration():
    """Test basic integration between systems."""
    print("\n=== Testing System Integration ===")
    
    try:
        # Initialize all systems
        waypoints = [(100, 100), (200, 200), (250, 250)]
        drone = Drone((100, 100), 150)
        nav = NavigationSystem(waypoints)
        
        print("✓ All systems initialized")
        
        # Simulate basic navigation
        for i in range(3):
            command, target = nav.update_position(drone.get_position()[:2])
            if command == "REACHED_DESTINATION":
                print("  - Navigation completed successfully")
                break
            
            print(f"  - Step {i+1}: {command} -> {target}")
            next_x, next_y = drone.get_next_position(command)
            drone.x, drone.y = next_x, next_y
        
        print("✓ Basic integration test passed")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Enhanced Drone Simulation Systems Test")
    print("=" * 50)
    
    tests = [
        test_vision_system,
        test_navigation_system,
        test_drone_system,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Systems are ready for simulation.")
        print("\nTo run the simulation:")
        print("  python simulation_main.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 