import os
import sys
import logging
from logging import Formatter, DEBUG, INFO, WARNING, ERROR, StreamHandler

logger_name = 'dnsui'
formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_levels = {'DEBUG': DEBUG, 'INFO': INFO, 'WARNING': WARNING, 'ERROR': ERROR}
env_log_level = os.getenv('LOG_LEVEL')
if env_log_level in log_levels.keys():
    log_level = log_levels[env_log_level]
else:
    log_level = INFO

logg_handlers = []

try:
    handler: StreamHandler = StreamHandler()
    logg_handlers.append(handler)
except Exception as e:
    print('Unexpected error: (StreamHandler)', sys.exc_info()[0])

logger = logging.getLogger(logger_name)
logger.setLevel(log_level)

for handler in logg_handlers:
    # Get formatter
    formatter = formatter
    # Set formatter
    handler.setFormatter(formatter)
    # Add the handlers to the logger
    logger.addHandler(handler)

logger.debug(f'Loaded these handlers: {logg_handlers}')
