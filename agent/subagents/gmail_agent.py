import logging

from google.adk.agents import Agent

logger = logging.getLogger(__name__)


def read_inbox(max_results: int = 5) -> str:
    """Reads the user's latest emails from the inbox."""
    logger.info(f"Reading {max_results} emails from inbox.")
    return "Mock Inbox: 1. Project Update, 2. Lunch Plans"


def search_emails(query: str) -> str:
    """Searches the user's emails using Gmail query syntax."""
    logger.info(f"Searching emails for: {query}")
    return f"Mock search results for '{query}': No recent matches."


def read_email(message_id: str) -> str:
    """Reads the full body of a specific email."""
    logger.info(f"Reading full email ID: {message_id}")
    return f"Mock Email content for message {message_id}: Hello this is a test."


gmail_agent = Agent(
    name="GmailAgent",
    model="gemini-2.5-flash",
    description="Manages the user's Gmail inbox. Can search and read emails.",
    instruction="You are a personal assistant handling email. Answer questions about the inbox. Only read emails.",
    tools=[read_inbox, search_emails, read_email],
)
