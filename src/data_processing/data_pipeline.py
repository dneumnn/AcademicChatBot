import os
from pytube import (
    YouTube,
    Playlist
)
from youtube_transcript_api import YouTubeTranscriptApi
from deepmultilingualpunctuation import PunctuationModel
from happytransformer import HappyTextToText
import yt_dlp
import re
import cv2

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

    if url_already_downloaded(url):
        print("ALREADY DOWNLOADED!")
        return 200

    video_urls = []

    # load url(s) in the video_urls list
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
        try:
            download_youtube_video_pytube(video_url)
        except:
            try:
                download_youtube_video_yt_dlp(url)
            except:
                return 500
        try:
            meta_data = extract_meta_data(url)
            print(meta_data)
            replace_spaces_in_filenames("./media/videos/") # Fix: needs to be implemented to work with multiple videos
            new_file_path = get_new_filepath(meta_data['title'])
            extract_frames_from_video(new_file_path, 2)
            write_url_to_already_downloaded(url)
            return 200
        except Exception as e:
            print(f"/analyze error: {e}")
            return 500


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
            'retries': 3,
            'geo_bypass': True,
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
        return video_urls
    
    except Exception as e:
        raise e


def extract_meta_data(url: str):
    """
    Extract the relevant meta data for a YouTube video.

    Args:
        url (str): URL of the YouTube video.
    
    Raises:
        Exception: For errors during meta data extraction.
    """
    meta_data = {}

    ydl_opts = {
            'format': 'best',
            'outtmpl': "media/videos/%(title)s.%(ext)s",
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

            return meta_data

    except Exception as e:
        raise e


def get_new_filepath(filename: str):
    
    clean_filename = clean_up_filename(filename)

    for current_file in os.listdir("./media/videos"):
        if clean_filename in current_file:
            return os.path.join("./media/videos/", current_file)


def replace_spaces_in_filenames(directory: str):
    """
    
    """

    for filename in os.listdir(directory):
        clean_string = clean_up_filename(filename)

        original_file_path = os.path.join(directory, filename)
        new_file_path = os.path.join(directory, clean_string)
        if not os.path.exists(new_file_path):
            os.rename(original_file_path, new_file_path)


def clean_up_filename(filename: str):
    if " " in filename:
        filename = filename.replace(" ", "_")

    encoded_string = filename.encode("ascii", "ignore")
    clean_string = encoded_string.decode("ascii")

    return clean_string
        

def extract_frames_from_video(filename: str, extracted_fps: int):

    if not os.path.exists("./media/frames"):
        os.makedirs("./media/frames")

    cam = cv2.VideoCapture(filename)
    video_fps = cam.get(cv2.CAP_PROP_FPS)
    interval = video_fps / extracted_fps

    success, image = cam.read()
    count = 0
    while success:
        print(count)
        print(interval)
        if count % interval == 0:
            print("TRUE")
            cv2.imwrite(f"./media/frames/frame{count}.jpg", image)
        success, image = cam.read()
        count += 1


def url_already_downloaded(url: str):
    # Check if the file exists
    if not os.path.exists("./src/data_processing/extracted_urls.txt"):
        return False

    with open("./src/data_processing/extracted_urls.txt", 'r') as file:
        for line in file:
            if line.strip() == url:
                return True
    return False


def write_url_to_already_downloaded(url: str):
    with open("./src/data_processing/extracted_urls.txt", 'a') as file:
        file.write(url + '\n')


def extract_youtube_video_id(url: str):
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
        raise ValueError("YouTube Video ID could not be extracted from the URL")


def download_youtube_transcript(url: str, language: str="en"):
    # TODO insert doc string
    """
    Get transcript of YouTube video.

    Args:
        url (str): URL of a YouTube video.
        language (str): Language of the transcript.
    
    Returns:
    Example:
    """
    try:
        video_id = extract_youtube_video_id(url)
        raw_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        combined_transcript = " ".join(item['text'] for item in raw_transcript)

        model = PunctuationModel()
        punctuation_transcript = model.restore_punctuation(combined_transcript)

        # TODO optimize model
        happy_tt = HappyTextToText("T5", "t5-large")

        prompt = (
            "Please correct the following text for spelling, capitalization, syntax, and transcription errors. Ensure proper sentence structure, adjust for incorrect word usage, and maintain the original meaning: "
        )

        prompt_punctuation_transcript = prompt + punctuation_transcript
        final_transcript = happy_tt.generate_text(prompt_punctuation_transcript)

        return final_transcript
    except Exception as e:
        raise e
    
