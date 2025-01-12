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
from src.db.graph_db.db_handler import GraphHandler
from src.db.graph_db.utilities import *

# Static variables
VIDEO_DIRECTORY = "./media/"
LOG_FILE_PATH = "src/data_processing/data-processing.log"

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")

# Create log file
create_log_file(LOG_FILE_PATH)

# Database Connection
uri = "bolt://localhost:7687"
user = "neo4j"
password = "this_pw_is_a_test25218###1119jj"

graph_handler = GraphHandler(uri, user, password)

# ********************************************************
# * Final pipeline function

def download_pipeline_youtube(url: str, chunk_max_length: int=550, chunk_overlap_length: int=50, embedding_model: str="nomic-embed-text"):
    """
    Pipeline for processing YouTube videos and their content.

    This method defines the pipeline for processing a YouTube video or playlist. It handles downloading the content
    and processing both the audio and visual elements. It uses multiple modular functions from the data_processing package,
    ensuring a clear separation between technical implementation details and the overall structural overview.

    Args:
        url (str): URL of the YouTube video or playlist.
        chunk_max_length (int): Maximum length of character of each chunk.
        chunk_overlap_length (int): Number of characters each chunk si overlapping.

    Returns:
        status_code (int): The status code that should be returned by the Fast API endpoint.
        status_message (str). A message about the status that should be returned by the Fast API endpoint.
    Check the README of this package for more insights into the possible returned status codes.

    Example:
        download_pipeline_youtube("https://www.youtube.com/watch?v=example")

    TODO:
        - Document in the README all LLMs that are being used.
        - Add enhanced images in /images.
        - Add placeholder .env.
    """

    write_empty_line("src/data_processing/data-processing.log")
    log.info("download_pipeline_youtube: Start data pipeline.")
    log.info("download_pipeline_youtube: Parameter 1: url = %s", url)
    log.info("download_pipeline_youtube: Parameter 2: chunk_max_length = %s", chunk_max_length)
    log.info("download_pipeline_youtube: Parameter 3: chunk_overlap_length = %s", chunk_overlap_length)
    log.info("download_pipeline_youtube: Parameter 4: embedding_model = %s", embedding_model)

    chunk_length = chunk_max_length - chunk_overlap_length
    video_urls = []
    processed_video_titles = []

    # * Load url(s) in the video_urls list
    # TODO: Check other types of URLs, e.g. what happens, if an URL is passed, which belongs to a single video which is part of a playlist?
    if "watch" in url and "list" not in url:
        log.info("download_pipeline_youtube: %s is a YouTube video.", url)
        video_urls.append(url)
    elif "list" in url:
        log.info("download_pipeline_youtube: %s is a YouTube playlist.", url)
        video_urls = extract_video_urls_from_playlist(url)
    else:
        log.warning("download_pipeline_youtube: %s is neither a YouTube video nor a playlist.", url)
        return 415, "The URL is a valid YouTube URL, but neither a video nor a playlist."

    # * Try to download and process the list of YouTube videos
    for video_url in video_urls:
        # Set needed variables
        video_id = extract_youtube_video_id(video_url)
        video_filepath = f"{VIDEO_DIRECTORY}/{video_id}/video/{video_id}.mp4"
        meta_data = {}

        # * Download video
        if video_with_id_already_downloaded(video_id):
            log.warning("download_pipeline_youtube: video with ID %s was already downloaded and analyzed.", video_id)
            continue
        try:
            log.info("download_pipeline_youtube: %s is a new URL!", url)
            download_youtube_video_pytube(video_url)
        except:
            try:
                log.warning("download_pipeline_youtube: Downloading video with PyTube failed. Now trying to download it with yt_dlp.")
                download_youtube_video_yt_dlp(video_url)
            except:
                log.error("download_pipeline_youtube: Download failed with both PyTube and yt_dlp.")
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
            extract_frames_from_video(video_filepath, 30)
            create_image_description(video_id)
        except Exception as e:
            log.error("download_pipeline_youtube: The visual processing failed: %s", e)
            return 500, "Internal error when trying to process the video visual. Please contact a developer."
        
        # * Audio Processing: Download and pre-process transcripts
        try:
            download_preprocess_youtube_transcript(video_url)
            # Read the downloaded transcript into the variable "processed_text_transcript"
            with open(f"media/{video_id}/transcripts/{video_id}.txt", "r") as file:
                processed_text_transcript = file.read()
        except Exception as e:
            log.error("download_pipeline_youtube: The audio processing failed: %s", e)
            return 500, "Internal error when trying to process the video audio. Please contact a developer."

        # * Chunking: Append timestamps, merge sentences and add chunk overlap
        try:
            extracted_time_sentence = extract_time_and_sentences(processed_text_transcript)
            merged_sentence = merge_sentences_based_on_length(extracted_time_sentence, chunk_length)
            chunked_text = add_chunk_overlap(merged_sentence, chunk_overlap_length)

            # Rename column "sentence" into "chunks" for the chunked data csv
            df = pd.DataFrame(chunked_text)
            df = df.rename(columns={"sentence":"chunks"})
            transcript_chunks_path = f"media/{video_id}/transcripts_chunks/"
            if not os.path.exists(transcript_chunks_path):
                os.makedirs(transcript_chunks_path)
            df.to_csv(f"media/{video_id}/transcripts_chunks/{video_id}.csv", index=False)
        except Exception as e:
            log.error("download_pipeline_youtube: The chunking failed: %s", e)
            return 500, "Internal error when trying to chunk the video content. Please contact a developer."

        # * Embed text chunks
        try:
            embed_text_chunks(video_id, embedding_model)
        except Exception as e:
            log.error("download_pipeline_youtube: The embedding of the chunked data failed: %s", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."
        
        try:
            create_topic_video(video_id, meta_data['title'], processed_text_transcript)
        except:
            print("Error topic definition")

        # * Insert Meta Data into graph_db       
        try:
            graph_handler.create_meta_data_session(meta_data)
        except Exception as e:
            log.error("download_pipeline_youtube: Creation of Meta data Node failed: %s", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."
        try:
            chunks = read_csv_chunks(video_id, meta_data)
        except Exception as e:
            log.error("download_pipeline_youtube: Transcript CSV chunk could not be read: %s", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."
        try:
            graph_handler.create_transcript_chunk_session(chunks)
        except Exception as e:
            log.error("download_pipeline_youtube: Creation of Transcript Chunk Node failed: %s", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."
        try:
            graph_handler.create_chunk_next_relation_session(chunks)
            graph_handler.create_chunk_metadata_relation_session(chunks, meta_data)
        except Exception as e:
            log.error("download_pipeline_youtube: Creation of Transcript Chunk relations failed: %s", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."
        try:
            graph_handler.create_chunk_similarity_relation_session(chunks, video_id)
        except Exception as e:
            log.error("download_pipeline_youtube: Creation of Transcript Chunk similarity relation failed: %s", e)
            return 500, "Internal error when trying to embed the chunked data. Please contact a developer."
        graph_handler.close()

        processed_video_titles.append(meta_data['title'])

    if len(processed_video_titles) == 0:
        log.info(f"YouTube content for URL {url} was already processed.")
        return 200, f"YouTube content was already processed."
    else:
        # TODO: Implement better format for the title(s)
        log.info("download_pipeline_youtube: The video with URL %s was successfully processed!", url)
        return 200, f"YouTube content with Title(s) {processed_video_titles} successfully processed."


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

    if not os.path.exists(f"{VIDEO_DIRECTORY}{id}"):
        return False
    else:
        return True

