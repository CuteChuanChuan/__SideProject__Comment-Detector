import functions_framework
import requests

URL = "https://comment-detector.org/overview/"

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def hello_pubsub(cloud_event):
    # Print out the data from Pub/Sub, to prove that it worked
    response = requests.get(url=URL)
    print(response.status_code)
