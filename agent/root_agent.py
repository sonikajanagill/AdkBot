import logging

from google.adk.agents import Agent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from agent.subagents.calendar_agent import calendar_agent
from agent.subagents.drive_agent import drive_agent
from agent.subagents.gmail_agent import gmail_agent
from agent.subagents.search_agent import search_agent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are AdkBot, a highly capable and secure personal assistant.
Your goal is to help the user by reading their emails, managing calendars, organizing files, and searching the web.
Always explain what you're about to do before doing it.
For any destructive action (delete, send, modify), ask for explicit confirmation first.

You have persistent memory across conversations. Use it to remember user preferences,
past interactions, and context to provide a more personalized experience.
"""


async def save_session_to_memory(callback_context):
    """After each agent turn, save the session to Memory Bank for long-term recall."""
    try:
        memory_service = callback_context._invocation_context.memory_service
        if memory_service:
            await memory_service.add_session_to_memory(
                callback_context._invocation_context.session
            )
            logger.info(f"Session saved to Memory Bank for user {callback_context._invocation_context.session.user_id}")
    except Exception as e:
        logger.warning(f"Failed to save session to memory: {e}")


root_agent = Agent(
    name="adkbot",
    model="gemini-2.5-flash",
    description="Secure personal assistant capable of orchestrating specialized tasks.",
    instruction=SYSTEM_PROMPT,
    tools=[PreloadMemoryTool()],
    sub_agents=[search_agent, gmail_agent, calendar_agent, drive_agent],
    after_agent_callback=save_session_to_memory,
)
