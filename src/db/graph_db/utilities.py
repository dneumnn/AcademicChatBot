import csv

# read transcript_csv and format information as needed for graph insertion
def read_csv_chunks(video_id, meta_data):
    chunks = []
    with open(f"media/{video_id}/transcripts_chunks/{video_id}.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['time'] != "":
                chunks.append({
                    "node_id": meta_data["id"],
                    "sentence": row["chunks"],
                    "time": float(row["time"].split()[0]),
                    "length": int(row["length"]),
                    "embedding":row["chunks_embedded"]
                })

    return chunks


# read frames and format information as needed for graph insertion
def read_csv_frames(video_id):
    frames = []
    with open(f"media/{video_id}/frames_description/frame_descriptions.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader: 
            if row['time_in_s'] != "":
                frames.append({
                    "time": float(row["time_in_s"]),
                    "file_name": f"{video_id}_{row['file_name']}",
                    "description": row["description"]

                })
    return frames