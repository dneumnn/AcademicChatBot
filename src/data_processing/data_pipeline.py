import os
import subprocess
from dotenv import load_dotenv
import pandas as pd
import csv

import requests

# Import other functions of the data_processing package
from .video_metadata_download import *
from .audio_processing import *
from .chunk_processing import *
from .visual_processing import *
from .embeddings import *
from .logger import log, create_log_file, write_empty_line

# Import other functions of the DB packages
from src.db.graph_db.main import *
# from src.db.graph_db.db_handler import GraphHandler
from src.db.graph_db.utilities import *
from src.vectordb.main import *

# Env variables Data Pre-Processing
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")
PROCESSED_VIDEOS_PATH = os.getenv("PROCESSED_VIDEOS_PATH")
TOPIC_OVERVIEW_PATH = os.getenv("TOPIC_OVERVIEW_PATH")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")

# Create log file
create_log_file(LOG_FILE_PATH)

# Env variables Database Connection
# GRAPHDB_URI = os.getenv("GRAPHDB_URI")
# GRAPHDB_USER = os.getenv("GRAPHDB_USER")
# GRAPHDB_PASSWORD = os.getenv("GRAPHDB_PASSWORD")

# graph_handler = GraphHandler(GRAPHDB_URI, GRAPHDB_USER, GRAPHDB_PASSWORD)

# ********************************************************
# * Final pipeline function

def download_pipeline_youtube(url: str, chunk_max_length: int=550, chunk_overlap_length: int=50, seconds_between_frames: int=120, max_limit_similarity: float=0.85, local_model: bool = False, enabled_detailed_chunking: bool = False):
    """
    Pipeline for processing YouTube videos and their content.

    This method defines the pipeline for processing a YouTube video or playlist. It handles downloading the content
    and processing both the audio and visual elements. It uses multiple modular functions from the data_processing package,
    ensuring a clear separation between technical implementation details and the overall structural overview.

    Args:
        url (str): URL of the YouTube video or playlist.
        chunk_max_length (int, optional): Maximum length of character of each chunk.
        chunk_overlap_length (int, optional): Number of characters each chunk is overlapping.
        seconds_between_frames (int, optional): How many seconds should pass between the extracted frames.
        local_model (bool, optional): False: a Gemini model using an API key is used. True: A local Ollama model is used.
        enabled_detailed_chunking (bool, optional): False: A simpler, sentence-based chunking method is used. True: A detailed, LLM-based chunking method is used. 

    Returns:
        status_code (int): The status code that should be returned by the Fast API endpoint.
        status_message (str). A message about the status that should be returned by the Fast API endpoint.
    Check the README of this package for more insights into the possible returned status codes.

    Example:
        download_pipeline_youtube("https://www.youtube.com/watch?v=example")
    """

    write_empty_line("src/data_processing/data-processing.log")
    log.info("download_pipeline_youtube: Start data pipeline.")
    log.info("download_pipeline_youtube: Parameter 1: url = %s", url)
    log.info("download_pipeline_youtube: Parameter 2: chunk_max_length = %s", chunk_max_length)
    log.info("download_pipeline_youtube: Parameter 3: chunk_overlap_length = %s", chunk_overlap_length)
    log.info("download_pipeline_youtube: Parameter 4: seconds_between_frames = %s", seconds_between_frames)
    log.info("download_pipeline_youtube: Parameter 5: max_limit_similarity = %s", max_limit_similarity)
    log.info("download_pipeline_youtube: Parameter 6: local_model = %s", local_model)
    log.info("download_pipeline_youtube: Parameter 7: enabled_detailed_chunking = %s", enabled_detailed_chunking)

    # Check if passed parameters are valid
    if chunk_max_length < 1:
        log.error("download_pipeline_youtube: chunk_max_length input invalid.")
        return 500, "YouTube content could not be processed: The chunk_max_length parameter cannot be below 1!"
    if chunk_overlap_length < 1:
        log.error("download_pipeline_youtube: chunk_overlap_length input invalid.")
        return 400, "YouTube content could not be processed: The chunk_overlap_length parameter cannot be below 1!"
    if chunk_max_length < chunk_overlap_length:
        log.error("download_pipeline_youtube: chunk_max_length and chunk_overlap_length combination input invalid.")
        return 400, "YouTube content could not be processed: The chunk_max_length parameter cannot be below the chunk_overlap_length parameter!"
    if seconds_between_frames < 1:
        log.error("download_pipeline_youtube: seconds_between_frames input invalid.")
        return 400, "YouTube content could not be processed: The parameter seconds_between_frames cannot be below 1!"
    if max_limit_similarity < 0.1:
        log.error("download_pipeline_youtube: max_limit_similarity input invalid.")
        return 400, "YouTube content could not be processed: The parameter max_limit_similarity cannot be below 0.1!"
    if max_limit_similarity > 1:
        log.error("download_pipeline_youtube: max_limit_similarity input invalid.")
        return 400, "YouTube content could not be processed: The parameter max_limit_similarity cannot be above 1.0!"
    log.info("download_pipeline_youtube: All variables checks passed.")
    
    # Validate ENV Variables
    required_env_vars = ["PROCESSED_VIDEOS_PATH", "TOPIC_OVERVIEW_PATH", "LOG_FILE_PATH"]
    for env_var in required_env_vars:
        env_var_value = os.getenv(env_var)
        if not env_var_value:
            log.error("download_pipeline_youtube: Variable %s not set.", env_var)
            return 424, f"Env variable '{env_var}' is not set. Please contact a developer."
    log.info("download_pipeline_youtube: All required env variables are set.")

    # Validate API Key or check for local ollama
    if not local_model:
        # Validate gemini API
        api_key = os.getenv("API_KEY_GOOGLE_GEMINI")
        print(api_key)
        if not api_key:
            return 424, "Error while trying to fetch the Gemini API. Please provide an API key!"
        gemini_url = f'https://generativelanguage.googleapis.com/v1beta2/models?key={api_key}'
        response = requests.get(gemini_url)
        if response.status_code == 200:
            log.info("download_pipeline_youtube: Gemini API call test succeeded!")
        else:
            log.error("download_pipeline_youtube: Gemini API call test failed!: %s.", response.status_code)
            return 424, "Error while trying to fetch the Gemini API. Please provide a valid API key and check your internet connection."
    else:
        # Check local ollama models
        required_models = ["llama3.2-vision", "nomic-embed-text", "llama3.2"]
        for model in required_models:
            check_passed, message = model_exists(model)
            if not check_passed:
                log.info("download_pipeline_youtube: Error while validating the local model: %s.", message)
                return 424, f"Error while validating the local model: {message}. Please contact a developer."
        log.info("download_pipeline_youtube: Required local models were found.")

    chunk_length = chunk_max_length - chunk_overlap_length
    video_urls = []
    processed_video_titles = []

    # * Load url(s) in the video_urls list
    # Also check if the URL type is a valid YouTube video/ playlist
    if "watch" in url and "list" not in url:
        log.info("download_pipeline_youtube: %s is a YouTube video.", url)
        video_urls.append(url)
    elif "list" in url:
        log.info("download_pipeline_youtube: %s is a YouTube playlist.", url)
        video_urls = extract_video_urls_from_playlist(url)
    elif "shorts" in url:
        log.warning("download_pipeline_youtube: %s is a YouTube short. Not supported.", url)
        return 415, "The URL is a shorts video. Shorts are not supported, please provide a video or playlist URL."
    elif "@" in url:
        log.warning("download_pipeline_youtube: %s is a YouTube channel. Not supported.", url)
        return 415, "The URL is a channel. This is not supported, please provide a video or playlist URL."
    else:
        log.warning("download_pipeline_youtube: %s is neither a YouTube video nor a playlist.", url)
        return 415, "The URL is a valid YouTube URL, but neither a video nor a playlist."

    # * Try to download and process the list of YouTube videos
    for video_url in video_urls:
        # Set needed result variables
        video_id = extract_youtube_video_id(video_url)
        meta_data = {}

        # * Download video
        if video_with_id_already_downloaded(video_id):
            log.warning("download_pipeline_youtube: Video with ID %s was already downloaded and analyzed.", video_id)
            continue
        try:
            log.info("download_pipeline_youtube: %s is a new URL!", url)
            download_youtube_video_pytube(video_url)
        except:
            try:
                log.warning("download_pipeline_youtube: Downloading video %s with PyTube failed. Now trying to download it with yt_dlp.", video_id)
                download_youtube_video_yt_dlp(video_url)
            except:
                log.error("download_pipeline_youtube: Downloading video %s failed with both PyTube and yt_dlp.", video_id)
                return 500, "Internal error when trying to download the video. Please contact a developer."

        # * Extract meta data
        try:
            meta_data = extract_meta_data_pytube(video_url)
        except:
            try:
                log.warning("download_pipeline_youtube: Extracting meta data using PyTube failed. Now trying to extract it with yt_dlp.")
                meta_data = extract_meta_data_yt_dlp(video_url)
            except:
                log.error("download_pipeline_youtube: Extracting meta data failed with both PyTube and yt_dlp.")
                return 500, "Internal error when trying to extract the video meta data. Please contact a developer."

        # * Visual Processing: Extract frames with description
        try:
            # extract_frames_from_video(f"media/{video_id}/video/{video_id}.mp4", seconds_between_frames)
            extract_frames_from_video(video_id, seconds_between_frames)
            remove_duplicate_images(video_id, max_limit_similarity)
            create_image_description(video_id, local_model=local_model)
        except Exception as e:
            log.error("download_pipeline_youtube: The visual processing failed: %s.", e)
            return 500, "Internal error when trying to process the video visual. Please contact a developer."
        
        # * Audio Processing: Download and pre-process transcripts
        try:
            download_preprocess_youtube_transcript(video_url, local_model=local_model)
            # Read the downloaded transcript into the variable "processed_text_transcript"
            with open(f"media/{video_id}/transcripts/{video_id}.txt", "r", encoding="utf-8") as file: # TODO: maybe directly return through method
                processed_text_transcript = file.read()
        except Exception as e:
            log.error("download_pipeline_youtube: The audio processing failed: %s.", e)
            return 500, "Internal error when trying to process the video audio. Please contact a developer."

        # * Create Video Topic
        try:
            create_topic_video(video_id, meta_data['title'], processed_text_transcript)
        except Exception as e:
            log.error("download_pipeline_youtube: Transcript CSV could not be read: %s.", e)
            return 500, "Internal error when trying to read Transcript CSV File. Please contact a developer."

        # * Chunking: Append timestamps, merge sentences and add chunk overlap
        try:
            if not enabled_detailed_chunking:
                extracted_time_sentence = extract_time_and_sentences(processed_text_transcript)
                merged_sentence = merge_sentences_based_on_length(extracted_time_sentence, chunk_length)
                chunked_text = add_chunk_overlap(merged_sentence, chunk_overlap_length)
            else:
                detailed_llm_chunks = create_chunk_llm(processed_text_transcript)
                check_detailed_llm_chunks = check_llm_chucks(detailed_llm_chunks, chunk_max_length)
                format_detailed_llm_chunks = format_llm_chunks(check_detailed_llm_chunks)
                chunked_text = add_chunk_overlap(format_detailed_llm_chunks, chunk_overlap_length)
            append_meta_data(meta_data, video_id, chunked_text)
        except Exception as e:
            log.error("download_pipeline_youtube: The chunking failed: %s.", e)
            return 500, "Internal error when trying to chunk the video content. Please contact a developer."

        # * Embed text chunks
        # ! Deprecated
        try:
            embed_text_chunks(video_id)
        except Exception as e:
            log.error("download_pipeline_youtube: The embedding of the chunked data failed: %s.", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."

        # * Integrate data into VectorDB
        try:
            generate_vector_db(video_id)
        except Exception as e:
            log.error("download_pipeline_youtube: The embedding of the chunked data in VectorDB failed: %s.", e)
            return 500, "Internal error when trying to generate the vector db. Please contact a developer."

        # * Integrate data into GraphDB
        try:
            load_csv_to_graphdb(meta_data, video_id)
            log.info("download_pipeline_youtube: Transcripts CSV for video %s successfully inserted into the GraphDB.", video_id)
        except Exception as e:
            log.error("download_pipeline_youtube: Transcripts CSV for video %s could not be inserted into the GraphDB: %s.", video_id, e)
            return 500, "Internal error when trying Insert Data into GraphDB. Please contact a developer."

        processed_video_titles.append(meta_data['title']) # Add this video title to the list of successfully processed videos

    # * Log results and return appropriate message to the user
    if len(processed_video_titles) == 0:
        log.warning("download_pipeline_youtube: YouTube content for URL %s was already processed.", url)
        return 200, "YouTube content was already processed."
    elif len(processed_video_titles) == 1:
        log.info("download_pipeline_youtube: YouTube content for video %s successfully processed! ", url)
        return 200, f"YouTube video with title {processed_video_titles[0]} successfully processed!"
    else:
        log.info("download_pipeline_youtube: YouTube content for playlist %s successfully processed!", url)
        response = "YouTube playlist successfully processed!\nProcessed videos:\n\n"
        response += "\n".join([f"{i + 1}. {title}" for i, title in enumerate(processed_video_titles)])
        return 200, response


def video_with_id_already_downloaded(id: str):
    """
    Helper function.
    Check if the video with this ID has already been downloaded and processed.

    Args:
        id (str): ID of a YouTube video.

    Returns:
        bool: True if this video has already been processed, False if not.

    Example:
        url_already_downloaded("dQw4w9WgXcQ")
    """

    processed_video_path = PROCESSED_VIDEOS_PATH.replace("_video_id_", id)

    if not os.path.exists(processed_video_path):
        return False
    else:
        return True


def model_exists(model_name: str):
    """
    Helper function.
    Checks if a local ollama modell is available.

    Args:
        model_name (str): The mode name.
    
    Returns:
        bool: True if the model exists, False if not.
        message: Contains a message with additional information.
    
    Example:
        model_exists("llama3.2-vision")
    """
    try:
        # Get the list of available models
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        models = result.stdout.splitlines()
        # Check if the specified model is in the list
        return any(model_name in model for model in models), "Model not found"
    except subprocess.CalledProcessError as e:
        # Error occured while checking models
        return False, "Error occured"
    except FileNotFoundError:
        # Ollama command-line tool is not installed or not in PATH
        return False, "Ollama not found"
    