# ClawdBot: The Secure Google ADK Assistant

**"From Zero to Secure AI Assistant in a Weekend"**

ClawdBot is a high-security, open-source alternative to typical AI agents, built entirely on **Google Agent Development Kit (ADK) 1.0** and Google Cloud side infrastructure.

This repository demonstrates how to build an agent that is not just powerful, but secure by default with **6 layers of native security.**

## Features

- **ADK 1.0 Multi-Agent Framework**: A root orchestrator delegating to specialized Gemini 2.0 Flash subagents for Gmail, Calendar, Drive, and Search.
- **DLP PII Filtering**: Before a message hits the LLM, Cloud DLP scrubs credit cards, SSNs, and phone numbers.
- **Secret Manager**: Credentials are never loaded from `.env` files in production.
- **IAM Least Privilege**: The Cloud Run agent runs with a tightly restricted service account (cannot destroy infrastructure).
- **Human-in-the-Loop Approval**: Destructive actions (like creating a calendar event) pause execution and await explicit user approval via Telegram.
- **Cloud Trace**: Full visibility into latency and action execution.
- **WIF for CI/CD**: Keyless GitHub Actions deployment via Workload Identity Federation.
- **Firestore Memory**: Persistent cross-session conversation memory and tracking.

## Architecture

![Architecture](https://via.placeholder.com/800x400?text=Architecture+Diagram)

## Setup and Development

1. **Local Setup:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Environment Variables:**
   Copy `.env-example` to `.env` and fill in your Gemini API Key and Telegram Bot Token.

3. **Running the ADK Dev Server:**
   You can run tests locally without Telegram using the built-in ADK UI:
   ```bash
   adk web
   ```

4. **Running the FastAPI Gateway locally (for Telegram):**
   ```bash
   uvicorn agent.main:app --reload
   ```
   *Note: To receive Telegram webhooks locally, expose port 8000 using ngrok: `ngrok http 8000`.*

## Deployment

The entire stack is configured in modular Terraform located in the `terraform/` directory.

```bash
cd terraform
terraform init
terraform apply -var-file=environments/dev.tfvars
```

Once deployed, GitHub Actions will handle subsequent updates automatically via WIF.

## Testing

Structured tests cover the agent logic, security pipelines (DLP/Guards), and API integration.

```bash
pytest tests/ -v
```

---
*Built as a secure reference implementation for Google Cloud Agentic Workloads.*
