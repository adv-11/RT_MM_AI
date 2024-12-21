from google import genai
from google.genai import types
import os
import time
import cv2
import numpy as np
import pyautogui
import pyaudio
from threading import Thread
from moviepy.editor import ImageSequenceClip
from fastapi import FastAPI, WebSocket
from dotenv import load_dotenv
load_dotenv()
import time
import json
from PIL import Image
from IPython.display import display, Markdown, HTML
from fastapi.middleware.cors import CORSMiddleware

# GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# model_name = "gemini-2.0-flash-exp"

# client = genai.Client(api_key=GOOGLE_API_KEY)

# system_instructions = """
#     When given a video and a query, call the relevant function only once with the appropriate timecodes and text for the video
#   """

# def upload_video(video_file_name):
#   video_file = client.files.upload(path=video_file_name)

#   while video_file.state == "PROCESSING":
#       print('Waiting for video to be processed.')
      
#       video_file = client.files.get(name=video_file.name)

#   if video_file.state == "FAILED":
#     raise ValueError(video_file.state)
#   print(f'Video processing complete: ' + video_file.uri)

#   return video_file

''' Code below contains sample working, uncomment it out and give it a try to ensure dependencies, installations, api key, etc is valid
'''


# sample_video = upload_video('sample_vid\LZKA4762.MP4')

# sample_prompt = 'Identify the animal and its breed from the video.'

# response = client.models.generate_content(
#     model=model_name,
#     contents=[
#         types.Content(
#             role="user",
#             parts=[
#                 types.Part.from_uri(
#                     file_uri=sample_video.uri,
#                     mime_type=sample_video.mime_type),
#                 ]),
#         sample_prompt,
#     ]
# )
# print (response.text)

# screen share, plus audio stop


# response = client.models.generate_content(
#     model=model_name,
#     contents=[
#         types.Content(
#             role="user",
#             parts=[
#                 types.Part.from_uri(
#                     file_uri=video.uri,
#                     mime_type=video.mime_type),
#                 ]),
#         prompt,
#     ]
# )
# print (response.text)


#4o code starts here




# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
MODEL_NAME = "gemini-2.0-flash-exp"

# Initialize Google GenAI client
client = genai.Client(api_key=GOOGLE_API_KEY)

# FastAPI app
app = FastAPI()


# Allow frontend and backend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for screen recording and audio detection
frames = []
recording = False
audio_detected = False
start_time, end_time = None, None


# Audio detection
def detect_audio():
    global audio_detected, start_time, end_time
    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    silence_threshold = 500  # Adjust as needed

    while True:
        audio_data = np.frombuffer(stream.read(1024), dtype=np.int16)
        if audio_data.max() > silence_threshold:
            if not audio_detected:
                audio_detected = True
                start_time = time.time()
        else:
            if audio_detected:
                end_time = time.time()
                audio_detected = False

# Screen recording
def record_screen():
    global recording, frames
    while recording:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frames.append(frame)
        time.sleep(0.1)

@app.websocket("/screen-share")
async def screen_share(websocket: WebSocket):
    global recording, frames
    await websocket.accept()

    # Start screen recording and audio detection threads
    recording = True
    frames.clear()
    audio_thread = Thread(target=detect_audio)
    audio_thread.start()
    record_thread = Thread(target=record_screen)
    record_thread.start()

    try:
        while True:
            await websocket.receive_text()  # Keep the connection open
    except Exception as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        recording = False
        audio_thread.join()
        record_thread.join()

        # Generate video from captured frames
        video_filename = "screen_capture.mp4"
        clip = ImageSequenceClip(frames, fps=10)
        clip.write_videofile(video_filename, codec="libx264")
        print(f"Video saved as {video_filename}")

        # Upload video and send prompt to Gemini API
        upload_and_process(video_filename)

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
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(
                        file_uri=video_file.uri,
                        mime_type="video/mp4"
                    ),
                ]
            ),
            prompt,
        ]
    )

    print("Gemini Response:")
    print(response.text)
