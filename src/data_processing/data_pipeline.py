import os
from dotenv import load_dotenv
import pandas as pd

# Import other functions of the data_processing package
from .video_metadata_download import *
from .audio_processing import *
from .chunk_processing import *
from .visual_processing import *
from .embeddings import *
from .logger import log, create_log_file, write_empty_line

# Static variables
VIDEO_DIRECTORY = "./media/"
PROCESSED_URLS_FILE = "./src/data_processing/extracted_urls.txt"

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")

# Create log file
create_log_file("src/data_processing/data-processing.log")


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
        status_code (int). The status code that should be returned by the Fast API schnittstelle.
        Check the README of this package for more insights into the possible returned status codes.

    Example:
        download_pipeline_youtube("https://www.youtube.com/watch?v=example")

    TODO:
        - Implement better error handling.
        - Document in the README all LLMs that are being used.
        - Add better and more detailed comments.
    """

    write_empty_line("src/data_processing/data-processing.log")
    log.info("download_pipeline_youtube: Start data pipeline.")

    chunk_length = chunk_max_length - chunk_overlap_length
    video_urls = []

    # load url(s) in the video_urls list
    # TODO: Check other types of URLs, e.g. what happens, if an URL is passed, which belongs to a single video which is part of a playlist?
    if "watch" in url and "list" not in url:
        log.info("download_pipeline_youtube: %s is a YouTube video.", url)
        video_urls.append(url)
    elif "list" in url:
        log.info("download_pipeline_youtube: %s is a YouTube playlist.", url)
        video_urls = extract_video_urls_from_playlist(url)
    else:
        log.warning("download_pipeline_youtube: %s is neither a YouTube video nor a playlist.", url)
        return 415

    # try to download the list of YouTube videos
    for video_url in video_urls:
        videoid = extract_youtube_video_id(video_url)

        if url_already_downloaded(videoid):
            log.warning("download_pipeline_youtube: %s was already downloaded and analyzed.", url)
            continue
        try:
            log.info("download_pipeline_youtube: %s is a new URL!", url)
            download_youtube_video_pytube(video_url)
        except:
            try:
                log.warning("download_pipeline_youtube: Downloading video with PyTube failed. Now trying to download it with yt_dlp.")
                download_youtube_video_yt_dlp(video_url)
            except:
                return 500

        # TODO: Implement better try-catch mechanism. They are not nested anymore, but the called functions can be further improved.
        try:
            # TODO: Also add a second method for extracting meta data (similar to video download)
            meta_data = extract_meta_data(video_url)
            # print(meta_data)

            video_filepath = f"{VIDEO_DIRECTORY}/{videoid}/video/{videoid}.mp4"
            extract_frames_from_video(video_filepath, 10)

            create_image_description(videoid) # download_pipeline_youtube: Error during creation of image descriptions: %s

            download_preprocess_youtube_transcript(video_url) # start another try block here

            # Read the downloaded transcript into the variable "processed_text_transcript"
            with open(f"media/{videoid}/transcripts/{videoid}.txt", "r") as file:
                processed_text_transcript = file.read()

            extracted_time_sentence = extract_time_and_sentences(processed_text_transcript)
            merged_sentence = merge_sentences_based_on_length(extracted_time_sentence, chunk_length)
            chunked_text = add_chunk_overlap(merged_sentence, chunk_overlap_length)

            # Rename column "sentence" into "chunks" for the chunked data
            df = pd.DataFrame(chunked_text)
            df = df.rename(columns={"sentence":"chunks"})
            transcript_chunks_path = f"media/{videoid}/transcripts_chunks/"
            if not os.path.exists(transcript_chunks_path):
                os.makedirs(transcript_chunks_path)
            df.to_csv(f"media/{videoid}/transcripts_chunks/{videoid}.csv", index=False)

            log.info("download_pipeline_youtube: The video with URL %s was successfully processed!", url) # ends here with: download_pipeline_youtube: Error during transcript: %s

            embed_text_chunks(videoid, embedding_model) # try: download_pipeline_youtube: Error during embedding: %s

        except Exception as e:
            log.error("download_pipeline_youtube: /analyze error: %s", e)
            return 500
    return 200


def url_already_downloaded(id: str):
    """
    Check if the video or playlist with this URL has already been downloaded and processed.

    Args:
        url (str): URL of a YouTube video or playlist.

    Returns:
        bool: True if this URL has already been processed, False if not.

    Example:
        url_already_downloaded("https://www.youtube.com/playlist?v=example")
    """

    if not os.path.exists(f"./media/{id}"):
        return False
    else:
        return True

