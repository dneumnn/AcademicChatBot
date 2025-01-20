from datetime import datetime
import logging
import os
import uuid
import pytz

# Generate unique session ID at the start of the application
session_id = str(uuid.uuid4())[:8] # Shortened UUID

# * Available log levels:
    # Debug (10)
    # Info (20)
    # Warning (30)
    # Error (40)
    # Critical (50)

# * Configure logging
logging.basicConfig (
    filename=os.getenv("LOG_FILE_PATH"), # Name of the log file
    level=logging.INFO, # Logging level
    format=f'%(asctime)s [Session-{session_id}] %(levelname)s - %(message)s' # Format of the log messages
)

log = logging.getLogger("data_processing")


def create_log_file(filename: str):
    try:
        if not os.path.exists(filename) or os.stat(filename).st_size == 0:

            # Get current timestamp and the used timezone
            tz = pytz.timezone('CET') # Central European Time
            timestamp = datetime.now(tz)
            formated_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
            timezone = timestamp.strftime('%Z')

            # Write into the log file.
            with open(filename, 'w') as file:
                file.write("# Application Log - Service: Data Pre-Processing\n")
                file.write(f"# Generated on: {formated_timestamp} {timezone}\n")
                file.write("================================================================================================================================================================\n")
    except:
        print("log file creation failed")

def write_empty_line(filename: str):
    with open(filename, 'a') as file:
        file.write("\n")

