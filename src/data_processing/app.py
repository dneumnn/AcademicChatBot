import os
from pytube import YouTube

def analyze_function(video_input: str):
    print(f"{video_input} will now get analyzed")
    yt = YouTube(video_input)
    print(yt.streams)


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
        print(e)

