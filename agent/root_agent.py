import logging

from google.adk.agents import Agent

from agent.subagents.calendar_agent import calendar_agent
from agent.subagents.drive_agent import drive_agent
from agent.subagents.gmail_agent import gmail_agent
from agent.subagents.search_agent import search_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are ClawdBot, a highly capable and secure personal assistant.
Your goal is to help the user by reading their emails, managing calendars, organizing files, and searching the web.
Always explain what you're about to do before doing it.
For any destructive action (delete, send, modify), ask for explicit confirmation first.
"""

root_agent = Agent(
    name="clawdbot",
    model="gemini-2.0-flash",
    description="Secure personal assistant capable of orchestrating specialized tasks.",
    instruction=SYSTEM_PROMPT,
    sub_agents=[search_agent, gmail_agent, calendar_agent, drive_agent]
)
