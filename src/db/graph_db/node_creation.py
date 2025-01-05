# Check if Node already exists
def check_url_id_exists(tx, label, property_name, property_value):
    query = f"""
    MATCH (n:{label} {{{property_name}: $property_value}})
    RETURN COUNT(n) > 0 AS exists
    """
    result = tx.run(query, property_value=property_value)
    return result.single()["exists"]


# Meta-data node
def create_meta_data_node(tx, meta_data):
    if not check_url_id_exists(tx, "MetaData", "url_id", meta_data["id"]):
        query = """
        CREATE (m:MetaData {
            url_id: $url_id, 
            title: $title, 
            description: $description,
            tags: $tags,
            categories: $categories, 
            upload_date: $upload_date, 
            duration: $duration, 
            uploader_url: $uploader_url,  
            uploader: $uploader, 
            thumbnail: $thumbnail,
            view_count: $view_count,
            like_count: $like_count,
            age_limit: $age_limit
        })
        """
        tx.run(query, url_id=meta_data["id"], 
            title=meta_data["title"], 
            description=meta_data["description"],
            tags=meta_data["tags"],  
            categories=meta_data["categories"], 
            upload_date=meta_data["upload_date"],
            duration=meta_data["duration"], 
            uploader_url=meta_data["uploader_url"], 
            uploader=meta_data["uploader"], 
            thumbnail=meta_data["thumbnail"], 
            view_count=meta_data["view_count"], 
            like_count=meta_data["like_count"], 
            age_limit=meta_data["age_limit"])  
        print(f"Node with url_id {meta_data['id']} created.")
        return
    else:
        print(f"Node with url_id {meta_data['id']} already exists.")
        return
        
# Text-chunk node
def create_transcript_chunk_node(tx, chunk):
    if not check_url_id_exists(tx, "TranscriptChunk", "node_id", chunk["node_id"]):
        query = """
        CREATE (c:TranscriptChunk {
            node_id: $node_id, text: $sentence, start_time: $time,
            length: $length, embedding: $embedding
        })
        """
        tx.run(query, node_id=chunk["node_id"],
            sentence=chunk["sentence"], 
            time=chunk["time"],  
            length=chunk["length"],
            embedding=chunk["embedding"])
        print(f"Node with url_id {chunk['node_id']} created.")
        return
    else:
        print(f"Node with url_id {chunk['node_id']} already exists.")
        return
    
# Frame node 
def create_frame_description_node(tx, frame):
    if not check_url_id_exists(tx, "FrameDescription", "frame_id", frame["frame_id"]):
        query = """
        CREATE (f:FrameDescription {
            frame_id: $frame_id, text: $frameText, start_time: $time
        })
        """
        tx.run(query, frame_id=frame["frame_id"],
            frameText=frame["text"], 
            time=frame["time"]) 
        print(f"Node with url_id {frame['frame_id']} created.")
        return
    else:
        print(f"Node with url_id {frame['frame_id']} already exists.")
        return
