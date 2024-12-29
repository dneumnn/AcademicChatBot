import os
from dotenv import load_dotenv
import pandas as pd

# Import other functions of the data_processing package
from src.data_processing.video_metadata_download import *
from src.data_processing.audio_processing import *
from src.data_processing.chunk_processing import *
from src.data_processing.visual_processing import *

# Static variables
VIDEO_DIRECTORY = "./media/videos/"
PROCESSED_URLS_FILE = "./src/data_processing/extracted_urls.txt"
TRANSCRIPT_DIRECTORY = "./media/transcripts/"
TRANSCRIPT_CHUNKS_DIRECTORY = "./media/transcripts_chunks/"

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")


# ********************************************************
# * Final pipeline function

def download_pipeline_youtube(url: str):
    """
    Pipeline for processing YouTube videos and their content.

    This method defines the pipeline for processing a YouTube video or playlist. It handles downloading the content
    and processing both the audio and visual elements. It uses multiple modular functions from the data_processing package,
    ensuring a clear separation between technical implementation details and the overall structural overview.

    Args:
        url (str). URL of the YouTube video or playlist.

    Returns:
        status_code (int). The status code that should be returned by the Fast API schnittstelle.
        Check the README of this package for more insights into the possible returned status codes.

    Example:
        download_pipeline_youtube("https://www.youtube.com/watch?v=example")

    TODO:
        - Implement better error handling.
        - Implement better logging.
        - Make the directories in the other files matching.
        - Document in the README all LLMs that are being used.
        - Add better and more detailed comments.
    """

    video_urls = []

    # load url(s) in the video_urls list
    # TODO: Check other types of URLs, e.g. what happens, if an URL is passed, which belongs to a single video which is part of a playlist?
    if "watch" in url and "list" not in url:
        print(f"{url} is a youtube video")
        video_urls.append(url)
    elif "list" in url:
        print(f"{url} is a youtube playlist")
        video_urls = extract_video_urls_from_playlist(url)
    else:
        print(f"{url} is neither a youtube video nor a playlist")
        return 415

    # try to download the list of YouTube videos
    for video_url in video_urls:
        if url_already_downloaded(video_url):
            print("This URL was already downloaded and analyzed")
            continue
        try:
            print("This URL is new!")
            download_youtube_video_pytube(video_url)
        except:
            try:
                download_youtube_video_yt_dlp(video_url)
            except:
                return 500
        try:
            # TODO: Also add a second method for extracting meta data (similar to video download)
            meta_data = extract_meta_data(video_url)
            print(meta_data)

            videoid = extract_youtube_video_id(video_url)
            video_filepath = VIDEO_DIRECTORY + videoid + ".mp4"
            extract_frames_from_video(video_filepath, 60)

            # TODO: Implement better try-catch mechanism. This nested try-catch blocks are not good.
            try:
                create_image_description(videoid)
            except Exception as e:
                print(f"Error during creation of Image descriptions: {e}")

            try:
                download_preprocess_youtube_transcript(video_url)

                with open(f"{TRANSCRIPT_DIRECTORY}{videoid}.txt", "r") as file:
                    processed_text_transcript = file.read()

                extracted_time_sentence = extract_time_and_sentences(processed_text_transcript)
                merged_sentence = merge_sentences_based_on_length(extracted_time_sentence, 500)
                chunked_text = add_chunk_overlap(merged_sentence, 50)

                df = pd.DataFrame(chunked_text)
                df = df.rename(columns={"sentence":"chunks"})
                df.to_csv(f"{TRANSCRIPT_CHUNKS_DIRECTORY}{videoid}.csv", index=False)

                write_url_to_already_downloaded(video_url)

            except Exception as e:
                print(f"Error during transcript: {e}")
        except Exception as e:
            print(f"/analyze error: {e}")
            return 500
    return 200


def url_already_downloaded(url: str):
    """
    Check if the video or playlist with this URL has already been downloaded and processed.

    Args:
        url (str): URL of a YouTube video or playlist.

    Returns:
        bool: True if this URL has already been processed, False if not.

    Example:
        url_already_downloaded("https://www.youtube.com/playlist?v=example")
    """

    # Check if the file exists
    if not os.path.exists(PROCESSED_URLS_FILE):
        return False

    with open(PROCESSED_URLS_FILE, 'r') as file:
        for line in file:
            if line.strip() == url:
                return True
    return False


def write_url_to_already_downloaded(url: str):
    """
    Write the URL to the list of already downloaded and processed video or playlists.

    Args:
        url (str): URL of a YouTube video or playlist.

    Example: 
        write_url_to_already_downloaded("https://www.youtube.com/playlist?v=example")
    """
    with open(PROCESSED_URLS_FILE, 'a') as file:
        file.write(url + '\n')

