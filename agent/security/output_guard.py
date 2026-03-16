import logging
import re

logger = logging.getLogger(__name__)

# Basic regex for catching leaked bearer tokens or API keys
TOKEN_REGEX = re.compile(r'(Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*)|([A-Za-z0-9_-]{39})')

def check_output_safety(text: str) -> str:
    """
    Scans agent generated text for potential leaked tokens and strips them.
    In real usage, this might also involve another LLM pass or DLP.
    """
    if TOKEN_REGEX.search(text):
        logger.warning("Agent attempted to output a potential token/secret. Redacting.")
        text = TOKEN_REGEX.sub("[REDACTED SECRET]", text)
    
    return text
