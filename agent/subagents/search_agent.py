from google.adk.agents import Agent
from google.adk.tools import google_search

search_agent = Agent(
    name="SearchAgent",
    model="gemini-2.5-flash",
    description="Finds recent information and facts on the internet.",
    instruction="You are a research assistant. Use Google Search to find answers to the user's questions. Provide clear, concise summaries of what you find.",
    tools=[google_search],
)
