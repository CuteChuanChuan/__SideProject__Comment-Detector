import os
import logging
from dotenv import load_dotenv

load_dotenv(verbose=True)


class LoggingConfig:
    def __init__(self, name):
        self.name = name
        self.level = logging.INFO
        self.date_format = "%Y-%m-%d %H:%M:%S"
        self.format = "%(asctime)s %(levelname)s %(message)s"
        self.handlers = [logging.FileHandler(f"log/{self.name}.log", "w", "utf-8")]

    def configure(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        formatter = logging.Formatter(self.format, datefmt=self.date_format)

        for handler in self.handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger


class PostgresConfig:
    def __init__(self):
        self.database = os.getenv("POSTGRES_DATABASE")
        self.user = os.getenv("POSTGRES_USERNAME")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")
        self.config = {
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port,
        }
