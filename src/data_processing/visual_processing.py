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
from .logger import log, clean_up_logger

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")


def extract_frames_from_video(video_id: str, interval_in_sec: int = 30):
    """
    Extract a certain number of frames of a YouTube video.

    Args:
        video_id (str): The ID of the video that should be processed.
        interval_in_sec (int, optional): Interval in seconds between each frame to be extracted. This specifies how frequently frames are captured from the video.

    Example:
        extract_frames_from_video("ndm5Xsq45jM", 50)
    """

    log.info("extract_frames_from_video: Begin extraction of video frames for video with ID %s.", video_id)

    # Extract filename from file path # ! Deprecated
    # filename = re.search(r"video/(.+?)\.mp4", save_path).group(1)
    # if not os.path.exists(f"./media/{filename}/frames/"):
    #     os.makedirs(f"./media/{filename}/frames/")

    frames_folder = f"{os.getenv('PROCESSED_VIDEOS_PATH').replace('_video_id_', video_id)}/frames"
    if not os.path.exists(frames_folder):
        os.makedirs(frames_folder)

    # Calculate interval in frames
    cam = cv2.VideoCapture(f"{os.getenv('PROCESSED_VIDEOS_PATH').replace('_video_id_', video_id)}/video/{video_id}.mp4")
    video_fps = cam.get(cv2.CAP_PROP_FPS)
    interval_in_frames = round(video_fps * interval_in_sec)
    log.info(f"extract_frames_from_video: Calculated frames interval = {interval_in_frames}.")

    # Extract frames
    success, image = cam.read()
    count = 0
    extracted_frames = 0
    logging_done = True
    while success:
        if count % interval_in_frames == 0:
            log.debug(f"extract_frames_from_video: Extracting frame {count} for video with ID {video_id}.")
            timestamp_ms = cam.get(cv2.CAP_PROP_POS_MSEC)
            cv2.imwrite(f"{frames_folder}/frame{count}_{timestamp_ms}.jpg", image)
            extracted_frames += 1
            logging_done = False
        success, image = cam.read()
        count += 1
        if(extracted_frames % 15) == 0 and not logging_done:
            log.info("extract_frames_from_video: Successfully extracted 15 frames.")
            logging_done = True
    if not extracted_frames % 15 == 0:
        remaining_frames_to_log = extracted_frames % 15
        log.info("extract_frames_from_video: Successfully extracted %s frames.", remaining_frames_to_log)
    log.info("extract_frames_from_video: Successfully extracted %s frames from the video in total.", extracted_frames)


def create_image_description(video_id: str, gemini_model: str="gemini-1.5-flash", local_model:bool=False, local_llm:str="llama3.2-vision"):
    """
    Extract a certain number of frames of a YouTube video.

    Args:
        video_id (str): The ID of the video that should be processed.
        gemini_model (int, optional): The used gemini genai model. Defaults to 'gemini-1.5-flash'.
        local_model (bool, optional): False: a Gemini model using an API key is used. True: A local Ollama model is used.
        local_llm (str, optional): The used local genai model. Defaults to 'llama3.2-vision'

    Example:
        create_image_description("njjBbKpkmFI", "gemini-1.5-flash")
    """

    if not local_model:
        log.info("create_image_description: Start creating image descriptions for video with ID %s using %s as LLM.", video_id, gemini_model)
    else:
        log.info("create_image_description: Start creating image descriptions for video with ID %s using %s as LLM.", video_id, local_llm)
    # Configure and load genai model
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)

    # Paths
    frames_path_dir = f"{os.getenv('PROCESSED_VIDEOS_PATH').replace('_video_id_', video_id)}/frames"
    path_dir_frame_desc = f"{frames_path_dir.replace('/frames', '/frames_description')}"
    file_frame_desc = "frame_descriptions.csv"

    all_image_files = os.listdir(frames_path_dir)

    descriptions = []

    requests_made = 0
    # Iterate through all image files
    for file in all_image_files:
        image_file_path = frames_path_dir + "/" + file
        image_file = PIL.Image.open(image_file_path)

        prompt = (
                "Describe the extracted image from the instructional video, focusing solely on the relevant content related to "
                "the subject of the lesson: AI. Ignore irrelevant elements such as facecams or placeholders that are not related to "
                "the topic. Focus on describing concepts, diagrams, graphs, key points, or any other visual content in the image. "
                "If key points or visual representations of constructs, concepts, or models are shown, place them in context, "
                "explain their significance, and describe how they relate to the topic. Provide a coherent text block, with no formatting, "
                "bullet points, or other structural elements, just a clear and concise explanation of the image content. Also no line breaks or other special characters!"
            )

        if not local_model:
            if requests_made >= 10:
                log.info("create_image_descriptions: Successfully created %s image descriptions.", requests_made)
                log.warning("create_image_description: Too many API calls. Sleep for 60 seconds.")
                time.sleep(60)
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
                    "images": [image_file_path]
                }]
            )
            clean_up_logger()
            if requests_made >= 10:
                log.info("create_image_descriptions: Successfully created %s image descriptions.", requests_made)
                requests_made = 0

        if not os.path.exists(path_dir_frame_desc):
            os.makedirs(path_dir_frame_desc)


        # Save response in a designated file
        filename = file.replace(".jpg", "")        
        timestamp_ms = filename.split("_", 1)[1]
        filename = filename.split("_",1)[0]
        frame_time_s = float(timestamp_ms) / 1000
        if not local_model:
            descriptions.append({"video_id": video_id, "file_name": filename, "description": response.text.strip(), "time_in_s": frame_time_s})
        else:
            descriptions.append({"video_id": video_id, "file_name": filename, "description": response.message.content.strip(), "time_in_s": frame_time_s})
        log.debug("creating_image_description: Successfully created an image description for file %s.", filename)

    df = pd.DataFrame(descriptions)
    df.to_csv(f"{path_dir_frame_desc}/{file_frame_desc}", index=False)

    log.info("creating_image_description: Successfully described all %s images for video with ID %s.", len(descriptions), video_id)


def extract_number(filename):
    """
    Extracts numeric frame id from a file name based on a specific pattern and returns it.
    Helper function for remove_duplicate_images.

    Args:
        filename (str): The name of the file to process.

    Returns:
        int or float: The extracted number as an integer if the pattern is matched, 
                      or infinity (float('inf')) if no match is found.
    """
    match = re.search(r'frame(\d+)_', filename)
    return int(match.group(1)) if match else float('inf')


def remove_duplicate_images(video_id:str, threshold: int=0.9):
    """
     Args:
        image_folder_path (str): Path to the folder containing the images to process.
        threshold (float): Similarity threshold above which images are considered 
            duplicates. Default is 0.9.

    Returns:
        None: The function modifies the folder by deleting duplicate images.
    """
    log.info("remove_duplicate_images: Start removal of image duplicates using %s as the threshold.", threshold)
    frames_path_dir = f"{os.getenv('PROCESSED_VIDEOS_PATH').replace('_video_id_', video_id)}/frames"

    file_names = [
        file for file in os.listdir(frames_path_dir)
        if os.path.isfile(os.path.join(frames_path_dir, file))
    ]
    log.info("remove_duplicate_images: Found %s images to compare.", len(file_names))

    file_names_sorted = sorted(file_names, key=extract_number)

    file_names_sorted = [os.path.join(frames_path_dir, filename) for filename in file_names_sorted]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)

    if len(file_names_sorted) <= 1:
        log.warning("remove_duplicate_images: Skipped removing duplicate images, because less than two images are available.")
        return

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
    log.info("remove_duplicate_images: Removed %s images, as they seem to be duplicates. Kept %s unique images.", len(del_image_index), len(file_names)-len(del_image_index))
