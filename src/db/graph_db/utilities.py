import csv

def read_csv_chunks(file_path):
    chunks = []
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            node_id = f"TextChunk{index:02d}"
            chunks.append({
                "node_id": node_id,
                "sentence": row["sentence"],
                "time": row["start_time"],
                "length": int(row["length"])
            })
    return chunks

def read_csv_frames(file_path):
    frames = []
    with open(file_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            frame_id = f"Frame{index:02d}"
            frames.append({
                "frame_id": frame_id,
                "time": row["time"],
                "description": row["description"],
                "file_path": row["file_path"]
            })
    return frames