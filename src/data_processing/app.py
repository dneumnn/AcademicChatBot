import os
from pytube import (
    YouTube,
    Playlist
)
from youtube_transcript_api import YouTubeTranscriptApi
from deepmultilingualpunctuation import PunctuationModel
from happytransformer import HappyTextToText
import yt_dlp

##########################################################
# Final pipeline function

def download_pipeline_youtube(url: str):
    """
    Download youtube video(s) from playlist or video url

    Args:
        url (str). URL of the YouTube video or playlist
    
    Returns:
        status_code (int). The status code that should be returned by Fast API.

    Example:
        download_pipeline_youtube("https://www.youtube.com/watch?v=example")
    """
    if "watch" in url and "list" not in url:
        print(f"{url} is a youtube video")

        try:
            download_youtube_video_pytube(url)
            return 200
        except:
            try:
                download_youtube_video_yt_dlp(url)
                return 200
            except:
                return 500

    elif "list" in url:
        print(f"{url} is a youtube playlist")

        video_urls = extract_video_urls_from_playlist(url)
        for video_url in video_urls:
            try:
                download_youtube_video_pytube(video_url)
                return 200
            except:
                try:
                    download_youtube_video_yt_dlp(url)
                    return 200
                except:
                    return 500

    else:
        print(f"{url} is neither a youtube video nor a playlist")
        return 415


def download_youtube_video_pytube(url: str, resolution: str="720p"):
    """
    Download video from YouTube using the pytube library.

    Args:
        url (str): URL of the YouTube video.
        resolution (str, optional): The desired resolution of the video. Defaults to "720p".
    
    Raises:
        Exception: For errors during download.

    Example:
        download_youtube_video("https://www.youtube.com/watch?v=example", resolution="1080p")
    """
    try:
        save_path = "media/videos/"
        os.makedirs(save_path, exist_ok=True)

        yt = YouTube(url)
        stream = yt.streams.filter(res=resolution).first()
        if stream is None:
            stream = yt.streams.get_highest_resolution()
        
        stream.download(output_path=save_path)
        print(f"Video download successfully to {save_path}")

    except Exception as e:
        raise e


def download_youtube_video_yt_dlp(url: str):
    """
    Download video from YouTube using the pytube library.

    Args:
        url (str): URL of the YouTube video.
    
    Raises:
        Exception: For errors during download.

    Example:
        download_youtube_video_yt_dlp("https://www.youtube.com/watch?v=example")
    """

    ydl_opts = {
            'format': 'best',
            'outtmpl': "media/videos/%(title)s.%(ext)s",
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except Exception as e:
        raise e



def extract_video_urls_from_playlist(url: str):
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
        raise e
    


def download_youtube_transcript(url: str, language: str="en"):
    """
    
    """
    try:
        raw_transcript = YouTubeTranscriptApi.get_transcript(url, languages=["en"])
        combined_transcript = " ".join(item['text'] for item in raw_transcript)

        model = PunctuationModel()
        punctuation_transcript = model.restore_punctuation(combined_transcript)

        happy_tt = HappyTextToText("T5", "t5-base")
        final_transcript = happy_tt.generate_text(punctuation_transcript)

        print(final_transcript)
    except Exception as e:
        raise e
    

