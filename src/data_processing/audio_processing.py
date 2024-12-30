import os
from dotenv import load_dotenv

import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

from .video_metadata_download import extract_youtube_video_id
from .logger import log

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")


def download_preprocess_youtube_transcript(url: str, language:str="en", gemini_model: str="gemini-1.5-flash") -> None:
    """
    Download and add start time information into the transcript. 
    Time information is inserted in curly brackets inbetween the text. 

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
    
    try:
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

    except Exception as e:
        log.warning("Error during transcript correction: %s", e)

    transcript_path = f"media/{video_id}/transcripts/"
    if not os.path.exists(transcript_path):
            os.makedirs(transcript_path)

    with open(f"media/{video_id}/transcripts/{video_id}.txt", "w", encoding="utf-8") as datei:
        datei.write(response.text)

