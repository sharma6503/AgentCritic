# Agentic Code Reviewer (v0.1.0)

A powerful, multi-agent AI code review platform built with **Google ADK (Agent Development Kit)**. This application orchestrates a swarm of specialized AI agents to analyze your codebase concurrently, providing deep insights on architecture, code quality, security, and runtime validation.

## ✨ Features

- **Multi-Agent Orchestration**: Utilizes a fleet of specialized experts organized into parallel and sequential pipelines:
  - **Ingestion Agent**: Fast-paths GitHub repositories, ZIP archives, and pasted code into memory. Now robust against binary edge-cases and large codebase truncation.
  - **ADK Architecture Expert**: Analyzes system design and architectural patterns using the **Pipeline Pattern**.
  - **Quality Expert**: Evaluates code quality and maintainability using a professional **Bug-Fixing Skill** (Generator Pattern).
  - **Security Expert**: Identifies vulnerabilities and deployment flaws using a **Security Hardening Skill** (Reviewer Pattern).
  - **Validator Expert**: Runs dynamic code validation checks in a safe sandbox.
  - **Synthesis Agent**: Compiles individual expert traces into a comprehensive, finalized Markdown report.
  - **Metrics Extractor Agent**: Extracts structured JSON health assessments and generates dual-pane visualizations (Findings vs. Health Scores).
  - **HTML Agent**: Automatically converts the synthesis report into an ultra-premium, beautifully animated HTML document.
- **Model Lifecycle Auditing**: Proactively detects deprecated Gemini models (e.g., `gemini-2.0-flash`) and provides shutdown dates with upgrade guidance.
- **Resilience & Stability**:
  - **Reflect & Retry**: Automounted plugin that retries transient tool failures across the entire pipeline.
  - **Traffic Shaping**: Semaphore-based concurrency control to prevent `429 RESOURCE_EXHAUSTED` errors.
  - **State Purge**: Automatically clears stale review data when a new codebase is submitted.
- **Background Session Independence**: Switch between past sessions seamlessly while heavy reviews run concurrently in the background without locking up the UI.
- **Context Caching & Resumability**: Leverages ADK `ContextCacheConfig` (min 15k tokens) and `ResumabilityConfig` for cost-efficient, interruptible workflows under heavy load.
- **GitHub Fast-Path Ingestion**: Bypasses slow LLM fetching by using high-speed REST zip downloads over the GitHub API.

## 🛠️ Technology Stack

- **Backend Platform:** Python 3.11+, FastAPI, Uvicorn
- **AI / Agentic Logic:** Google Agent Development Kit (`google-adk`), Google Gemini Pro (`google-genai`)
- **Data Visualization:** Matplotlib, Seaborn (for health metrics plots)
- **Frontend App:** Next.js (App Router), React 18, Framer Motion (fluid animations)

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js v18+ 

### 1. Environment Configuration
Create a `.env` file in the root directory.
```env
GOOGLE_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_authorization_token
```

### 2. Backend Setup
```bash
# Navigate to project root
pip install -r requirements.txt
uvicorn api:app --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Start Reviewing
Navigate to [http://localhost:3000](http://localhost:3000) and submit a GitHub URL or ZIP file.

## ⚙️ How it Works

1. **Submission**: Code is submitted to `/api/review/...`. New submissions trigger a structural state purge for fresh results.
2. **Review Fleet**: The `ParallelAgent` fleet runs four experts simultaneously (ADK, Quality, Security, Validator) to maximize concurrency.
3. **Reporting Fleet**: Synthesis and JSON Metrics extraction run in parallel once expert evaluations are complete.
4. **HTML Generation**: The `html_agent` translates the final report into a themed, interactive document with neo-brutalist aesthetics.
5. **Resilience**: Every tool call in the pipeline is protected by a reflection-based retry mechanism to handle transient network issues.
