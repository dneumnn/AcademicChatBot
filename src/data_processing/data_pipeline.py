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
import google.generativeai as genai
from dotenv import load_dotenv
import cv2
import PIL.Image
import json

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")


# Static variables
VIDEO_DIRECTORY = "./media/videos/"
FRAMES_DIRECTORY = "./media/frames"
EXTRACTED_URLS_PATH = "./src/data_processing/extracted_urls.txt"

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
            meta_data = extract_meta_data(video_url)
            print(meta_data)

            videoid = extract_youtube_video_id(video_url)
            video_filepath = VIDEO_DIRECTORY + videoid + ".mp4"
            extract_frames_from_video(video_filepath, 5)

            write_url_to_already_downloaded(video_url)
        except Exception as e:
            print(f"/analyze error: {e}")
            return 500
    return 200


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
    videoid = extract_youtube_video_id(url)

    ydl_opts = {
            'format': 'best',
            'outtmpl': f"media/videos/{videoid}.%(ext)s",
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
    videoid = extract_youtube_video_id(url)

    meta_data = {}

    ydl_opts = {
            'format': 'best',
            'outtmpl': f"media/videos/{videoid}.%(ext)s",
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


def extract_frames_from_video(video_filepath: str, interval_in_sec: int = 5):
    """
    Extract a certain number of frames of a YouTube video.

    Args:
        video_filepath (str): The filepath of the video.
        interval_in_sec (int): Interval in seconds between each frame to be extracted. This specifies how frequently frames are captured from the video.

    Example: 
        extract_youtube_video_id("./media/videos/my_example_video.mp4", 5)
    """

    print("Begin extraction...")

    filename = video_filepath.replace(VIDEO_DIRECTORY, "")
    filename = filename.replace(".mp4", "")
    if not os.path.exists(f"./media/frames/{filename}"):
        os.makedirs(f"./media/frames/{filename}")

    cam = cv2.VideoCapture(video_filepath)
    video_fps = cam.get(cv2.CAP_PROP_FPS)
    interval = round(video_fps * interval_in_sec)
    print(f"Calculated interval: {interval}")

    success, image = cam.read()
    count = 0
    while success:
        if count % interval == 0:
            print(f"Writing frame {count}")
            cv2.imwrite(f"./media/frames/{filename}/frame{count}.jpg", image)
        success, image = cam.read()
        count += 1


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
    if not os.path.exists(EXTRACTED_URLS_PATH):
        return False

    with open(EXTRACTED_URLS_PATH, 'r') as file:
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
    with open(EXTRACTED_URLS_PATH, 'a') as file:
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
    

def download_preprocess_youtube_transcript(url: str, language:str="en", gemini_model: str="gemini-1.5-flash"):
    """
    Download and add start time information into the transcript. Time information is inserted in curly brackets inbetween the text. 

    Args:
        url (str): URL of a YouTube video.
        language (str): language of the transcript.
        gemini_model: Gemini model that is in use for processing the transcript.

    Returns:
        Creation of a transcript file in the folder media/transcripts with the video id as name.
    """
    video_id = extract_youtube_video_id(url)
    raw_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
    
    combinded_transcript = []
    for item in raw_transcript:
        start_time = f"{{{item['start']}}}"  
        text = item['text']
        combinded_transcript.append(f"{start_time} {text}")
    raw_combined_transcript = " ".join(combinded_transcript)
        
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)
    prompt = (
        "Please improve the following transcript by correcting any grammar mistakes, "
        "fixing capitalization errors, fixing punctuation missings and mistakes, "
        "and correcting any misspelled or misheard words. Do not modify the formatting "
        "in any way—keep it as one continuous block of text with no additional headings, "
        "paragraphs, or bullet points. Only focus on improving the text itself. Ignore all "
        "curly brackets and the inserted number inside; keep them at the same position "
        "of the text without adjusting it: "
    )
    prompt_transcript = prompt + raw_combined_transcript
    response = model.generate_content(prompt_transcript)

    with open(f"media/transcripts/{video_id}.txt", "w", encoding="utf-8") as datei:
        datei.write(response.text)

    
def create_image_description(image_file_path: str, gemini_model: str="gemini-1.5-flash"):
    """
    """
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)
    image_file = PIL.Image.open(image_file_path)

    prompt = (
        "Please provide a detailed description of the image from the YouTube video, "
        "focusing on the relevant content, e.g. AI, Machine Learning, "
        "or other topics shown in the picture. Describe the setting, including the environment, any diagrams, "
        "charts, equations, or visual aids displayed. If there are visual representations of algorithms, "
        "models, or data, explain them in detail, including any colors, patterns, or structures. "
        "If relevant people, such as experts in computer vision or similar fields, are shown in the "
        "context of the task, briefly mention them and their relevance. Avoid mentioning irrelevant people "
        "unless they are directly related to the content of the video."
    )

    response = model.generate_content(
        [prompt, image_file]
    )
    print(response.text)


def extract_time_and_sentences(text: str):
    """
    Extract timestamp for each sentence and convert them into dictionary.

    Args:
        text (str): Input text with inserted time stamps inside the curly brackets.

    Returns:
        list: List of elements containing dictionaries with time, sentence & sentence length.
    """
    split_text = re.split(r'(?<=[.?!])\s+', text)
    
    time_pattern = r'\{([^}]+)\}'  
    
    result = []
    
    for sentence in split_text:
        
        sentence = sentence.strip()
        
        if not sentence:
            continue
        
        time_match = re.search(time_pattern, sentence)
        
        if time_match:
            time = time_match.group(1)
        else:
            time = None
        
        sentence = re.sub(r'\{[^}]+\}', '', sentence)

        sentence_length = len(sentence)
        
        result.append({'time': time, 'sentence': sentence, 'length': sentence_length})
    
    return result


def merge_sentences_based_on_length(result, max_chunk_length):
    """
    Combine sentences to chunks to align with max chunk length.

    Args:
        result (list): Input from the function extract_time_and_sentences.
        max_chunk_length (int): Max number of characters of the chunk size.

    Returns:
        List: List of elements each element contains the content of the chunk.
    """
    merged_result = []
    i = 0
    
    while i < len(result):
        
        current_sentence = result[i]
        combined_sentence = current_sentence['sentence']
        total_length = current_sentence['length']
        time = current_sentence['time']
        
        while i + 1 < len(result) and total_length + result[i + 1]['length'] <= max_chunk_length:
          
            next_sentence = result[i + 1]
            combined_sentence += ' ' + next_sentence['sentence']
            total_length += next_sentence['length']
            
            if time is None:
                time = next_sentence['time']
            
            i += 1
        
        merged_result.append({'time': time, 'sentence': combined_sentence, 'length': total_length})
        
        i += 1
    
    return merged_result

def process_data(data, max_overlap):
    """
    Add overlap to chunks.

    Args:
        data (list): List of dict. including the chunk text.
        max_overlap (int): Number of characters of max. overlap of the chunks. 

    Returns:
        List of dictionaries including chunks.
    """
    processed_data = []

    for i, entry in enumerate(data):
        sentences = re.split(r'(?<=[.!?])\s+', entry['sentence'])
        words = entry['sentence'].split()

        if i > 0:  
            previous_entry = processed_data[-1]
            previous_sentence = previous_entry['sentence']

            if len(previous_sentence) <= max_overlap:
                overlap_content = previous_sentence
            else:
                
                overlap_content = previous_sentence[-max_overlap:]
                first_space = overlap_content.find(" ")
                if first_space != -1:
                    overlap_content = overlap_content[first_space + 1:]

            sentences[0] = overlap_content + ' ' + sentences[0]

        updated_sentence = ' '.join(sentences)
        processed_data.append({
            'time': entry['time'],
            'sentence': updated_sentence,
            'length': len(updated_sentence)
        })

    return processed_data

def create_chunk_llm(text: str, max_chunk_length: int=500, gemini_model: str="gemini-1.5-flash"):
    """
    
    """
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)
    prompt = (
        f"""
        Divide the transcript text into logical chunks, ensuring each chunk 
        is no longer than {max_chunk_length} characters.

        Preserve the text exactly as it is, including any content within curly 
        brackets - do not adjust, alter, or reformat it. Ensure no words are 
        missed or omitted. Return the output in brackets "[]", with each element 
        containing a single chunk. 

        Transcript text:
        """
    )
    prompt_transcript = prompt + text
    response = model.generate_content(prompt_transcript)
    response = response.text
    response = re.sub(r"```json|```", "", response).strip()

    return response

