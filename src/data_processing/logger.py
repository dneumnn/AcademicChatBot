import logging

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
    format='%(asctime)s %(levelname)s - %(message)s' # Format of the log messages
)

log = logging.getLogger("data_processing")
