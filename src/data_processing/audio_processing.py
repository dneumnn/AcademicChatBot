import os
from dotenv import load_dotenv
import time

import google.generativeai as genai
from ollama import chat
from ollama import ChatResponse
from youtube_transcript_api import YouTubeTranscriptApi

from .video_metadata_download import extract_youtube_video_id
from .logger import log

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")

def split_transcript(transcript: str, max_length: int) -> list:
    """
    Split the transcript into smaller chunks without cutting words.
    
    Args:
        transcript (str): The raw combined transcript.
        max_length (int): Maximum allowed character length per chunk.
    
    Returns:
        list: List of transcript chunks.
    """
    chunks = []
    current_chunk = []

    for word in transcript.split():
        # Check if adding the next word would exceed the max_length
        if sum(len(chunk) for chunk in current_chunk) + len(word) + 1 > max_length:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
        current_chunk.append(word)
    
    # Add the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def download_preprocess_youtube_transcript(url: str, language:str="en", gemini_model: str="gemini-1.5-flash", local_model:bool=False) -> None:
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
        if local_model == False:
            max_length = 20000  
            transcript_chunks = split_transcript(raw_combined_transcript, max_length)

            time.sleep(60)
            genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
            model = genai.GenerativeModel(gemini_model)
            prompt = (
                """Please improve the following transcript by correcting any grammar mistakes, 
                fixing capitalization errors, fixing punctuation missings and mistakes, 
                and correcting any misspelled or misheard words. Do not modify the formatting 
                in any way—keep it as one continuous block of text with no additional headings, 
                paragraphs, or bullet points. Only focus on improving the text itself. Ignore all 
                curly brackets and the inserted number inside; keep them at the same position 
                of the text without adjusting it: """
            )

            improved_chunks = []
            for chunk in transcript_chunks:
                response = model.generate_content(prompt + chunk)
                improved_chunks.append(response.text)
        
            improved_transcript = " ".join(improved_chunks)

        else:
            max_length = 2500  
            transcript_chunks = split_transcript(raw_combined_transcript, max_length)
            prompt =  """Please improve the following transcript by correcting any grammar mistakes, 
                fixing capitalization errors, fixing punctuation missings and mistakes, 
                and correcting any misspelled or misheard words. Do not modify the formatting 
                in any way—keep it as one continuous block of text with no additional headings, 
                paragraphs, or bullet points. Only focus on improving the text itself. Ignore all 
                curly brackets and the inserted number inside keep them at the same position 
                of the text without adjusting it. Do not return anything else, 
                do not say "Here is the improved transcript". This is the transcript: """

            improved_chunks = []
            for chunk in transcript_chunks:
                response: ChatResponse = chat(model='llama3.2', messages=[
                {
                    'role': 'user',
                    'content': prompt + chunk,
                },
                ])
                improved_chunks.append(response.message.content)
        
            improved_transcript = " ".join(improved_chunks)

    except Exception as e:
        log.warning("Error during transcript correction: %s", e)

    transcript_path = f"media/{video_id}/transcripts/"
    if not os.path.exists(transcript_path):
            os.makedirs(transcript_path)

    with open(f"media/{video_id}/transcripts/{video_id}.txt", "w", encoding="utf-8") as datei:
        datei.write(improved_transcript)
        log.info("Transcript was successfully extracted and improved.")

