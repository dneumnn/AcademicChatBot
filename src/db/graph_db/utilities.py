import csv
from src.data_processing.logger import log

# read transcript_csv and format information as needed for graph insertion
def read_csv_chunks(video_id, meta_data):
    chunks = []
    with open(f"media/{video_id}/transcripts_chunks/{video_id}.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Validate 'time' and 'length' before processing
            time_value = row.get('time')  # Safely get 'time'
            length_value = row.get('length')  # Safely get 'length'
            
            if (
                time_value and time_value.replace('.', '', 1).isdigit()  # Check if time is a valid float
                and length_value and length_value.isdigit()  # Check if length is a valid integer
            ):
                try:
                    chunks.append({
                        "node_id": meta_data["id"],
                        "sentence": row.get("chunks", ""),  # Default to empty string if 'chunks' is missing
                        "time": float(time_value.split()[0]),  # Convert time to float
                        "length": int(length_value),  # Convert length to int
                        "embedding": row.get("chunks_embedded", "")  # Default to empty string if missing
                    })
                except Exception as e:
                    log.error(f"Error processing row: {row}, error: {e}")
            else:
                log.info(f"Skipping chunk due to invalid data format: {row}")
    return chunks


# read frames and format information as needed for graph insertion
def read_csv_frames(video_id):
    frames = []
    with open(f"media/{video_id}/frames_description/frame_descriptions.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Validate the 'time_in_s' field
            time_value = row.get('time_in_s')  # Safely get 'time_in_s'
            
            if time_value and time_value.replace('.', '', 1).isdigit():  # Check if time_in_s is a valid float
                try:
                    frames.append({
                        "time": float(time_value),  # Convert time_in_s to float
                        "file_name": f"{video_id}_{row.get('file_name', '')}",  # Use file_name as-is (default to empty string)
                        "description": row.get("description", "")  # Default to empty string if missing
                    })
                except Exception as e:
                    log.error(f"Error processing row: {row}, error: {e}")
            else:
                log.info(f"Skipping frame due to invalid 'time_in_s': {row}")
    return frames