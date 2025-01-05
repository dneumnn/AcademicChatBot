import os
import re
from pytube import (
    YouTube,
    Playlist
)
import yt_dlp

from .logger import log

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
        save_path = "media/"
        os.makedirs(save_path, exist_ok=True)

        yt = YouTube(url)
        stream = yt.streams.filter(res=resolution).first()
        if stream is None:
            stream = yt.streams.get_highest_resolution()
        
        stream.download(output_path=save_path)
        log.info("download_youtube_video_pytube: PyTube video download successfull. Saved file to %s.", save_path)

    except Exception as e:
        log.warning("YouTube video download using pytube was unsuccessful: %s", e)
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
    videoid = extract_youtube_video_id(url)

    ydl_opts = {
            'format': 'best',
            'outtmpl': f"media/{videoid}/video/{videoid}.%(ext)s",
            'retries': 3,
            'geo_bypass': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        log.info("download_youtube_video_yt_dlp: yt_dlp video download successfull. Saved file to /media/videos/%s.mp4.", videoid)
    except Exception as e:
        log.warning("YouTube video download using yt-dlp was unsuccessful: %s", e)
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
        log.info("extract_video_urls_from_playlist: Extracted %d videos from the %s URL.", len(video_urls), url)
        return video_urls
    
    except Exception as e:
        log.warning("Extraction of YouTube URLs from playlist was unsuccessful: %s", e)
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
        log.warning("YouTube meta extraction data using pytube was unsuccessful: %s", e)
        raise e


def extract_meta_data_yt_dlp(url: str) -> dict:
    """
    Extract the relevant meta data of a YouTube video.

    Args:
        url (str): URL of the YouTube video.
    
    Raises:
        Exception: For errors during meta data extraction.
    """
    videoid = extract_youtube_video_id(url)

    meta_data = {}

    ydl_opts = {
            'format': 'best',
            'outtmpl': f"media/{videoid}/video/{videoid}.%(ext)s",
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
        log.warning("YouTube meta extraction data using yt-dlp was unsuccessful: %s", e)
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

