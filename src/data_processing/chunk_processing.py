import os
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Env variables
load_dotenv() 
API_KEY_GOOGLE_GEMINI = os.getenv("API_KEY_GOOGLE_GEMINI")


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


def add_chunk_overlap(data, max_overlap):
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

