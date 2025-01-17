import gradio as gr
import cv2
import numpy as np
import pyautogui
import pyaudio
import threading
import time
import simplepeer
import uuid

# Global variables
audio_recording = False
audio_stream = None
audio_data = []

# Audio recording function
def start_audio_recording():
    global audio_recording, audio_stream, audio_data
    if not audio_recording:
        audio_recording = True
        audio_data = []
        audio_stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                               channels=1,
                                               rate=44100,
                                               input=True,
                                               frames_per_buffer=1024)
        print("Audio recording started.")
        # Start thread to record audio in the background
        threading.Thread(target=record_audio).start()
    else:
        print("Audio is already recording.")

def stop_audio_recording():
    global audio_recording, audio_stream
    if audio_recording:
        audio_recording = False
        audio_stream.stop_stream()
        audio_stream.close()
        print("Audio recording stopped.")
    else:
        print("No audio recording to stop.")

def record_audio():
    global audio_stream, audio_data
    while audio_recording:
        audio_chunk = np.frombuffer(audio_stream.read(1024), dtype=np.int16)
        audio_data.append(audio_chunk)

# Screen Capture for WebRTC
def capture_screen():
    while True:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        yield frame

# Function to start the peer connection and handle screen share
def start_screen_sharing(audio_status):
    global peer
    if audio_status == "Start Audio":
        start_audio_recording()
    elif audio_status == "Stop Audio":
        stop_audio_recording()

    print("Screen sharing started")
    peer = simplepeer({
        "initiator": True,
        "trickle": False,
    })

    # Prepare the video stream for the peer connection
    for frame in capture_screen():
        peer.signal(frame)
        time.sleep(0.1)  # Control frame rate

    return "Screen sharing started"

# Gradio Interface
def interface():
    with gr.Blocks() as demo:
        gr.Markdown("### Real-Time Screen Sharing with Audio Capture")

        with gr.Row():
            screen_share_button = gr.Button("Start Screen Share")
            audio_button = gr.Button("Start Audio")

        status = gr.Textbox(value="No Status Yet", label="Current Status", interactive=False)

        screen_share_button.click(start_screen_sharing, inputs=[audio_button], outputs=status)
        audio_button.click(start_audio_recording, inputs=None, outputs=None)

    demo.launch()

# Run Gradio Interface
if __name__ == "__main__":
    interface()
