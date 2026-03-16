import logging

from agent.errors import SecurityError

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "you are now a",
    "system prompt",
    "developer mode",
]

def check_input_safety(text: str) -> bool:
    """
    Checks if the input text contains known prompt injection attacks.
    Raises SecurityError if malicious content is detected.
    """
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in text_lower:
            logger.warning(f"Blocked potential prompt injection: matched '{pattern}'")
            raise SecurityError(
                "Your request triggered a security filter. Please rephrase your input."
            )
            
    if len(text) > 4000:
        raise SecurityError("Input exceeds maximum allowed length.")
        
    return True
