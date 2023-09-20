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


class PostgresConfig:
    def __init__(self):
        self.database = os.getenv("POSTGRES_DATABASE")
        self.user = os.getenv("POSTGRES_USERNAME")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.config = {"database": self.database,
                       "user": self.user,
                       "password": self.password,
                       "host": self.host,
                       "port": self.port}
