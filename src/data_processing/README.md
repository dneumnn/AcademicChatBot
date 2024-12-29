# Data Pre-Processing

This package contains a data pipeline that pre-processes the data from a certain YouTube video or YouTube playlist. The pipeline is started through the `/analyze` API from the FastAPI code. An URL of a video or playlist is passed and if it is a valid YouTube URL, the pipeline extracts descriptions for relevant frames in the video as well as an improved version of the provided transcript/ subtitles for that video. The results are then stored in multiple folders in the `/media` folder. This allows the database packages for the graph DB and vector DB to use those saved data to write them into the databases.

## Data Pipeline

- Step 1: Check if URL is a valid YouTube video or a valid YouTube playlist.
- Step 2: Append video URLs to a list of demanded URLs.
- Step 3: Download video through pytube, or if that didnt work, using yt_dlp.
- Step 4: Extract fitting meta data from video.
- Step 5: Extract frames from the video.
- Step 6: Use a LLM to describe each frame.
- Step 7: Extract the transcript for the video.
- Step 8: Append fitting timestamp for each sentence and improve the quality of each sentence through a LLM.
- Step 9: Merge sentences and chunk the data.
- Step 10: Write video URL to the list of already downloaded and processed URLs.
Repeat step 3 to 10 for each video.

## Generated Files

`/media/frames` - Frames
`/media/frames_description` - Frames Description
`/media/transcripts` - Transcripts

---

![Data Pipeline Image](/media/images/pre-processing-pipeline.png)
