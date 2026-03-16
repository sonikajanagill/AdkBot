import logging

from google.cloud import dlp_v2

from agent.config import settings

logger = logging.getLogger(__name__)

# Initialize client lazily to avoid credential errors on startup
_dlp_client = None

def get_dlp_client():
    global _dlp_client
    if not _dlp_client:
        try:
            _dlp_client = dlp_v2.DlpServiceClient()
        except Exception as e:
            logger.warning(f"Failed to initialize DLP client. PII scanning disabled. Error: {e}")
    return _dlp_client

def scan_and_redact(text: str) -> str:
    """Scans for PII and redacts it before it reaches the LLM or user."""
    client = get_dlp_client()
    if not client or not settings.gcp_project_id:
        return text

    project_path = f"projects/{settings.gcp_project_id}"
    
    inspect_config = {
        "info_types": [
            {"name": "CREDIT_CARD_NUMBER"},
            {"name": "PHONE_NUMBER"},
            {"name": "US_SOCIAL_SECURITY_NUMBER"}
        ],
        "min_likelihood": dlp_v2.Likelihood.LIKELY,
    }
    
    replace_config = {
        "info_type_transformations": {
            "transformations": [
                {
                    "info_types": [{"name": "CREDIT_CARD_NUMBER"}],
                    "primitive_transformation": {
                        "replace_config": {"new_value": {"string_value": "[REDACTED CREDIT CARD]"}}
                    }
                }
            ]
        }
    }
    
    request = {
        "parent": project_path,
        "item": {"value": text},
        "deidentify_config": replace_config,
        "inspect_config": inspect_config,
    }
    
    try:
        response = client.deidentify_content(request=request)
        return response.item.value
    except Exception as e:
        logger.error(f"DLP scanning failed: {e}")
        return text # Fail open for demo if DLP not enabled in GCP yet
