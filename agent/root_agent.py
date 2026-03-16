import logging

from google.adk.agents import Agent

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

{memory}
"""


async def load_memory_on_start(callback_context):
    """Before agent runs, retrieve relevant memories and inject into state."""
    try:
        memory_service = callback_context._invocation_context.memory_service
        session = callback_context._invocation_context.session
        if memory_service and session:
            memories = await memory_service.search_memory(
                app_name=callback_context._invocation_context.app_name,
                user_id=session.user_id,
                query=session.events[-1].content.parts[0].text if session.events else "",
            )
            if memories:
                memory_text = "\n".join(
                    [f"- {m.fact}" for m in memories if hasattr(m, "fact")]
                )
                if memory_text:
                    callback_context.state["memory"] = (
                        f"\nRelevant memories from past conversations:\n{memory_text}"
                    )
                    logger.info(f"Loaded {len(memories)} memories for user {session.user_id}")
                    return
        callback_context.state["memory"] = ""
    except Exception as e:
        logger.warning(f"Failed to load memory: {e}")
        callback_context.state["memory"] = ""


async def save_session_to_memory(callback_context):
    """After each agent turn, save the session to Memory Bank for long-term recall."""
    try:
        memory_service = callback_context._invocation_context.memory_service
        if memory_service:
            await memory_service.add_session_to_memory(
                callback_context._invocation_context.session
            )
    except Exception as e:
        logger.warning(f"Failed to save session to memory: {e}")


root_agent = Agent(
    name="adkbot",
    model="gemini-2.5-flash",
    description="Secure personal assistant capable of orchestrating specialized tasks.",
    instruction=SYSTEM_PROMPT,
    sub_agents=[search_agent, gmail_agent, calendar_agent, drive_agent],
    before_agent_callback=load_memory_on_start,
    after_agent_callback=save_session_to_memory,
)
