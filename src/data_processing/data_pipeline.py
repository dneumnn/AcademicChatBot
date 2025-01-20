import os
from dotenv import load_dotenv
import pandas as pd
import csv

# Import other functions of the data_processing package
from .video_metadata_download import *
from .audio_processing import *
from .chunk_processing import *
from .visual_processing import *
from .embeddings import *
from .logger import log, create_log_file, write_empty_line

# Import other functions of the graphDB package
from src.db.graph_db.main import *
# from src.db.graph_db.db_handler import GraphHandler
from src.db.graph_db.utilities import *

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

def download_pipeline_youtube(url: str, chunk_max_length: int=550, chunk_overlap_length: int=50, seconds_between_frames: int=30, local_model: bool = False, enabled_detailed_chunking: bool = False):
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
    log.info("download_pipeline_youtube: Parameter 5: local_model = %s", local_model)
    log.info("download_pipeline_youtube: Parameter 6: enabled_detailed_chunking = %s", enabled_detailed_chunking)

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
            create_image_description(video_id, local_model=local_model)
        except Exception as e:
            log.error("download_pipeline_youtube: The visual processing failed: %s", e)
            return 500, "Internal error when trying to process the video visual. Please contact a developer."
        
        # * Audio Processing: Download and pre-process transcripts
        try:
            download_preprocess_youtube_transcript(video_url, local_model=local_model)
            # Read the downloaded transcript into the variable "processed_text_transcript"
            with open(f"media/{video_id}/transcripts/{video_id}.txt", "r") as file: # TODO: maybe directly return through method
                processed_text_transcript = file.read()
        except Exception as e:
            log.error("download_pipeline_youtube: The audio processing failed: %s", e)
            return 500, "Internal error when trying to process the video audio. Please contact a developer."

        # TODO: Comment and clean up from here on
        # * Chunking: Append timestamps, merge sentences and add chunk overlap
        try:
            extracted_time_sentence = extract_time_and_sentences(processed_text_transcript)
            merged_sentence = merge_sentences_based_on_length(extracted_time_sentence, chunk_length)
            chunked_text = add_chunk_overlap(merged_sentence, chunk_overlap_length)

            # TODO: Place 
            # Rename column "sentence" into "chunks" for the chunked data csv
            df = pd.DataFrame(chunked_text)
            df = df.rename(columns={"sentence":"chunks"})
            transcript_chunks_path = f"media/{video_id}/transcripts_chunks/"
            if not os.path.exists(transcript_chunks_path):
                os.makedirs(transcript_chunks_path)

            # TODO: Place before chunking
            # Create topic_overview.csv if it does not already exist
            VIDEO_TOPIC_OVERVIEW_FILEPATH = "/media/video_topic_overview.csv"
            if not os.path.exists(VIDEO_TOPIC_OVERVIEW_FILEPATH):
                os.makedirs(os.path.dirname(VIDEO_TOPIC_OVERVIEW_FILEPATH), exist_ok=True)
                df_video_topic_overview = pd.DataFrame(columns=["video_id", "video_topic"])
                df_video_topic_overview.to_csv(VIDEO_TOPIC_OVERVIEW_FILEPATH, index=False)
            
            # * Create Video Topic and Update Chunked Data
            try:
                create_topic_video(video_id, meta_data['title'], processed_text_transcript)
            except Exception as e:
                log.error("download_pipeline_youtube: Transcript CSV could not be read: %s", e)
                return 500, "Internal error when trying to read Transcript CSV File. Please contact a developer."
            
            df_video_topic_overview = pd.read_csv(VIDEO_TOPIC_OVERVIEW_FILEPATH)
            df_video_topic_overview_filtered = df_video_topic_overview[df_video_topic_overview["video_id"] == video_id]
            topic = df_video_topic_overview_filtered["video_topic"].iloc[0] if not df_video_topic_overview_filtered.empty else None

            df["video_id"] = meta_data["id"]
            df["video_topic"] = topic
            df["video_title"] = meta_data["title"]
            df["video_uploaddate"] = meta_data["upload_date"]
            df["video_duration"] = meta_data["duration"]
            df["channel_url"] = meta_data["uploader_url"] 
            
            df.to_csv(f"media/{video_id}/transcripts_chunks/{video_id}.csv", index=False)
        except Exception as e:
            log.error("download_pipeline_youtube: The chunking failed: %s", e)
            return 500, "Internal error when trying to chunk the video content. Please contact a developer."

        # * Embed text chunks
        try:
            embed_text_chunks(video_id)
        except Exception as e:
            log.error("download_pipeline_youtube: The embedding of the chunked data failed: %s", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."

        # * Integrate data into GraphDB
        try:
            load_csv_to_graphdb(meta_data, video_id)
            log.info("download_pipeline_youtube: Transcripts CSV for video %s successfully inserted into the GraphDB.", video_id)
        except Exception as e:
            log.error("download_pipeline_youtube: Transcripts CSV for video %s could not be inserted into the GraphDB: %s", video_id, e)
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

    processed_video_path = PROCESSED_VIDEOS_PATH.replace("_videoid_", id)

    if not os.path.exists(processed_video_path):
        return False
    else:
        return True

