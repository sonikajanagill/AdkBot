import logging

from google.adk.agents import Agent
from google.adk.tools import Tool

logger = logging.getLogger(__name__)

def list_recent_files(max_results: int = 10) -> str:
    """Lists the user's most recently accessed files in Google Drive."""
    logger.info(f"Listing {max_results} recent files.")
    return "Mock Drive: 1. Q3 Report.pdf, 2. Design Specs.docx"

def search_files(query: str) -> str:
    """Searches Google Drive for files matching the query."""
    logger.info(f"Searching drive for: {query}")
    return f"Mock Search Results: Found 2 files for '{query}'"

def summarise_document(file_id: str) -> str:
    """Reads a file from Google Drive and provides a summary."""
    logger.info(f"Summarising document ID: {file_id}")
    return f"Mock summary of document {file_id}: This is a high level overview of Q3."

list_recent_tools = Tool.from_function(list_recent_files)
search_files_tool = Tool.from_function(search_files)
summarise_document_tool = Tool.from_function(summarise_document)

drive_agent = Agent(
    name="DriveAgent",
    model="gemini-2.0-flash",
    description="Searches Google Drive and summarizes documents.",
    instruction="You are a file and document management assistant. Locate files and summarize them when asked.",
    tools=[list_recent_tools, search_files_tool, summarise_document_tool]
)
