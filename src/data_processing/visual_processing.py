import os
import re
import PIL.Image
import cv2
from dotenv import load_dotenv
import google.generativeai as genai

# Import other functions of the data_processing package
from .logger import log

# Static variables
VIDEO_DIRECTORY = "./media/videos/"
FRAMES_DIRECTORY = "./media/frames/"
IMAGE_DESCRIPTION_DIRECTORY = "./media/frames_description/"

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
            cv2.imwrite(f"./media/{filename}/frames/frame{count}.jpg", image)
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

    TODO:
        - Describe only the images that add relevant content. Ignore frames that are unreadable or serve merely as transitions.
    """

    log.info(f"create_image_description: Start creating descriptions for images using {gemini_model} as LLM.")

    # Configure and load genai model
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)

    path_dir = f"./media/{video_id}/frames/"
    all_image_files = os.listdir(path_dir)

    # Iterate through all image files
    for file in all_image_files:

        image_file_path = path_dir + "/" + file
        image_file = PIL.Image.open(image_file_path)

        prompt = (
            "Please provide a detailed description of the image from the YouTube video, "
            "focusing on the relevant content, e.g. AI, Machine Learning, "
            "or other topics shown in the picture. Describe the setting, including the environment, any diagrams, "
            "charts, equations, or visual aids displayed. If there are visual representations of algorithms, "
            "models, or data, explain them in detail, including any colors, patterns, or structures. "
            "If relevant people, such as experts in computer vision or similar fields, are shown in the "
            "context of the task, briefly mention them and their relevance. Focus on mentioning people who "
            "are directly relevant to the content of the video. Avoid mentioning other people."
        )

        # Generate response
        response = model.generate_content(
            [prompt, image_file]
        )

        path_dir_frame_desc = f"./media/{video_id}/frames_description/"
        if not os.path.exists(path_dir_frame_desc):
            os.makedirs(path_dir_frame_desc)

        # Save response in a designated file
        filename = file.replace(".jpg", "")
        with open(f"{path_dir_frame_desc}/{filename}.txt", "w", encoding="utf-8") as response_file:
            response_file.write(response.text)
        log.info(f"creating_image_description: Successfully created an image description for file {filename}.")

