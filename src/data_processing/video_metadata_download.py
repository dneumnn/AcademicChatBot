import os
import re
import pandas as pd
from pytube import (
    YouTube,
    Playlist
)
import yt_dlp
from dotenv import load_dotenv
import google.generativeai as genai

from .logger import log

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")

def download_youtube_video_pytube(url: str, resolution: str = "720p") -> None:
    """
    Download video from YouTube using the pytube library.

    Args:
        url (str): URL of the YouTube video.
        resolution (str, optional): The desired resolution of the video. Defaults to "720p".
    
    Raises:
        Exception: For errors during download.

    Example:
        download_youtube_video_pytube("https://www.youtube.com/watch?v=example", resolution="1080p")
    """
    try:
        video_id = extract_youtube_video_id(url)
        save_path = f"{os.getenv('PROCESSED_VIDEOS_PATH').replace('_video_id_', video_id)}/video"
        os.makedirs(save_path, exist_ok=True)

        yt = YouTube(url)
        stream = yt.streams.filter(res=resolution).first()
        if stream is None:
            stream = yt.streams.get_highest_resolution()
        
        stream.download(output_path=save_path)
        log.info("download_youtube_video_pytube: PyTube video download successfull. Saved file to %s.", save_path)

    except Exception as e:
        log.warning("download_youtube_video_pytube: YouTube video download using pytube was unsuccessful: %s", e)
        raise e


def download_youtube_video_yt_dlp(url: str) -> None:
    """
    Download video from YouTube using the dlp library.

    Args:
        url (str): URL of the YouTube video.
    
    Raises:
        Exception: For errors during download.

    Example:
        download_youtube_video_yt_dlp("https://www.youtube.com/watch?v=example")
    """
    video_id = extract_youtube_video_id(url)
    save_path = f"{os.getenv('PROCESSED_VIDEOS_PATH').replace('_video_id_', video_id)}/video"
    os.makedirs(save_path, exist_ok=True)

    save_path = f"{save_path}/{video_id}.%(ext)s"

    ydl_opts = {
            'format': 'best',
            'outtmpl': save_path,
            'retries': 3,
            'geo_bypass': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        log.info("download_youtube_video_yt_dlp: yt_dlp video download successfull. Saved file to %s", save_path)
    except Exception as e:
        log.warning("download_youtube_video_yt_dlp: YouTube video download using yt-dlp was unsuccessful: %s", e)
        raise e


def extract_video_urls_from_playlist(url: str) -> list:
    """
    Extract all YouTube video links from a playlist.

    Args:
        url (str): URL of the YouTube playlist.

    Returns:
        list (str): List of video URLs from the playlist.
    
    Example: 
        extract_youtube_video_url_from_playlist("https://www.youtube.com/playlist?list=PLexample")
    """

    try:
        playlist = Playlist(url)
        video_urls = [
            video_url for video_url in playlist.video_urls
        ]
        log.info("extract_video_urls_from_playlist: Extracted %d videos from URL %s.", len(video_urls), url)
        return video_urls
    
    except Exception as e:
        log.warning("extract_video_urls_from_playlist: Extraction of YouTube URLs from playlist %s was unsuccessful: %s", url, e)
        raise e

    
def extract_meta_data_pytube(url: str) -> dict:
    """
    Extract the relevant meta data of a YouTube video using pytube.

    Args:
        url (str): URL of the YouTube video.
    
    Raises:
        Exception: For errors during meta data extraction.
    """
    try:
        yt = YouTube(url)

        meta_data = {}
        
        meta_data['id'] = yt.video_id
        meta_data['title'] = yt.title
        meta_data['description'] = yt.description
        meta_data['upload_date'] = yt.publish_date.strftime("%Y-%m-%d") if yt.publish_date else None
        meta_data['duration'] = yt.length  
        meta_data['view_count'] = yt.views
        meta_data['uploader_url'] = yt.channel_url
        meta_data['uploader_id'] = yt.author
        meta_data['channel_id'] = None  
        meta_data['uploader'] = yt.author
        meta_data['thumbnail'] = yt.thumbnail_url
        meta_data['like_count'] = None  
        meta_data['tags'] = yt.keywords
        meta_data['categories'] = None  
        meta_data['age_limit'] = None 

        log.info(
            "extract_meta_data_pytube: Extracted meta data for video with title %s from channel %s.",
            meta_data['title'], 
            meta_data['uploader']
        ) 

        return meta_data
    
    except Exception as e:
        log.warning("extract_meta_data_pytube: YouTube meta extraction data using pytube was unsuccessful: %s", e)
        raise e


def extract_meta_data_yt_dlp(url: str) -> dict:
    """
    Extract the relevant meta data of a YouTube video.

    Args:
        url (str): URL of the YouTube video.
    
    Raises:
        Exception: For errors during meta data extraction.
    """
    meta_data = {}

    ydl_opts = {
            'format': 'best',
            'retries': 3,
            'geo_bypass': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False) # Extract info

            meta_data['id'] = result.get('id')
            meta_data['title'] = result.get('title')
            meta_data['description'] = result.get('description')
            meta_data['upload_date'] = result.get('upload_date')
            meta_data['duration'] = result.get('duration')
            meta_data['view_count'] = result.get('view_count')
            meta_data['uploader_url'] = result.get('uploader_url')
            meta_data['uploader_id'] = result.get('uploader_id')
            meta_data['channel_id'] = result.get('channel_id')
            meta_data['uploader'] = result.get('uploader')
            meta_data['thumbnail'] = result.get('thumbnail')
            meta_data['like_count'] = result.get('like_count')
            meta_data['tags'] = result.get('tags')
            meta_data['categories'] = result.get('categories')
            meta_data['age_limit'] = result.get('age_limit')

            log.info(
                "extract_meta_data_yt_dlp: Extracted meta data for video with title %s from channel %s.",
                meta_data['title'], 
                meta_data['uploader']
            )

            return meta_data

    except Exception as e:
        log.warning("extract_meta_data_yt_dlp: YouTube meta extraction data using yt-dlp was unsuccessful: %s", e)
        raise e


def extract_youtube_video_id(url: str) -> str:
    """
    Extract YouTube video id from YouTube video.

    Args:
        url (str): URL of a YouTube video.

    Returns:
        video_id (str): ID of the YouTube video.

    Example:
        extract_youtube_video_id("https://www.youtube.com/playlist?v=example")
    """

    video_id = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
    if video_id:
        return video_id.group(1)
    else:
        log.warning("YouTube Video ID could not be extracted from the URL")
        raise ValueError("YouTube Video ID could not be extracted from the URL")


def create_topic_video(videoid: str, video_title: str, video_transcript: str, video_transcript_len: int = 500, gemini_model: str = "gemini-1.5-flash"):
    """
    Create chunks based on LLM.

    Args:
        text (str): text input.
        max_chunk_length (int): max. character length of the chunks.
        gemini_model (str): version of the gemini model.
    
    Returns:
        List of chunks.

    """
    transcript_cleaned = re.sub(r'\s+', ' ', re.sub(r'\{.*?\}', '', video_transcript)).strip()[:video_transcript_len].rsplit(' ', 1)[0] if len(video_transcript) > video_transcript_len else video_transcript
    csv_path = os.getenv("TOPIC_OVERVIEW_PATH")

    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)
    prompt = (
        f"""
        Based on the provided information, categorize the following YouTube video into a broad topic area such as Data Science, Web Development, Digital Marketing, Health and Wellness, Gaming, etc.

        You should infer the most appropriate topic for the video based on its title and the beginning of its transcript. If the information is unclear or spans multiple categories, choose the most relevant one or state "Unclear" if no category can be determined.

        Video title: {video_title}
        Video transcript start: {transcript_cleaned}

        Please provide your response in the format:
        [Insert Topic]
        """
    )
    
    response = model.generate_content(prompt)
    response = response.text

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)

        unique_topics = df["video_topic"].unique()

        prompt = f"""
        Consider the topic: {response}. Compare it with the following list of predefined topics: {unique_topics}. 

        1. If '{response}' closely matches any of the predefined topics, return the matching topic.
        2. If there is no close match, return '{response}' as it is.

        Ensure the comparison accounts for synonymous terms or slight variations in phrasing.

        Please provide your response in the format:
        [Insert Topic]
        """
        final_topic = model.generate_content(prompt)
        final_topic = final_topic.text

        new_row = {"video_id": videoid, "video_topic": final_topic}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    else:
        # Create topic_overview.csv if it does not already exist
        df = pd.DataFrame([{"video_id": videoid, "video_topic": response}])
    
    df.to_csv(csv_path, index=False)

