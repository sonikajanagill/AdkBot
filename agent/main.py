import logging
import os

import google.auth
import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import VertexAiMemoryBankService
from google.genai import types

from agent.config import settings
from agent.errors import AgentError
from agent.root_agent import root_agent

# Set up Vertex AI environment
_, project_id = google.auth.default()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id or settings.gcp_project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", settings.gcp_location)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AdkBot Gateway", version="1.0.0")

# Create the ADK runner with Memory Bank and auto session creation
APP_NAME = "adkbot"
session_service = InMemorySessionService()
memory_service = VertexAiMemoryBankService(
    project=settings.gcp_project_id,
    location=settings.gcp_location,
    agent_engine_id=settings.agent_engine_id,
)
logger.info(f"Memory Bank initialized with engine ID: {settings.agent_engine_id}")

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
    memory_service=memory_service,
    auto_create_session=True,
)


def run_agent(user_id: str, session_id: str, message_text: str) -> str:
    """Run the ADK agent and collect the final response text."""
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message_text)],
    )
    all_text_parts = []
    for event in runner.run(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        logger.info(f"Event from agent={event.author}, final={event.is_final_response()}, "
                     f"has_content={bool(event.content)}")
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    logger.info(f"  text part ({len(part.text)} chars): {part.text[:100]}...")
                    all_text_parts.append(part.text)
                elif part.function_call:
                    logger.info(f"  function_call: {part.function_call.name}")
                elif part.function_response:
                    logger.info(f"  function_response: {part.function_response.name}")

    # Return the last non-empty text part (the final agent response)
    final_text = ""
    for text in reversed(all_text_parts):
        if text.strip():
            final_text = text
            break

    logger.info(f"Final response ({len(final_text)} chars): {final_text[:200]}")
    return final_text or "I processed your request but have no response to show."


async def send_telegram_message(chat_id: int, text: str) -> None:
    """Sends a message back to the user via Telegram Bot API."""
    if not settings.telegram_bot_token:
        logger.warning("No Telegram token configured. Skipping message send.")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")


async def process_telegram_update(update: dict) -> None:
    """Background task to process the update and run the ADK agent."""
    try:
        if "message" not in update or "text" not in update["message"]:
            return

        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message["text"]

        logger.info(f"Processing message from {chat_id}: {text}")

        # Send typing indicator
        if settings.telegram_bot_token:
            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendChatAction"
            async with httpx.AsyncClient() as client:
                await client.post(url, json={"chat_id": chat_id, "action": "typing"})

        # Run ADK agent
        try:
            user_id = str(chat_id)
            session_id = f"telegram-{chat_id}"
            reply_text = run_agent(user_id, session_id, text)

        except AgentError as e:
            logger.error(f"Agent error: {e}")
            reply_text = f"I ran into an issue: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error running agent: {e}", exc_info=True)
            reply_text = "Sorry, I encountered an unexpected error while processing your request."

        await send_telegram_message(chat_id, reply_text)

    except Exception as e:
        logger.error(f"Error in process_telegram_update background task: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/ready")
async def readiness_check():
    return {"status": "ready"}


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>AdkBot Gateway</title>
            <style>body { font-family: sans-serif; padding: 2rem; }</style>
        </head>
        <body>
            <h1>AdkBot API is running</h1>
            <p>To interact via browser UI during local dev, use the ADK CLI:</p>
            <code>adk web</code>
            <p>For production, configure the Telegram Webhook to point to <code>/webhook/telegram</code></p>
        </body>
    </html>
    """


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        update = await request.json()
        background_tasks.add_task(process_telegram_update, update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error parsing webhook request: {e}")
        return {"ok": False}


@app.post("/scheduled/briefing")
async def morning_briefing(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        chat_id = payload.get("chat_id")
        if not chat_id:
            return {"error": "Missing chat_id"}

        logger.info(f"Starting scheduled briefing for {chat_id}")

        async def run_briefing():
            try:
                prompt = (
                    "Please read my latest emails and check my calendar for today, "
                    "then provide a concise morning briefing."
                )
                user_id = str(chat_id)
                session_id = f"briefing-{chat_id}"
                reply = run_agent(user_id, session_id, prompt)
                await send_telegram_message(chat_id, f"**Morning Briefing**\n\n{reply}")
            except Exception as e:
                logger.error(f"Failed to run briefing for {chat_id}: {e}")

        background_tasks.add_task(run_briefing)
        return {"status": "briefing started"}
    except Exception as e:
        logger.error(f"Error starting briefing: {e}")
        return {"error": str(e)}
