import logging
import time
from typing import Any, Callable, Dict

from agent.errors import ApprovalTimeout

logger = logging.getLogger(__name__)

# Simulating an internal pending action store. In Phase 4, this goes to Firestore.
pending_approvals: Dict[str, Dict[str, Any]] = {}

def request_approval(chat_id: int, action_name: str, payload_desc: str, callback: Callable):
    """
    Registers a pending action that requires explicit user approval via Telegram.
    This demonstrates the Human-in-the-Loop flow.
    """
    action_id = f"{chat_id}_{int(time.time())}"
    
    pending_approvals[action_id] = {
        "chat_id": chat_id,
        "action": action_name,
        "payload": payload_desc,
        "callback": callback,
        "timestamp": time.time()
    }
    
    logger.info(f"Requested human approval for: {action_id} -> {action_name}")
    # In a real async flow, we would send a Telegram msg with InlineKeyboard
    # and suspend the agent tool execution until the callback is triggered.
    return action_id

def process_approval(action_id: str, approved: bool) -> str:
    """Processes an approval triggered by a Telegram webhook."""
    if action_id not in pending_approvals:
        return "Action expired or invalid."
        
    action = pending_approvals.pop(action_id)
    
    if time.time() - action["timestamp"] > 300: # 5 min timeout
        raise ApprovalTimeout("Action timed out before approval.")
        
    if approved:
        logger.info(f"Action {action['action']} approved by human.")
        # Execute the original callback
        result = action["callback"]()
        return f"Executed safely: {result}"
    else:
        logger.warning(f"Action {action['action']} rejected by human.")
        return "Action cancelled by user."
