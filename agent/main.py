import logging

import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse

from agent.config import settings
from agent.errors import AgentError
from agent.memory import memory_manager
from agent.root_agent import root_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ClawdBot Gateway", version="1.0.0")

async def send_telegram_message(chat_id: int, text: str):
    """Sends a message back to the user via Telegram Bot API."""
    if not settings.telegram_token:
        logger.warning("No Telegram token configured. Skipping message send.")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

async def process_telegram_update(update: dict):
    """Background task to process the update and run the ADK agent."""
    try:
        if "message" not in update or "text" not in update["message"]:
            return
            
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message["text"]
        
        logger.info(f"Processing message from {chat_id}: {text}")
        
        # Send typing indicator
        url = f"https://api.telegram.org/bot{settings.telegram_token}/sendChatAction"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": chat_id, "action": "typing"})
            
        # Run ADK agent
        try:
            # Memory injection (Phase 4)
            _ = memory_manager.get_recent_context(chat_id)
            
            # The agent.run will consume the latest text
            response = root_agent.run(text)
            reply_text = response.text
            
            # Save context to Firestore
            memory_manager.save_message(chat_id, "user", text)
            memory_manager.save_message(chat_id, "assistant", reply_text)
                
        except AgentError as e:
            logger.error(f"Agent error: {e}")
            reply_text = f"⚙️ I ran into an issue: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error running agent: {e}", exc_info=True)
            reply_text = "❌ Sorry, I encountered an unexpected error while processing your request."
            
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
            <title>ClawdBot Gateway</title>
            <style>body { font-family: sans-serif; padding: 2rem; }</style>
        </head>
        <body>
            <h1>ClawdBot API is running</h1>
            <p>To interact via browser UI during local dev, use the ADK CLI:</p>
            <code>adk web</code>
            <p>For production, configure the Telegram Webhook to point to <code>/webhook/telegram</code></p>
        </body>
    </html>
    """

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming Telegram updates. Fast response to Telegram is required, 
    so we process the agent interaction in the background.
    """
    try:
        update = await request.json()
        background_tasks.add_task(process_telegram_update, update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error parsing webhook request: {e}")
        return {"ok": False}

@app.post("/scheduled/briefing")
async def morning_briefing(request: Request, background_tasks: BackgroundTasks):
    """
    Triggered by Cloud Scheduler daily.
    Will dispatch the briefing flow for configured users.
    """
    try:
        payload = await request.json()
        chat_id = payload.get("chat_id")
        if not chat_id:
            return {"error": "Missing chat_id"}
            
        logger.info(f"Starting scheduled briefing for {chat_id}")
        
        async def run_briefing():
            try:
                # Instruct the agent to generate a morning briefing autonomously
                prompt = (
                    "Please read my latest emails and check my calendar for today, "
                    "then provide a concise morning briefing."
                )
                response = root_agent.run(prompt)
                await send_telegram_message(chat_id, f"🌅 **Morning Briefing**\n\n{response.text}")
            except Exception as e:
                logger.error(f"Failed to run briefing for {chat_id}: {e}")
                
        background_tasks.add_task(run_briefing)
        return {"status": "briefing started"}
    except Exception as e:
        logger.error(f"Error starting briefing: {e}")
        return {"error": str(e)}
