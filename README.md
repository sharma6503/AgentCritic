# Agentic Code Reviewer

A powerful, multi-agent AI code review platform built with **Google ADK (Agent Development Kit)**. This application orchestrates a swarm of specialized AI agents to analyze your codebase concurrently, providing deep insights on architecture, code quality, security, and runtime validation.

## ✨ Features

- **Multi-Agent Orchestration**: Utilizes a fleet of specialized experts:
  - **Ingestion Agent**: Fast-paths GitHub repositories, ZIP archives, and pasted code into memory. Now robust against binary edge-cases and empty payloads.
  - **ADK Architecture Expert**: Analyzes system design and architectural patterns.
  - **Quality Expert**: Evaluates code quality, maintainability, and standard practices.
  - **Security Expert**: Identifies vulnerabilities, deployment flaws, and security risks.
  - **Validator Expert**: Runs dynamic code validation checks.
  - **Synthesis Agent**: Compiles the individual expert traces into a comprehensive, finalized Markdown report.
  - **HTML Agent**: Automatically converts the synthesis report into an ultra-premium, beautifully animated HTML document (cycling randomly through Cyberpunk, Minimalist, Oceanic, Developer, and Sunset Glass themes).
- **Background Session Independence**: Switch between past sessions seamlessly while heavy reviews run concurrently in the background without locking up the UI. State persistence is securely handled by SQLite metadata matching.
- **Context Caching & Resumability**: Leverages ADK `ContextCacheConfig` (min 32k tokens) and `ResumabilityConfig` to dramatically reduce redundant token usage and allow pausing/resumption of the multi-agent pipeline workflow under heavy load.
- **GitHub Fast-Path Ingestion**: Automatically intercepts GitHub URLs and downloads repositories as zip archives over the GitHub REST API, bypassing slow LLM file-by-file agent fetching for ingestion times measured in seconds rather than minutes.
- **Live Agent Traces**: Built-in Server-Sent Events (SSE) streaming architecture dynamically pushes intermediate agent logs (traces) to the sleek React frontend in real-time as experts finish their individual evaluations.
- **FastAPI Backend**: Robust asynchronous event streaming and metadata management natively integrated with the Google ADK `DatabaseSessionService`.

## 🛠️ Technology Stack

- **Backend Platform:** Python 3.11+, FastAPI, Uvicorn
- **AI / Agentic Logic:** Google Agent Development Kit (`google-adk`), Google Gemini Pro (`google-genai`)
- **Frontend App:** Next.js (App Router), React 18, Framer Motion (fluid animations)

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js v18+ 

### 1. Environment Configuration
Create a `.env` file in the root directory (where `api.py` lives). The application supports both standard Gemini API Keys and Enterprise Google Cloud (Vertex AI) authentication.

**Option A: Standard Gemini API Key**
```env
GOOGLE_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_authorization_token_for_fast_fetching
```

**Option B: Vertex AI (Google Cloud Project)**
Ensure you have authenticated your local terminal using `gcloud auth application-default login` first.
```env
# Omit GOOGLE_API_KEY entirely
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
GITHUB_TOKEN=your_github_authorization_token_for_fast_fetching
```

### 2. Backend Setup
The backend runs the FastAPI SSE server and orchestrates the ADK swarm in memory.
```bash
# Navigate to project root
cd code_reviewer

# Activate your virtual environment and install dependencies
pip install -r requirements.txt # (or use uv)

# Start the FastApi Server
uvicorn api:app --port 8000 --reload
```
*(Note: Ensure it starts on port 8000. Your frontend heavily relies on proxying to `http://localhost:8000`!)*

### 3. Frontend Setup
The frontend hosts the sleek interactive chat UI and historic session management layout.
```bash
# Open a new terminal and navigate to the frontend directory
cd code_reviewer/frontend

# Install node dependencies
npm install

# Start the Next.js development server
npm run dev
```

### 4. Start Reviewing
Navigate to [http://localhost:3000](http://localhost:3000). You can paste a public repository URL, upload local source files in a `.zip`, or paste raw code snippets directly into the UI! Wait for the agents to analyze and view your comprehensive code review report.

## ⚙️ How it Works under the hood

1. **Submission**: Code is submitted to `/api/review/...`. If it's a GitHub repo, the backend securely overrides the LLM fetching protocol with a high-speed REST zip download, writing to a temp directory.
2. **Orchestration**: The root agent spins up a `ParallelAgent` fleet. The massive codebase text is distributed to all 4 review experts simultaneously, who process the context in completely asynchronous, non-blocking execution streams.
3. **Live Streaming**: The backend's `_sse_stream` function cleanly parses agent tool calls. As each intermediate expert generates their final response, the Python API intercepts it and emits an `agent_log` JSON event, rendering beautifully in the UI traces.
4. **Synthesis**: After all experts finish reporting in, the main `synthesis_agent` kicks in, assembling a brilliantly formatted final report that is streamlined directly to the user's screen instance via standard `delta` tokens.
