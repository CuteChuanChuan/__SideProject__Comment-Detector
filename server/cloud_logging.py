import os
import json
import loguru
import google.cloud.logging
from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2.service_account import Credentials

load_dotenv(verbose=True)
key_content = json.loads(os.getenv("LOGGER_KEY"))
credentials = Credentials.from_service_account_info(
    key_content
)

# client = google.cloud.logging.Client(credentials=credentials)
# client.setup_logging()

print(os.getcwd())

