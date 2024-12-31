# Check if Node already exists
def check_url_id_exists(tx, url_id):
    query = """
    MATCH (m:MetaData {url_id: $url_id})
    RETURN COUNT(m) > 0 AS exists
    """
    result = tx.run(query, url_id=url_id)
    return result.single()["exists"]


# Meta-data node
def create_meta_data_node(tx, meta_data):
    if not check_url_id_exists(tx, meta_data["id"]):
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
    else:
        print(f"Node with url_id {meta_data['id']} already exists.")
        
# Text-chunk node
def create_transcript_chunk_node(tx, chunk):
    if not check_url_id_exists(tx, chunk["id"]):
        query = """
        CREATE (c:TranscriptChunk {
            text: $sentence, start_time: $time,
            length: $length
        })
        """
        tx.run(query, text=chunk["sentence"], 
            time=chunk["time"],  
            length=chunk["length"])
        print(f"Node with url_id {chunk['id']} created.")
    else:
        print(f"Node with url_id {chunk['id']} already exists.")