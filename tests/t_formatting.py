import logging
from logtools_vrb import LevelAwareFormatter

######################################
# SAMPLE USAGE: LevelAwareFormatter
######################################

# Get Root Logger
logger = logging.getLogger()
# Construct StreamHandler object logging to stderr
sh = logging.StreamHandler()

# Create LevelAwareFormatter object with all standard values
laf = LevelAwareFormatter()
# and set specific Formatter for CRITICAL messages.
laf.set_level_formatter(logging.CRITICAL, "Houston, %(message)s in %(funcName)s")
# Apply formatter to handler and add handler to logger
laf.apply_to(sh, logger=logger)
logger.error("we have a problem")
# This message will be logged with the specific format for WARNING level messages
logger.critical("we have a problem")

# Create LevelAwareFormatter object with { style formatting, a default formatting string
# and an additional variable "ip" for use when formatting:
laf = LevelAwareFormatter("{levelname}: {asctime} {message} {ip}", "%Y-%m-%d %H:%M:%S", 
                          "{", defaults={"ip":"192.168.0.1"})
# and set specific Formatter for CRITICAL messages.
laf.set_level_formatter(logging.WARNING, "Attention! {asctime} {message} {ip}", "%d:%m:%Y %H:%M", '{')
# replace former formatter with this new one (no need to add handler to logger a second time)
laf.apply_to(sh)
# This message will be logged with the specific format for WARNING level messages
logger.warning("we have a problem")
# This message will be logged with the default format
logger.critical("we have a problem")
