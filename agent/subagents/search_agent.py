import logging

from google.adk.agents import Agent
from google.adk.tools import Tool

logger = logging.getLogger(__name__)

def web_search_tool(query: str) -> str:
    """
    Search the web for current information, news, or facts.
    
    Args:
        query: The search terms to look up.
    Returns:
        Summary of search results.
    """
    logger.info(f"Mock web search for: {query}")
    # Mock implementation for now
    return f"Search results for '{query}': Example finding (mock)"

search_tool = Tool.from_function(web_search_tool)

search_agent = Agent(
    name="SearchAgent",
    model="gemini-2.0-flash", # Note: ADK model binding needs valid key
    description="Finds recent information and facts on the internet.",
    instruction="You are a research assistant. Use the web search tool to find answers to the user's questions.",
    tools=[search_tool]
)
