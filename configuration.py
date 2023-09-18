import os
from dotenv import load_dotenv
import logging

load_dotenv(verbose=True)


class LoggingConfig:
    def __init__(self):
        self.level = logging.INFO
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.format = "%(asctime)s %(levelname)s %(message)s"
        self.handlers = [logging.FileHandler("log/stylish.log", "w", "utf-8")]
        self.logging_config = {"level": self.level,
                               "date_format": self.date_format,
                               "format": self.format,
                               "handlers": self.handlers}
