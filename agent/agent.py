import os

import google.auth
from google.adk.apps import App

from agent.root_agent import root_agent

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

app = App(
    root_agent=root_agent,
    name="agent",
)
