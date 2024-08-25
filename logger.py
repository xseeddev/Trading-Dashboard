import logging
import json
import os
from datetime import datetime

def get_log_file_path():
  """
  Creates a folder named "logs" with the current date appended and returns the path to a new JSON log file within that folder.
  """
  today = datetime.today().strftime('%Y-%m-%d')
  log_dir = os.path.join('logs', today)
  os.makedirs(log_dir, exist_ok=True)  # Create directory if it doesn't exist
  log_file_path = os.path.join(log_dir, f'{today}.json')
  return log_file_path

class JsonFormatter(logging.Formatter):
  """
  Custom formatter to format log messages as JSON objects.
  """
  def format(self, record):
    log_dict = {
      'timestamp': record.created,
      'name': record.name,
      'levelname': record.levelname,
      'message': record.msg
    }
    return json.dumps(log_dict)

def setup_logger(name, level=logging.DEBUG):
  """
  Sets up a logger with a custom JSON formatter and a rotating file handler.
  """
  logger = logging.getLogger(name)
  logger.setLevel(level)

  log_file_path = get_log_file_path()
  file_handler = logging.FileHandler(log_file_path)
  file_handler.setFormatter(JsonFormatter())
  logger.addHandler(file_handler)

  return logger

# Example usage
# logger = setup_logger('my_app')
# logger.debug('This is a debug message')
# logger.info('This is an info message')
# logger.warning('This is a warning message')
# logger.error('This is an error message')
# logger.critical('This is a critical message')