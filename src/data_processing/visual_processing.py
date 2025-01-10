import time
import os
import re
import PIL.Image
import cv2
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd

# Import other functions of the data_processing package
from .logger import log

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")


def extract_frames_from_video(video_filepath: str, interval_in_sec: int = 30):
    """
    Extract a certain number of frames of a YouTube video.

    Args:
        video_filepath (str): The filepath of the video.
        interval_in_sec (int): Interval in seconds between each frame to be extracted. This specifies how frequently frames are captured from the video.

    Example:
        extract_frames_from_video("./media/videos/my_example_video.mp4", 5)

    TODO:
        - Extract only the frames that differ significantly from the previous ones.
    """

    log.info("extract_frames_from_video: Begin extraction of video frames...")

    # Extract filename from file path
    filename = re.search(r"video/(.+?)\.mp4", video_filepath).group(1)
    if not os.path.exists(f"./media/{filename}/frames/"):
        os.makedirs(f"./media/{filename}/frames/")

    # Calculate interval in frames
    cam = cv2.VideoCapture(video_filepath)
    video_fps = cam.get(cv2.CAP_PROP_FPS)
    interval_in_frames = round(video_fps * interval_in_sec)
    log.info(f"extract_frames_from_video: Calculated frames interval = {interval_in_frames}.")

    # Extract frames
    success, image = cam.read()
    count = 0
    while success:
        if count % interval_in_frames == 0:
            log.info(f"extract_frames_from_video: Extracting frame {count} for video {filename}.")
            timestamp_ms = cam.get(cv2.CAP_PROP_POS_MSEC)
            cv2.imwrite(f"./media/{filename}/frames/frame{count}_{timestamp_ms}.jpg", image)
        success, image = cam.read()
        count += 1


def create_image_description(video_id: str, gemini_model: str="gemini-1.5-flash"):
    """
    Extract a certain number of frames of a YouTube video.

    Args:
        video_id (str): The ID of the video that should be processed. Needs to match the directory name in /media/frames/video_id
        gemini_model (int): The used gemini genai model. Defaults to 'gemini-1.5-flash'.

    Example:
        create_image_description("njjBbKpkmFI", "gemini-1.5-flash")
    """

    log.info("create_image_description: Start creating descriptions for images using %s as LLM.", gemini_model)

    # Configure and load genai model
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)

    path_dir = f"./media/{video_id}/frames/"
    all_image_files = os.listdir(path_dir)

    descriptions = []

    requests_made = 0
    # Iterate through all image files
    for file in all_image_files:

        image_file_path = path_dir + "/" + file
        image_file = PIL.Image.open(image_file_path)

        prompt = (
            "Describe the extracted image from the instructional video, focusing solely on the relevant content related to "
            "the subject of the lesson: AI. Ignore irrelevant elements such as facecams or placeholders that are not related to "
            "the topic. Focus on describing concepts, diagrams, graphs, key points, or any other visual content in the image. "
            "If key points or visual representations of constructs, concepts, or models are shown, place them in context, "
            "explain their significance, and describe how they relate to the topic. Provide a coherent text block, with no formatting, "
            "bullet points, or other structural elements, just a clear and concise explanation of the image content."
        )


        if requests_made >= 14:
            time.sleep(50)
            requests_made = 0

        # Generate response
        response = model.generate_content(
            [prompt, image_file]
        )

        requests_made += 1

        path_dir_frame_desc = f"./media/{video_id}/frames_description/"
        if not os.path.exists(path_dir_frame_desc):
            os.makedirs(path_dir_frame_desc)


        # Save response in a designated file
        filename = file.replace(".jpg", "")
        timestamp_ms = filename.split("_", 1)[1]
        filename = filename.split("_",1)[0]
        frame_time_s = float(timestamp_ms) / 1000.0

        descriptions.append({"file_name": filename, "description": response.text, "time_in_s": frame_time_s})

    df = pd.DataFrame(descriptions)
    df.to_csv(f"{path_dir_frame_desc}/frame_descriptions.csv", index=False)

    log.info("creating_image_description: Successfully created an image description for file %s.", filename)

