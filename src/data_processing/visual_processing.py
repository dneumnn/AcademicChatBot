import time
import os
import re
import PIL.Image
import cv2
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
import ollama
import torch
import clip

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


def create_image_description(video_id: str, gemini_model: str="gemini-1.5-flash", local_model:bool=False, local_llm:str="llama3.2-vision"):
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

        if local_model == False:
            # TODO: Dynamically read the time to sleep (?)
            if requests_made >= 14:
                time.sleep(50)
                requests_made = 0

            # Generate response
            response = model.generate_content(
                [prompt, image_file]
            )

            requests_made += 1
        
        else:
            response = ollama.chat(
                model=local_llm,
                messages=[{
                    "role": "user",
                    "content": prompt,
                    "images": [image_file]
                }]
            )


        path_dir_frame_desc = f"./media/{video_id}/frames_description/"
        if not os.path.exists(path_dir_frame_desc):
            os.makedirs(path_dir_frame_desc)


        # Save response in a designated file
        filename = file.replace(".jpg", "")        
        timestamp_ms = filename.split("_", 1)[1]
        filename = filename.split("_",1)[0]
        frame_time_s = float(timestamp_ms) / 1000
        descriptions.append({"video_id": video_id, "file_name": filename, "description": response.text.strip(), "time_in_s": frame_time_s})

    df = pd.DataFrame(descriptions)
    df.to_csv(f"{path_dir_frame_desc}/frame_descriptions.csv", index=False)

    log.info("creating_image_description: Successfully created an image description for file %s.", filename)


def extract_number(filename):
    """
    Extracts numeric frame id from a file name based on a specific pattern and returns it.

    Args:
        filename (str): The name of the file to process.

    Returns:
        int or float: The extracted number as an integer if the pattern is matched, 
                      or infinity (float('inf')) if no match is found.
    """
    match = re.search(r'frame(\d+)_', filename)
    return int(match.group(1)) if match else float('inf')


def remove_duplicate_images(image_folder_path:str, threshold: int=0.9):
    """
     Args:
        image_folder_path (str): Path to the folder containing the images to process.
        threshold (float): Similarity threshold above which images are considered 
            duplicates. Default is 0.9.

    Returns:
        None: The function modifies the folder by deleting duplicate images.
    """
    file_names = [
        file for file in os.listdir(image_folder_path)
        if os.path.isfile(os.path.join(image_folder_path, file))
    ]

    file_names_sorted = sorted(file_names, key=extract_number)

    file_names_sorted = [os.path.join(image_folder_path, filename) for filename in file_names_sorted]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)

    del_image_index = []
    r_i = 0

    for i in range(1, len(file_names_sorted)):
        image1 = file_names_sorted[r_i]
        image2 = file_names_sorted[i]

        cos = torch.nn.CosineSimilarity(dim=0)
        image1_preprocess = preprocess(PIL.Image.open(image1)).unsqueeze(0).to(device)
        image2_preprocess = preprocess(PIL.Image.open(image2)).unsqueeze(0).to(device)

        image1_features = model.encode_image(image1_preprocess)
        image2_features = model.encode_image(image2_preprocess)
        similarity = (cos(image1_features[0], image2_features[0]).item() + 1) / 2

        if similarity < threshold:
            r_i = i
        else:
            del_image_index.append(i)

    del_image_path = [file_names_sorted[i] for i in del_image_index if 0 <= i < len(file_names_sorted)]
    for remove_image in del_image_path:
        os.remove(remove_image)
