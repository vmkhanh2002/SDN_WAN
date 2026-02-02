# LLMs for User Intent Task Orchestration — Medical Research Lab Environment

## Short summary

This repository is a prototype that demonstrates using LLMs to interpret clinician intents and orchestrate tasks across MCP-style servers (device orchestration, access control, network monitoring, verification, and clinical analysis) in a medical research lab environment.

Quick start

1. Create and activate a Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the server:

```bash
# from project root
uvicorn fastmcp:app --reload --port 8000
```

Run the client CLI

```bash
python3 clients/clients.py 


```

GEMINI API Key Generation:
- Create .env file and add GEMINI_API_KEY variable with your own private api key.
- Guide to add: https://ai.google.dev/gemini-api/docs/api-key

New task endpoints (POST):
- `/tasks/device-orchestration` — body: { action: "restart" | "provision", deviceId?: "DEV-1" }
- `/tasks/access-control` — body: { op: "check" | "grant", user?: "nurse-1", permission?: "read_patient", role?: "tech" }
- `/tasks/network-monitoring` — body: {} (returns summary)
- `/tasks/verification` — body: {} (returns issues and alerts)

Notes
- Data files are under `data/`.
- Task implementations live under `servers/tasks/` as separate routers and modules.
- LLM integration is optional and **client-driven**: clients may supply an LLM API key to request LLM-powered explanations, but the server does not store LLM credentials.


Quick verification (no pytest needed):

```bash
python3 tests/test_tasks.py
```

