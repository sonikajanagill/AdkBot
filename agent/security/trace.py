import functools
import logging

from google.cloud import trace_v1

logger = logging.getLogger(__name__)

_trace_client = None

def get_trace_client():
    global _trace_client
    if not _trace_client:
        try:
            _trace_client = trace_v1.TraceServiceClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Trace client: {e}")
    return _trace_client

def traced(span_name: str):
    """
    Decorator to wrap a function in a Cloud Trace span.
    Helps measure latency of security layers.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # In a real environment, we would link this to the incoming GCP trace header
            logger.debug(f"[Trace Start] {span_name}")
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                logger.debug(f"[Trace End] {span_name}")
        return wrapper
    return decorator
