import os
from pytube import (
    YouTube,
    Playlist
)

##########################################################
# Final pipeline function
##########################################################

def download_pipeline_youtube(url: str):
    """
    Download youtube video(s) from playlist or video url

    Args:
        url (str). URL of the YouTube video or playlist

    Example:
        download_pipeline_youtube("https://www.youtube.com/watch?v=example")
    """
    if "watch" in url and "list" not in url:
        print(f"{url} is a youtube video")
        download_youtube_video(url)

    elif "list" in url:
        print(f"{url} is a youtube playlist")

        video_urls = extract_youtube_video_url_from_playlist(url)
        for video_url in video_urls:
            download_youtube_video(video_url)

    else:
        print(f"{url} is neither a youtube video nor a playlist")


##########################################################


def download_youtube_video(url: str, resolution: str="720p"):
    """
    Download video from YouTube.

    Args:
        url (str): URL of the YouTube video.
    
    Raises:
        Exception: For errors during download.

    Example:
        download_youtube_video("https://www.youtube.com/watch?v=example", resolution="1080p")
    """
    try:
        save_path = "AcademicChatBot/media/download_videos/"
        os.makedirs(save_path, exist_ok=True)

        yt = YouTube(url)
        stream = yt.streams.filter(res=resolution).first()
        if stream is None:
            stream = yt.streams.get_highest_resolution()
        
        stream.download(output_path=save_path)
        print(f"Video download successfully to {save_path}")

    except Exception as e:
        print(f"Error occurred while downloading the youtube video: {e}")




def extract_youtube_video_url_from_playlist(url: str):
    """
    Extract all YouTube video links from a playlist.

    Args:
        url (str): URL of the YouTube playlist

    Returns:
        list[str]: List of video URLs from the playlist
    
    Example: 
        extract_youtube_video_url_from_playlist("https://www.youtube.com/playlist?list=PLexample")
    """
    try:
        playlist = Playlist(url)
        video_urls = [
            video_url for video_url in playlist.video_urls
        ]
        return video_urls
    
    except Exception as e:
        print(f"Error occurred while fetching playlist links: {e}")
        
