from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
load_dotenv()
import time
import json
from PIL import Image
from IPython.display import display, Markdown, HTML

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
model_name = "gemini-2.0-flash-exp"

client = genai.Client(api_key=GOOGLE_API_KEY)

system_instructions = """
    When given a video and a query, call the relevant function only once with the appropriate timecodes and text for the video
  """

def upload_video(video_file_name):
  video_file = client.files.upload(path=video_file_name)

  while video_file.state == "PROCESSING":
      print('Waiting for video to be processed.')
      
      video_file = client.files.get(name=video_file.name)

  if video_file.state == "FAILED":
    raise ValueError(video_file.state)
  print(f'Video processing complete: ' + video_file.uri)

  return video_file


sample_video = upload_video('sample_vid\LZKA4762.MP4')

sample_prompt = 'Identify the animal and its breed from the video.'

response = client.models.generate_content(
    model=model_name,
    contents=[
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=sample_video.uri,
                    mime_type=sample_video.mime_type),
                ]),
        sample_prompt,
    ]
)

print (response.text)