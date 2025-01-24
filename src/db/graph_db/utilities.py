import csv
from src.data_processing.logger import log

# read transcript_csv and format information as needed for graph insertion
def read_csv_chunks(video_id, meta_data):
    chunks = []
    with open(f"media/{video_id}/transcripts_chunks/{video_id}.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            time_value = row.get('time') 
            length_value = row.get('length')          
            if (
                time_value and time_value.replace('.', '', 1).isdigit() 
                and length_value and length_value.isdigit()
            ):
                try:
                    chunks.append({
                        "node_id": meta_data["id"],
                        "sentence": row.get("chunks"),
                        "time": float(time_value.split()[0]),
                        "length": int(length_value),
                        "embedding": row.get("chunks_embedded")
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
            time_value = row.get('time_in_s')
            
            if time_value and time_value.replace('.', '', 1).isdigit():  
                try:
                    frames.append({
                        "time": float(time_value),
                        "file_name": f"{video_id}_{row.get('file_name')}",
                        "description": row.get("description")
                    })
                except Exception as e:
                    log.error(f"Error processing row: {row}, error: {e}")
            else:
                log.info(f"Skipping frame due to invalid 'time_in_s': {row}")
    return frames