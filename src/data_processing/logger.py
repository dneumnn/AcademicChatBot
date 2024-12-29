import logging
import uuid

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
    filename="src/data_processing/data-processing.log", # Name of the log file
    level=logging.WARNING, # Logging level
    format=f'%(asctime)s [Session-{session_id}] %(levelname)s - %(message)s' # Format of the log messages
)

log = logging.getLogger("data_processing")
