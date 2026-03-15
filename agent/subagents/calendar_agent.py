import logging

from google.adk.agents import Agent
from google.adk.tools import Tool

logger = logging.getLogger(__name__)

def list_events(days_ahead: int = 7) -> str:
    """List upcoming calendar events."""
    logger.info(f"Listing events for {days_ahead} days ahead.")
    return "Mock Calendar: Meeting at 3pm tomorrow."

def check_availability(date: str) -> str:
    """Check if the user is free on a specific date and time."""
    logger.info(f"Checking availability for: {date}")
    return f"Mock Availability for {date}: Free after 2pm."

def create_event(title: str, start: str, end: str, description: str) -> str:
    """Create a new calendar event. Will require approval."""
    logger.info(f"Creating event: {title} from {start} to {end}")
    # Later this will hit the Approval engine before execution
    return f"Mock Event Created: {title}"

list_events_tool = Tool.from_function(list_events)
check_availability_tool = Tool.from_function(check_availability)
create_event_tool = Tool.from_function(create_event)

calendar_agent = Agent(
    name="CalendarAgent",
    model="gemini-2.0-flash",
    description="Manages the user's agenda, availability, and scheduling.",
    instruction="You help the user manage their time. Check their calendar and schedule events if asked.",
    tools=[list_events_tool, check_availability_tool, create_event_tool]
)
