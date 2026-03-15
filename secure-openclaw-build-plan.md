# Build Plan: Secure OpenClaw Alternative on Google Cloud
**"From Zero to Secure AI Assistant in a Weekend"**

---

## Overview

| Item | Detail |
|------|--------|
| **Total Build Time** | 12–16 hours (spread over a weekend) |
| **Estimated Cost** | $0 – $5/month (free tier + pay-as-you-go) |
| **Prerequisites** | GCP account, Python 3.11+, Telegram account |
| **Final Result** | A Telegram-based AI assistant with 4 tools, persistent memory, proactive scheduling, and 6 security layers — all deployed on Cloud Run |
| **GitHub Deliverable** | Complete repo with Terraform IaC, ADK agent code, and README |

---

## Phase 0: Foundation Setup (1 hour)

### 0.1 — GCP Project Setup
- [ ] Create a new GCP project: `secure-agent-demo`
- [ ] Enable billing (free tier covers everything, but billing must be active)
- [ ] Set project-level budget alert at $5/month (good habit to demonstrate in article)
- [ ] Enable required APIs:
  ```
  Cloud Run API
  Cloud Build API
  Secret Manager API
  Cloud Scheduler API
  Firestore API
  Cloud DLP API
  Cloud Logging API
  Artifact Registry API
  ```

### 0.2 — Local Development Environment
- [ ] Create project directory structure:
  ```
  secure-agent/
  ├── agent/
  │   ├── __init__.py
  │   ├── main.py              # FastAPI gateway
  │   ├── agent.py             # ADK agent orchestrator
  │   ├── memory.py            # Firestore memory manager
  │   ├── security/
  │   │   ├── __init__.py
  │   │   ├── dlp_filter.py    # PII detection pre-processor
  │   │   ├── input_guard.py   # Input validation
  │   │   ├── output_guard.py  # Output sanitisation
  │   │   └── approval.py      # Human-in-the-loop flow
  │   └── tools/
  │       ├── __init__.py
  │       ├── gmail_reader.py
  │       ├── calendar_mgr.py
  │       ├── file_organiser.py
  │       └── web_search.py
  ├── terraform/
  │   ├── main.tf
  │   ├── variables.tf
  │   ├── cloud_run.tf
  │   ├── secrets.tf
  │   ├── scheduler.tf
  │   ├── iam.tf
  │   └── firestore.tf
  ├── tests/
  │   ├── test_agent.py
  │   ├── test_security.py
  │   └── test_tools.py
  ├── Dockerfile
  ├── requirements.txt
  ├── .env.example            # Template only — NO real secrets
  └── README.md
  ```
- [ ] Create Python virtual environment: `python -m venv .venv`
- [ ] Install core dependencies:
  ```
  google-adk
  google-cloud-firestore
  google-cloud-dlp
  google-cloud-secret-manager
  google-cloud-logging
  python-telegram-bot
  fastapi
  uvicorn
  ```

### 0.3 — Telegram Bot Creation
- [ ] Open Telegram → search @BotFather → `/newbot`
- [ ] Name: `SecureAgentDemo` (or your preference)
- [ ] Save the bot token (DO NOT commit — goes into Secret Manager in Phase 3)
- [ ] Set bot description: `/setdescription` → "A secure AI assistant built on Google Cloud"

### 0.4 — Gemini API Key
- [ ] Go to [AI Studio](https://aistudio.google.com/apikey)
- [ ] Generate API key for your project
- [ ] Note free tier limits: 15 RPM, 1M TPD, 1,500 RPD for Gemini 2.0 Flash
- [ ] Save key (goes into Secret Manager — never in code)

**Phase 0 Checkpoint:** Project created, APIs enabled, Telegram bot exists, Gemini key ready, local dev structure set up.

---

## Phase 1: ADK Agent Core — The Brain (3 hours)

### 1.1 — Basic ADK Agent (45 mins)
Build a minimal agent that responds to text input using Gemini.

- [ ] Create `agent/agent.py`:
  - Initialise ADK agent with Gemini 2.0 Flash as the model
  - Define agent system prompt:
    > "You are a helpful personal assistant. You can read emails, manage calendars, organise files, and search the web. Always explain what you're about to do before doing it. For any destructive action (delete, send, modify), ask for explicit confirmation first."
  - Set up basic conversation handling (text in → text out)
- [ ] Test locally with ADK's built-in dev server: `adk web`
- [ ] Verify: Send "Hello, what can you do?" → agent responds with capabilities list

### 1.2 — First Tool: Web Search (30 mins)
Start with the simplest tool to prove the ADK tool pattern works.

- [ ] Create `agent/tools/web_search.py`:
  - Use Google Custom Search JSON API (100 queries/day free)
  - Or use `googlesearch-python` library for zero-config demo
  - ADK `@tool` decorator with clear docstring (this is what the LLM reads)
- [ ] Register tool with agent
- [ ] Test: "Search for the latest news about OpenClaw security" → agent calls tool → returns summary

### 1.3 — Gmail Reader Tool (45 mins)
The tool that makes the demo feel like OpenClaw.

- [ ] Set up Gmail API OAuth:
  - Create OAuth 2.0 credentials in GCP console (type: Desktop app for local dev)
  - Download `credentials.json` (local dev only — production uses WIF)
  - First run: browser-based auth → generates `token.json`
- [ ] Create `agent/tools/gmail_reader.py`:
  - `read_inbox(max_results: int = 5)` → returns subject, sender, snippet
  - `search_emails(query: str)` → Gmail search syntax
  - `read_email(message_id: str)` → full email body
  - **READ-ONLY** — no send/delete/modify at this stage
- [ ] Register with agent
- [ ] Test: "Show me my latest 3 emails" → agent calls tool → returns formatted email list

### 1.4 — Calendar Manager Tool (30 mins)
- [ ] Create `agent/tools/calendar_mgr.py`:
  - `list_events(days_ahead: int = 7)` → upcoming events
  - `check_availability(date: str)` → free/busy slots
  - `create_event(title, start, end, description)` → **requires confirmation** (Phase 4)
- [ ] Register with agent
- [ ] Test: "What's on my calendar this week?" → formatted event list

### 1.5 — File Organiser Tool (30 mins)
- [ ] Create `agent/tools/file_organiser.py`:
  - Uses Google Drive API
  - `list_recent_files(max_results: int = 10)` → recent Drive files
  - `search_files(query: str)` → Drive file search
  - `summarise_document(file_id: str)` → reads doc content, returns Gemini summary
  - **READ-ONLY** — no move/delete/rename at this stage
- [ ] Register with agent
- [ ] Test: "Find my recent documents about MLOps" → returns matching files

**Phase 1 Checkpoint:** ADK agent running locally with 4 tools. You can have a conversation, search the web, read emails, check calendar, and find files. All via ADK dev server.

---

## Phase 2: Telegram Integration — The Interface (2 hours)

### 2.1 — FastAPI Gateway (30 mins)
- [ ] Create `agent/main.py`:
  - FastAPI app with webhook endpoint: `POST /webhook/telegram`
  - Parse Telegram update → extract message text and chat_id
  - Pass text to ADK agent → get response
  - Send response back via Telegram Bot API
  - Health check endpoint: `GET /health`
- [ ] Test locally with ngrok:
  - Run `ngrok http 8080`
  - Set Telegram webhook: `https://{ngrok-url}/webhook/telegram`
  - Send message in Telegram → response appears

### 2.2 — Rich Telegram Responses (30 mins)
Make the demo feel polished — this matters for the article screenshots.

- [ ] Format agent responses with Telegram Markdown:
  - Email subjects in **bold**
  - Calendar events with 📅 time formatting
  - Tool actions with inline status indicators
  - Error messages with clear explanation
- [ ] Add "typing" indicator while agent processes
- [ ] Add `/help` command with available capabilities
- [ ] Add `/status` command showing connected tools

### 2.3 — Conversation Context (30 mins)
- [ ] Implement session tracking by Telegram chat_id
- [ ] Maintain last 10 messages in memory for context
- [ ] Agent can reference previous messages: "Summarise that last email you showed me"
- [ ] Test multi-turn conversations work naturally

### 2.4 — Basic Error Handling (30 mins)
- [ ] Gemini API rate limit → friendly "I'm thinking, try again in a moment"
- [ ] Tool failures → "I couldn't access your emails right now. Here's why: {error}"
- [ ] Timeout handling → long operations get progress updates
- [ ] Invalid input → guide user to correct format

**Phase 2 Checkpoint:** Working Telegram bot. Message it from your phone, ask about emails, calendar, files. Multi-turn conversations work. Screenshots look clean for the article.

---

## Phase 3: Security Layers — The Differentiator (3 hours)

This is the phase that makes your article unique. Each security layer directly maps to a documented OpenClaw vulnerability.

### 3.1 — Secret Manager Integration (30 mins)
**Solves:** OpenClaw stores API keys in `.env` files on disk (Snyk finding: 7.1% of ClawHub skills leak credentials).

- [ ] Create secrets in Secret Manager:
  ```
  TELEGRAM_BOT_TOKEN
  GEMINI_API_KEY
  GMAIL_OAUTH_TOKEN
  ```
- [ ] Update application code to fetch from Secret Manager at startup:
  ```python
  from google.cloud import secretmanager
  
  def get_secret(secret_id: str) -> str:
      client = secretmanager.SecretManagerServiceClient()
      name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
      response = client.access_secret_version(request={"name": name})
      return response.payload.data.decode("UTF-8")
  ```
- [ ] Remove all hardcoded credentials from code
- [ ] Delete local `.env` file, update `.gitignore`
- [ ] **Article callout:** Side-by-side comparison of OpenClaw's `.env` file vs your Secret Manager approach

### 3.2 — Cloud DLP Pre-Processing Filter (45 mins)
**Solves:** OpenClaw has zero PII detection. User messages and tool outputs can contain sensitive data that gets sent to LLM APIs.

- [ ] Create `agent/security/dlp_filter.py`:
  - `scan_for_pii(text: str) -> DLPResult`:
    - Scans input text using Cloud DLP API
    - Detects: credit cards, phone numbers, emails, national IDs, names
    - Returns: found PII types + redacted text
  - `filter_input(message: str) -> str`:
    - Runs DLP scan on user message before it reaches Gemini
    - If PII found: warns user via Telegram, sends redacted version to agent
  - `filter_output(response: str) -> str`:
    - Scans agent response before sending back to user
    - Catches cases where tools return PII from emails/files
- [ ] Wire into gateway: input → DLP filter → agent → DLP filter → output
- [ ] Test: Send "My credit card is 4111-1111-1111-1111" → agent receives redacted version + user gets warning
- [ ] **Article callout:** The Meta AI safety director's agent had full access to her email. DLP would have flagged the PII in those emails before the agent could act on them.

### 3.3 — Input/Output Guard Rails (30 mins)
**Solves:** OpenClaw has no content filtering beyond whatever the LLM model provides. Prompt injection through tool outputs is documented.

- [ ] Create `agent/security/input_guard.py`:
  - Block prompt injection patterns:
    - "Ignore previous instructions"
    - "You are now a..."
    - System prompt extraction attempts
  - Validate message length (prevent context stuffing)
  - Rate limiting per user (prevent abuse)
  
- [ ] Create `agent/security/output_guard.py`:
  - Scan tool outputs for injection attempts before feeding back to agent
  - Validate agent responses don't contain:
    - Raw credentials or tokens
    - Internal system details
    - Instructions to bypass security
  - Truncate excessively long outputs

- [ ] **Article callout:** OpenClaw's Zenity-documented vulnerability — a malicious skill can inject persistent backdoor instructions. Your guard rails prevent this attack vector.

### 3.4 — Human-in-the-Loop Approval (45 mins)
**Solves:** OpenClaw executes actions autonomously with no confirmation. Summer Yue's agent mass-deleted emails without asking.

- [ ] Create `agent/security/approval.py`:
  - Define action risk levels:
    - **LOW (auto-approve):** Read email, list files, check calendar, web search
    - **MEDIUM (confirm once):** Summarise document, search emails
    - **HIGH (always confirm):** Create event, send email, modify files, delete anything
  - Approval flow:
    1. Agent decides to take HIGH-risk action
    2. Agent sends Telegram message: "I'd like to create a calendar event: {details}. Approve? ✅ / ❌"
    3. User taps inline button
    4. Only on ✅ does the tool execute
  - Implement Telegram inline keyboard for approve/reject
  - Timeout after 5 minutes → action cancelled with explanation
  
- [ ] Wire into ADK tool execution pipeline
- [ ] Test: "Schedule a meeting tomorrow at 3pm" → confirmation prompt → approve → event created
- [ ] **Article callout:** Direct comparison — "OpenClaw's agent deleted 4,000 emails without asking. Our agent asks before creating a single calendar event."

### 3.5 — IAM Conditions + Least Privilege (30 mins)
**Solves:** OpenClaw runs with whatever permissions the user's machine has — typically full access to everything.

- [ ] Create dedicated service account: `agent-runtime@{project}.iam.gserviceaccount.com`
- [ ] Grant minimum permissions:
  ```
  roles/secretmanager.secretAccessor    (read secrets only)
  roles/datastore.user                  (Firestore read/write)
  roles/dlp.user                        (DLP scan only)
  roles/logging.logWriter               (write logs only)
  ```
- [ ] Add IAM Condition on service account:
  - Time-based: only active during working hours (optional — shows the pattern)
  - Resource-based: can only access specific Firestore collection
- [ ] **Article callout:** OpenClaw documentation literally says "give it access to everything." IAM Conditions let you be surgical.

**Phase 3 Checkpoint:** All 6 security layers active. Every message flows through DLP, guard rails filter inputs/outputs, destructive actions require approval, secrets are in Secret Manager, IAM follows least privilege. You can now demonstrate each layer with a concrete test.

---

## Phase 4: Persistent Memory — The Intelligence (1.5 hours)

### 4.1 — Firestore Memory Schema (30 mins)
- [ ] Create Firestore database (Native mode, free tier)
- [ ] Design collections:
  ```
  conversations/{chat_id}/messages/{msg_id}
    - role: "user" | "assistant"
    - content: string
    - timestamp: datetime
    - tools_used: string[]
  
  users/{chat_id}/preferences
    - name: string
    - timezone: string
    - summary_style: "brief" | "detailed"
    - approved_actions: string[]
  
  agent_state/{chat_id}
    - last_active: datetime
    - pending_approvals: map[]
    - context_summary: string (rolling summary of past conversations)
  ```

### 4.2 — Memory Manager (30 mins)
- [ ] Create `agent/memory.py`:
  - `save_message(chat_id, role, content, tools_used)`
  - `get_recent_context(chat_id, limit=20) -> list[Message]`
  - `get_user_preferences(chat_id) -> Preferences`
  - `update_context_summary(chat_id)` — periodically compress old conversations into summary using Gemini
- [ ] Integrate with agent — conversation history loaded at each interaction
- [ ] Test: Close and reopen Telegram → agent remembers previous conversation

### 4.3 — Smart Context Window (30 mins)
- [ ] Implement rolling context strategy:
  - Last 10 messages: full content
  - Previous 50 messages: Gemini-generated summary
  - Older: discarded (but stored in Firestore for audit)
- [ ] User preferences persist across sessions
- [ ] Agent learns: "You usually want brief summaries" based on past interactions
- [ ] **Article callout:** OpenClaw's local JSON memory vs cloud-native persistent memory — resilience, security, and multi-device access.

**Phase 4 Checkpoint:** Agent remembers conversations across sessions, learns user preferences, and manages context efficiently. This is where it starts feeling genuinely useful.

---

## Phase 5: Proactive Agent — The Heartbeat (1 hour)

### 5.1 — Cloud Scheduler Setup (20 mins)
- [ ] Create scheduled job: `morning-briefing`
  - Schedule: `0 8 * * 1-5` (8am weekdays)
  - Target: Cloud Run endpoint `POST /scheduled/briefing`
  - Payload: `{"chat_id": "{your_telegram_id}"}`
- [ ] Create endpoint in FastAPI that triggers agent briefing flow

### 5.2 — Morning Briefing Flow (40 mins)
- [ ] Agent autonomously:
  1. Reads top 5 unread emails → generates summary
  2. Checks today's calendar → lists upcoming meetings
  3. Checks weather (optional — simple API call)
  4. Composes briefing message
  5. Sends to Telegram
- [ ] All read-only operations — no approval needed
- [ ] Runs through the same DLP filter — PII in email subjects gets redacted
- [ ] Test: Manually trigger endpoint → receive briefing on Telegram
- [ ] **Article callout:** This is OpenClaw's most loved feature. Ours does the same thing, but every piece of data flows through DLP and no credentials sit on disk.

**Phase 5 Checkpoint:** You wake up to a Telegram briefing every morning. The agent proactively summarises your emails and calendar. All secured.

---

## Phase 6: Cloud Run Deployment — Production (2 hours)

### 6.1 — Containerisation (30 mins)
- [ ] Create `Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY agent/ ./agent/
  CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8080"]
  ```
- [ ] Build and test locally: `docker build -t secure-agent . && docker run -p 8080:8080 secure-agent`
- [ ] Verify all endpoints work in container

### 6.2 — Terraform Infrastructure (45 mins)
- [ ] Write Terraform for all resources:
  - **`cloud_run.tf`**: Service with min 0 / max 1 instances (cost control), 512MB memory, 1 vCPU
  - **`secrets.tf`**: All 3 secrets + IAM bindings for Cloud Run service account to access them
  - **`iam.tf`**: Service account with least-privilege roles + IAM conditions
  - **`firestore.tf`**: Database + indexes for conversations collection
  - **`scheduler.tf`**: Morning briefing cron job targeting Cloud Run URL
- [ ] `terraform init && terraform plan` → review
- [ ] `terraform apply` → infrastructure created

### 6.3 — Deploy and Wire Up (30 mins)
- [ ] Push container to Artifact Registry
- [ ] Deploy to Cloud Run via Terraform (or `gcloud run deploy`)
- [ ] Set Telegram webhook to Cloud Run URL:
  ```
  https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://{CLOUD_RUN_URL}/webhook/telegram
  ```
- [ ] Test end-to-end: Telegram message → Cloud Run → agent → tools → response
- [ ] Verify Cloud Scheduler triggers morning briefing

### 6.4 — Monitoring and Logging (15 mins)
- [ ] Verify Cloud Audit Logs capture:
  - Every Secret Manager access
  - Every Cloud Run invocation
  - Every DLP scan
- [ ] Set up basic alerting:
  - Cloud Run error rate > 5%
  - DLP findings (PII detected) → alert
  - Unusual invocation patterns
- [ ] **Article callout:** OpenClaw has zero audit trail. Every action your agent takes is logged, traceable, and auditable.

**Phase 6 Checkpoint:** Fully deployed on Cloud Run. Accessible from Telegram anywhere. Infrastructure is code (Terraform). All security layers active in production.

---

## Phase 7: WIF Integration — The Enterprise Layer (1.5 hours)

This phase demonstrates the pattern even if the demo only needs basic service accounts. It's the "here's how this scales to enterprise" section of your article.

### 7.1 — WIF for Cross-Cloud Access (45 mins)
**Scenario:** Your agent needs to access an S3 bucket in AWS (simulating enterprise multi-cloud reality).

- [ ] Create Workload Identity Pool: `agent-identity-pool`
- [ ] Create Workload Identity Provider: configured for AWS (or GitHub Actions for demo)
- [ ] Configure service account impersonation:
  ```
  Agent (Cloud Run)
    → WIF Pool (validates identity)
      → Service Account (with specific GCP permissions)
        → Access resources (no key file ever created)
  ```
- [ ] Terraform the entire WIF setup
- [ ] **Article callout:** OpenClaw requires downloading AWS credentials as a file, storing them on disk where any skill can read them. WIF means the credential never exists as a file — it's exchanged in-memory, scoped, and time-limited.

### 7.2 — GitHub Actions CI/CD with WIF (30 mins)
- [ ] Set up WIF for GitHub Actions (no service account key in GitHub Secrets)
- [ ] Create `.github/workflows/deploy.yml`:
  - On push to `main`: build container → push to Artifact Registry → deploy to Cloud Run
  - Authenticate via WIF — zero stored credentials
- [ ] **Article callout:** Even your CI/CD pipeline is keyless. Show the GitHub Actions workflow using WIF vs the traditional service account JSON key approach.

### 7.3 — Document the Security Comparison (15 mins)
Create a comparison table for the article:

| Security Concern | OpenClaw | Your Agent |
|---|---|---|
| API keys | `.env` file on disk | Secret Manager (encrypted, rotated) |
| Cross-cloud auth | Downloaded credential files | WIF (keyless, time-limited) |
| PII in messages | No detection | Cloud DLP pre/post filter |
| Destructive actions | Auto-executed | Human-in-the-loop approval |
| Prompt injection | No protection | Input/output guard rails |
| Audit trail | None | Cloud Audit Logs (every action) |
| Runtime isolation | User's machine (full access) | Cloud Run (sandboxed container) |
| IAM | Whatever user has | Least privilege + conditions |

**Phase 7 Checkpoint:** WIF demonstrated for both cross-cloud access and CI/CD. The enterprise security story is complete with concrete implementation.

---

## Phase 8: Article-Ready Polish (1 hour)

### 8.1 — GitHub Repository Cleanup
- [ ] Comprehensive `README.md`:
  - Architecture diagram (export from your article)
  - Quick start guide (< 15 minutes to deploy)
  - Security features explained
  - Cost breakdown
  - Screenshots of Telegram interactions
- [ ] All code well-commented with security annotations
- [ ] `.env.example` showing required secrets (no real values)
- [ ] `terraform/` directory with complete IaC
- [ ] MIT license

### 8.2 — Demo Screenshots and Recording
- [ ] Screenshot: Telegram conversation showing email summary
- [ ] Screenshot: Human-in-the-loop approval prompt
- [ ] Screenshot: DLP catching PII and warning user
- [ ] Screenshot: Morning briefing message
- [ ] Screenshot: Cloud Audit Logs showing traced actions
- [ ] Screenshot: Secret Manager vs `.env` file comparison
- [ ] Optional: 2-minute screen recording of full demo flow

### 8.3 — Cost Verification
- [ ] After running for 1 week, screenshot actual GCP billing
- [ ] Document real costs per component
- [ ] Compare with OpenClaw's documented $10–$150/month API token costs
- [ ] **Article gold:** "I ran this for a week. Here's my actual bill: $0.43"

---

## Build Verification Checklist

### Core Functionality
- [ ] Send Telegram message → get intelligent response
- [ ] "Show me my emails" → formatted email list
- [ ] "What's on my calendar?" → upcoming events
- [ ] "Find my MLOps documents" → Drive file results
- [ ] "Search for OpenClaw security news" → web results summary
- [ ] Multi-turn conversation with context retention
- [ ] Morning briefing arrives at 8am

### Security Layers
- [ ] Secret Manager: no credentials in code or on disk
- [ ] DLP: credit card number in message → warning + redaction
- [ ] Input guard: "Ignore previous instructions" → blocked
- [ ] Output guard: tool returns PII → redacted before user sees it
- [ ] Approval: "Create a meeting" → confirmation prompt before action
- [ ] IAM: service account has minimum required permissions
- [ ] Audit: all actions visible in Cloud Logging
- [ ] WIF: cross-cloud access without key files

### Article Assets
- [ ] GitHub repo with complete, runnable code
- [ ] Terraform for one-command infrastructure deployment
- [ ] Screenshots of every security layer in action
- [ ] Cost breakdown with real billing data
- [ ] Architecture diagram
- [ ] Security comparison table (OpenClaw vs yours)

---

## Suggested Article Outline (After Build)

> **Title:** "I Built a Secure OpenClaw Alternative on Google Cloud for $0 — Here's Every Security Layer"
>
> 1. **The Problem** — OpenClaw is amazing but terrifying (Summer Yue story, Lethal Trifecta, Google VP quote)
> 2. **The Architecture** — What we're building and why (diagram)
> 3. **The Brain** — ADK + Gemini 2.0 Flash (free tier, open source)
> 4. **The Tools** — Gmail, Calendar, Drive, Web Search (reader builds along)
> 5. **The Interface** — Telegram bot (10-minute setup)
> 6. **Security Layer 1: Secrets** — Secret Manager vs .env files
> 7. **Security Layer 2: PII Protection** — Cloud DLP filter
> 8. **Security Layer 3: Guard Rails** — Input/output validation
> 9. **Security Layer 4: Human Approval** — The Summer Yue prevention layer
> 10. **Security Layer 5: Least Privilege** — IAM Conditions
> 11. **Security Layer 6: Keyless Auth** — WIF for cross-cloud
> 12. **The Heartbeat** — Proactive morning briefings
> 13. **The Memory** — Firestore persistent context
> 14. **The Bill** — Real cost breakdown ($0.43/week)
> 15. **What Enterprise Adds** — Where Vertex AI Guardrails and AlloyDB upgrade this
> 16. **Try It Yourself** — GitHub repo link, 15-minute quick start
>
> **Estimated reading time:** 15-20 minutes
> **GitHub companion:** Complete, deployable code

---

## What This Builds Toward (GDE Portfolio)

This single project generates:

| Output | Detail |
|--------|--------|
| **Medium article** | The main 15-20 min technical deep-dive |
| **GitHub repo** | Deployable code with Terraform IaC |
| **Conference talk** | "I Built a Secure OpenClaw Alternative on GCP" (30 min talk) |
| **Lightning talk** | "6 Security Layers OpenClaw Doesn't Have" (10 min) |
| **LinkedIn post series** | One post per security layer (6 posts over 2 weeks) |
| **AI Guild session** | Internal walkthrough of the build |
| **WCC workshop** | Hands-on "Build Your Own AI Assistant" session |
| **Follow-up articles** | One per security layer as standalone deep-dives |

---

*Build it. Screenshot everything. Write the article from real experience. That's GDE-level content.*
