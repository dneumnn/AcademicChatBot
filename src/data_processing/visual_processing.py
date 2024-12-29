import os
import PIL.Image
import cv2
from dotenv import load_dotenv
import google.generativeai as genai

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

    print("Begin extraction of video frames...")

    # Extract filename from file path
    filename = video_filepath.replace(VIDEO_DIRECTORY, "")
    filename = filename.replace(".mp4", "")
    if not os.path.exists(f"{FRAMES_DIRECTORY}{filename}"):
        os.makedirs(f"{FRAMES_DIRECTORY}{filename}")

    # Calculate interval in frames
    cam = cv2.VideoCapture(video_filepath)
    video_fps = cam.get(cv2.CAP_PROP_FPS)
    interval_in_frames = round(video_fps * interval_in_sec)
    print(f"Calculated frames interval: {interval_in_frames}")

    # Extract frames
    success, image = cam.read()
    count = 0
    while success:
        if count % interval_in_frames == 0:
            print(f"Extracting frame {count} for video {filename}")
            cv2.imwrite(f"{FRAMES_DIRECTORY}{filename}/frame{count}.jpg", image)
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

    # Configure and load genai model
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)

    path_dir = FRAMES_DIRECTORY + video_id + "/"
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

        path_dir_frame_desc = f"{IMAGE_DESCRIPTION_DIRECTORY}{video_id}"
        if not os.path.exists(path_dir_frame_desc):
            os.makedirs(path_dir_frame_desc)

        # Save response in a designated file
        filename = file.replace(".jpg", "")
        with open(f"{path_dir_frame_desc}/{filename}.txt", "w", encoding="utf-8") as response_file:
            response_file.write(response.text)

