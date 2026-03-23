# A2A Implementation Plan — Agent Critic 2.0

This plan focuses specifically on the **Agent2Agent (A2A)** protocol, enabling the Agent Critic system to operate as a distributed network of specialized micro-services.

## Objective
Decouple the "Experts" (Security, Quality, Architecture) from the "Root Agent" so they can be deployed, scaled, and updated independently or even across different cloud regions.

## 1. Service Architecture
We will transform the current sub-agents into standalone A2A services.

| Service | Port | Responsibility |
|---|---|---|
| **Security Service** | 8001 | Handles code security analysis. |
| **Quality Service** | 8002 | Handles code maintainability and style. |
| **Architecture Service** | 8003 | Handles design patterns and structure. |
| **Root (Coordinator)** | 8000 | Orchestrates the workflow and synthesizes results. |

## 2. Implementation Steps

### Phase A: Exposing Experts (The "Server" Side)
Each expert will be turned into an A2A server.
1. Create a `main.py` for each expert in `2.0/experts/`.
2. Wrap the expert agent with `to_a2a()`.
3. Serve using `uvicorn`.

```python
# Example: 2.0/experts/security/main.py
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from .agent import security_agent

app = to_a2a(security_agent, port=8001)
```

### Phase B: Consuming Experts (The "Client" Side)
The Coordinator agent will interact with these services via the `RemoteA2aAgent` proxy.
1. Update the `Workflow` in `2.0/agent.py`.
2. Replace local agents with `RemoteA2aAgent` instances pointing to the service URLs.

```python
# Example: 2.0/agent.py
from google.adk.workflow.agents.remote_a2a_agent import RemoteA2aAgent

security_expert = RemoteA2aAgent(url="http://localhost:8001")
# ...
workflow = Workflow(
    edges=[("START", ingestion_agent, security_expert, ...)]
)
```

## 3. Deployment & Scaling
- **Phase 1 (Local):** Run all services on different ports on localhost.
- **Phase 2 (Cloud):** Deploy each service to a separate Cloud Run instance. Update the `RemoteA2aAgent` URLs to point to the Cloud Run endpoints.

## 4. Verification
1. Start all three expert services.
2. Run the Coordinator agent.
3. Verify that the Coordinator successfully fetches "Agent Cards" from all three services and executes the cross-network workflow.
