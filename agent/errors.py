class AgentError(Exception):
    """Base class for all ClawdBot exceptions."""
    pass

class ToolError(AgentError):
    """Raised when a specific tool fails (retryable)."""
    pass

class SecurityError(AgentError):
    """Raised when an action is blocked by guardrails."""
    pass

class ApprovalTimeout(AgentError):
    """Raised when the user does not respond to an approval prompt in time."""
    pass
