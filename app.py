# app.py (Final Polished Version)

import streamlit as st
import cv2
import time
import pygame
from environment import Environment
from drone import Drone
from vision_system import VisionSystem
import numpy as np

# --- Page Configuration ---
st.set_page_config(layout="wide")
st.title("Autonomous Drone Landing Simulation")

# --- Initialization (runs only once) ---
if 'initialized' not in st.session_state:
    st.session_state.env = Environment('assets/map.png')
    st.session_state.drone = Drone(start_pos=(st.session_state.env.width // 2, st.session_state.env.height // 2), start_alt=150)
    st.session_state.vision = VisionSystem('assets/landmark.png')
    st.session_state.command = "HOLD"
    st.session_state.error = (0, 0)
    st.session_state.running = True
    st.session_state.initialized = True
    print("--- SIMULATION INITIALIZED ---")


# --- Display Placeholders ---
col1, col2 = st.columns(2)
with col1:
    st.header("Drone Camera Feed")
    camera_placeholder = st.empty()
with col2:
    st.header("Vision System Output")
    vision_placeholder = st.empty()

status_placeholder = st.empty()

# --- Main Simulation Loop ---
while st.session_state.running:
    env = st.session_state.env
    drone = st.session_state.drone
    vision = st.session_state.vision

    # 1. Get Camera View
    try:
        camera_feed_surface = env.get_camera_view(
            (drone.x, drone.y), (640, 480), drone.z)
        # Convert Pygame Surface to NumPy array for display
        camera_feed_np = pygame.surfarray.array3d(camera_feed_surface).transpose([1, 0, 2])
    except ValueError:
        st.error("Drone is out of bounds!")
        st.session_state.running = False
        break

    # 2. Process with Vision System
    processed_frame, landmark_pos = vision.find_landmark(camera_feed_surface)

    # 3. Get Command and Update Drone
    if landmark_pos:
        camera_center = (640 // 2, 480 // 2)
        command, error = vision.get_landing_command(camera_center, landmark_pos)
        st.session_state.command = command
        st.session_state.error = error
    else:
        st.session_state.command = "HOLD"

    # Use the workaround logic
    next_x, next_y = drone.get_next_position(st.session_state.command)
    drone.x = next_x
    drone.y = next_y
    
    if st.session_state.command == "DESCEND" and drone.z <= 10:
        st.success("LANDED!")
        st.balloons()
        st.session_state.running = False

    # 4. Update the Display
    # FIX: Changed use_column_width to use_container_width to remove warnings
    camera_placeholder.image(camera_feed_np, caption="Live Camera Feed", use_container_width=True)
    
    if processed_frame is not None:
        vision_placeholder.image(processed_frame, channels="BGR", caption="Processed Frame", use_container_width=True)
    else:
        vision_placeholder.image(camera_feed_np, caption="No Landmark Detected", use_container_width=True)

    status_placeholder.markdown(f"""
    ### **Status**
    - **Position:** `({drone.x}, {drone.y})`
    - **Altitude:** `{drone.z}`
    - **Command:** `{st.session_state.command}`
    - **Error:** `{st.session_state.error}`
    """)

    # Control loop speed
    time.sleep(0.05) # ~20 FPS