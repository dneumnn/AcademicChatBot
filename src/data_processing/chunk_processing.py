import os
import re
import time
from dotenv import load_dotenv
import google.generativeai as genai
import pandas as pd
import numpy as np

from .audio_processing import split_transcript
from .logger import log

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")


def extract_time_and_sentences(text: str) -> list:
    """
    Extract timestamp for each sentence and convert them into dictionary.

    Args:
        text (str): Input text with inserted time stamps inside the curly brackets.

    Returns:
        list: List of elements containing dictionaries with time, sentence & sentence length.
    """
    log.info("extract_time_and_sentences: Starting to process text and extract timestamps for sentences.")

    if not text:
        log.warning("extract_time_and_sentences: Input text is invalid. Return empty list.")
        return []

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
    
    log.info("extract_time_and_sentences: Processed %s sentences with timestamps.", len(result))
    return result


def merge_sentences_based_on_length(result, max_chunk_length) -> list:
    """
    Combine sentences to chunks to align with max chunk length.

    Args:
        result (list): Input from the function extract_time_and_sentences.
        max_chunk_length (int): Max number of characters of the chunk size.

    Returns:
        List: List of elements each element contains the content of the chunk.
    """
    log.info("merge_sentences_based_on_length: Start to merge sentences for max_chunk_length = %s.", max_chunk_length)
    merged_result = []
    i = 0
    
    while i < len(result):
        log.debug("merge_sentences_based_on_length: Processing chunk starting at sentence index %s.", i)
        
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
    
    log.info("merge_sentences_based_on_length: Completed merging. Created %s total chunks.", len(merged_result))
    return merged_result


def add_chunk_overlap(data, max_overlap) -> list:
    """
    Add overlap to chunks.

    Args:
        data (list): List of dict. including the chunk text.
        max_overlap (int): Number of characters of max. overlap of the chunks. 

    Returns:
        List of dictionaries including chunks.
    """
    log.info("add_chunk_overlap: Starting to add the chunk overlap with max_overlap set to %s.", max_overlap)

    processed_data = []

    for i, entry in enumerate(data):
        log.debug("add_chunk_overlap: Processing chunk %s.", i + 1)
        sentences = re.split(r'(?<=[.!?])\s+', entry['sentence'])

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

    log.info("add_chunk_overlap: Completed adding overlap. Processed %s total chunks.", len(processed_data))
    return processed_data


def create_chunk_llm(text: str, gemini_model: str = "gemini-1.5-flash", max_input_length_llm: int = 15000) -> list:
    """
    Create chunks based on LLM.

    Args:
        text (str): text input.
        max_chunk_length (int): max. character length of the chunks.
        gemini_model (str): version of the gemini model.
    
    Returns:
        List of chunks.

    """
    log.info("create_chunk_llm: Starting with the detailed, LLM-based chunking with max_input_length_llm set to %s.", max_input_length_llm)
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel(gemini_model)

    prompt = (
            f"""
            Divide the following transcript text into logical and consistent chunks. 
            Each chunk should be approximately the same size. Make sure no chunk is way longer than the others.
            Ensure that each chunk retains the relevant context so that meaning is not lost. 
            Pay special attention to the final chunk to ensure it is not longer than 
            the others—divide it into smaller chunks if necessary.

            Preserve the text within each chunk exactly as it is, including any content within curly 
            brackets - do not adjust, alter, or reformat it. Ensure no words are 
            missed or omitted. 
            
            Return the output in one textblock each chunk separted by "%%%", 
            with each element containing one chunk.

            Transcript text:
            """
        )

    if len(text) < max_input_length_llm:
        log.info("create_chunk_llm: Processing single chunk input with length %s.", len(text))

        prompt_transcript = prompt + text
        response = model.generate_content(prompt_transcript)
        response = response.text
        response = response.replace("\n", "")
        response = response.split("%%%%")

    else:
        log.info("create_chunk_llm: Processing input with multiple chunks with length %s.", len(text))
        chunks = []
        last_chunk = []

        text_splitted = split_transcript(text, max_input_length_llm)

        for i, text_snipped in enumerate(text_splitted):
            if i == 0:
                
                prompt_transcript = prompt + text_snipped
                response = model.generate_content(prompt_transcript)
                response = response.text
                response = response.replace("\n", "")
                response = response.split("%%%%")
                last_chunk.append(response.pop())
                chunks.extend(response)

            else:
                if i % 10 == 0:
                    log.warning("create_chunk_llm: Too many API calls. Sleep for 60 seconds.")
                    time.sleep(60)
                text_snipped = last_chunk[-1] + text_snipped
                prompt_transcript = prompt + text_snipped
                response = model.generate_content(prompt_transcript)
                response = response.text
                
                response = response.replace("\n", "")
                response = response.split("%%%%")
                
                if i != len(text_splitted) -1:
                    last_chunk.append(response.pop())
                chunks.extend(response)

    log.info("create_chunk_llm: Completed detailed chunk creation. Created %s chunks.", len(response))
    return response


def check_llm_chuncks(chunk_response, chunk_max_length):
    """
    Check and adjust LLM-generated chunks to ensure they fit the maximum length.

    Args:
        chunk_response (list): Response from the LLM with chunks to verify.
        chunk_max_length (int): Maximum allowed length for each chunk.

    Returns:
        List of adjusted chunks.
    """
    log.info("check_llm_chunks: Starting to check LLM chunks with chunk_max_length set to %s.", chunk_max_length)
    chunk_response = chunk_response[0].replace("\n", "").replace("\\", "")
    chunk_list = chunk_response.split("%%%")
    long_chunks = [(index, element) for index, element in enumerate(chunk_list) if len(element) > chunk_max_length]

    log.info("check_llm_chunks: Found %s chunks exceeding the defined max length.", len(long_chunks))

    genai.configure(api_key=API_KEY_GOOGLE_GEMINI)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = (
        f"""
        Divide the following transcript text into logical and consistent chunks.
        Each chunk should be approximately the same size. Make sure no chunk is way longer than the others. 
        Ensure that each chunk retains the relevant context so that meaning is not lost. 

        Preserve the text within each chunk exactly as it is, including any content within curly 
        brackets - do not adjust, alter, or reformat it. Ensure no words are 
        missed or omitted. 
                    
        Return the output in one textblock each chunk separted by "%%%", 
        with each element containing one chunk.

        Transcript text:
        """
    )

    for i, chunk in long_chunks:
        if i % 10 == 0:
            log.warning("check_llm_chunks: Too many API calls. Sleep for 60 seconds.")
            time.sleep(60)
        prompt_with_chunk = prompt + chunk
        response = model.generate_content(prompt_with_chunk)
        response = response.text.replace("\n", "").replace("\\", "")
        response = response.split("%%%")
        
        chunk_list[i:i + 1] = response

    chunk_list = [element for element in chunk_list if len(element) > 1]

    log.info("check_llm_chunks: Completed the LLM chunks check. Final check count: %s.", len(chunk_list))
    return chunk_list


def format_llm_chunks(chunk_list):
    """
    Format LLM chunks by extracting timestamps and cleaning text.

    Args:
        chunk_list (list): List of text chunks with embedded timestamps.

    Returns:
        List of dictionaries including time, cleaned sentence, and length.
    """
    log.info("format_llm_chunks: Start to format LLM chunks for %s chunks.", len(chunk_list))
    merged_results = []
    for i, chunk in enumerate(chunk_list):
        log.debug("format_llm_chunks: Processing LLM chunk %s.", i + 1)

        match = re.search(r"\{(.*?)\}", chunk)
        if match:
            timestamp = float(match.group(1))
        else:
            timestamp = None

        chunk_cleaned = re.sub(r"\{.*?\}", "", chunk)
        chunk_cleaned_length = len(chunk_cleaned)

        merged_results.append({"time": timestamp, "sentence": chunk_cleaned, "length": chunk_cleaned_length})
        if i % 15 == 0:
            log.info("format_llm_chunks: Successfully formatted 15 LLM chunks.")

    if not len(merged_results) % 15 == 0:
        remaning_chunks_to_log = len(merged_results) % 15
        log.info("format_llm_chunks: Successfully formatted %s LLM chunks.", remaning_chunks_to_log)
    log.info("format_llm_chunks: Successfully formatted %s LLM chunks in total.", len(merged_results))
    return merged_results


def append_meta_data(meta_data: dict, video_id: str, chunked_text):
    """
    
    """
    csv_dict = f"{os.getenv('PROCESSED_VIDEOS_PATH').replace('_video_id_', video_id)}/transcripts_chunks/"
    csv_path = f"{csv_dict}{video_id}.csv"
    topic_overview_path = os.getenv("TOPIC_OVERVIEW_PATH")

    df = pd.DataFrame(chunked_text)
    df = df.rename(columns={"sentence":"chunks"})
    if not os.path.exists(csv_dict):
        os.makedirs(csv_dict)

    df_video_topic_overview = pd.read_csv(topic_overview_path)
    df_video_topic_overview_filtered = df_video_topic_overview[df_video_topic_overview["video_id"] == video_id]
    topic = df_video_topic_overview_filtered["video_topic"].iloc[0] if not df_video_topic_overview_filtered.empty else None

    df["video_id"] = meta_data["id"]
    df["video_topic"] = topic
    df["video_title"] = meta_data["title"]
    df["video_uploaddate"] = meta_data["upload_date"]
    df["video_duration"] = meta_data["duration"]
    df["channel_url"] = meta_data["uploader_url"]

    for i in range(len(df["time"])):
    
        value = str(df.loc[i, "time"])
        
        if not value.replace('.', '', 1).isdigit():
            match = re.search(r'\d+(\.\d+)?', value)
            df.loc[i, "time"] = float(match.group()) if match else np.nan
        
        if pd.isna(df.loc[i, "time"]) and i > 0:
            df.loc[i, "time"] = float(df.loc[i-1, "time"]) + 20.0

    df = df.dropna(subset=['time'])

    df.to_csv(csv_path, index=False)
    log.info("append_meta_data: Appended relevant meta data to %s.", csv_path)
