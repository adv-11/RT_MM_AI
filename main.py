import streamlit as st
import time
import cv2
import numpy as np
import pyautogui
import pyaudio
from threading import Thread
from moviepy.editor import ImageSequenceClip
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
from PIL import Image

# Load environment variables
load_dotenv()

# Google GenAI API setup
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MODEL_NAME = "gemini-2.0-flash-exp"
client = genai.Client(api_key=GOOGLE_API_KEY)

# Streamlit app
st.title("Real-Time Multimodal AI")

# Global variables for screen recording and audio detection
frames = []
recording = False
audio_detected = False
audio_recording = False  # Whether audio is currently being captured
start_time, end_time = None, None

# Audio detection function
def detect_audio():
    global audio_detected, start_time, end_time
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    silence_threshold = 500  # Adjust as needed

    while audio_recording:
        audio_data = np.frombuffer(stream.read(1024), dtype=np.int16)
        print(f"Max audio data: {audio_data.max()}")  # Debugging audio detection
        if audio_data.max() > silence_threshold:
            if not audio_detected:
                audio_detected = True
                start_time = time.time()
        else:
            if audio_detected:
                end_time = time.time()
                audio_detected = False
        time.sleep(0.1)

# Screen recording function
def record_screen():
    global recording, frames
    while recording:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frames.append(frame)
        
        # Show the screen capture in the Streamlit app
        st.image(frame, channels="BGR", use_column_width=True)
        
        time.sleep(0.1)

# Function to generate video from frames
def generate_video_from_frames():
    video_filename = "screen_capture.mp4"
    clip = ImageSequenceClip(frames, fps=10)
    clip.write_videofile(video_filename, codec="libx264")
    print(f"Video saved as {video_filename}")
    return video_filename

# Streamlit frontend components
start_button = st.button("Start Screen Sharing")
stop_button = st.button("Stop Screen Sharing")
audio_button = st.button("Start Audio Recording")

# Function to handle screen share and audio recording toggles
def handle_screen_share():
    global recording, frames, audio_recording, audio_detected
    if start_button:
        st.write("Starting Screen Share...")
        # Start screen recording thread
        recording = True
        frames.clear()
        record_thread = Thread(target=record_screen)
        record_thread.start()

        st.write("Screen Sharing Started...")
    
    if stop_button:
        st.write("Stopping Screen Share...")
        # Stop recording
        recording = False
        record_thread.join()

        # Generate video from frames
        video_filename = generate_video_from_frames()

        # Process video with Google GenAI API
        upload_and_process(video_filename)
    
    if audio_button:
        if not audio_recording:
            st.write("Starting Audio Recording...")
            # Start audio detection
            audio_recording = True
            audio_thread = Thread(target=detect_audio)
            audio_thread.start()
            st.button("Stop Audio Recording", key="stop_audio")
        else:
            st.write("Stopping Audio Recording...")
            # Stop audio detection
            audio_recording = False
            st.button("Start Audio Recording", key="start_audio")

# Function to upload and process video using Google GenAI
def upload_and_process(video_file_name):
    global start_time, end_time
    # Upload video to Google GenAI
    video_file = client.files.upload(path=video_file_name)

    # Wait for processing
    while video_file.state == "PROCESSING":
        print("Waiting for video to be processed.")
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)

    if video_file.state == "FAILED":
        raise ValueError("Video processing failed")

    print(f"Video processing complete: {video_file.uri}")

    # Create a prompt based on the audio
    prompt = f"Analyze the video from {start_time} to {end_time}. Provide insights."

    # Generate content using Gemini API
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[types.Content(
            role="user",
            parts=[types.Part.from_uri(file_uri=video_file.uri, mime_type="video/mp4")]),
            prompt,
        ]
    )

    print("Gemini Response:")
    print(response.text)

# Run the screen share and audio toggle functionality
handle_screen_share()
