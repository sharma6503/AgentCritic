"""
FastAPI Backend for ADK Code Reviewer - SSE Streaming API
==========================================================

Exposes Server-Sent Events endpoints that the Next.js frontend connects to.
Runs on port 8000 (Next.js dev runs on port 3000).

Run with:
    uvicorn api:app --reload --port 8000
"""

import contextlib
import json
import os
import shutil
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

load_dotenv()

# ADK runner setup
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types
from code_reviewer.agent import root_agent

# ---------------------------------------------------------------------------
# App + Lifespan
# ---------------------------------------------------------------------------

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the session service."""
    global _session_service
    import logging as _log
    _log.basicConfig(level=_log.INFO)
    
    _log.info(f"Initializing DatabaseSessionService at {DB_PATH}")
    try:
        from google.adk.sessions import DatabaseSessionService
        _session_service = DatabaseSessionService(DB_PATH)
        yield
    finally:
        _log.info("Server shutting down. Session service cleanup...")
        _session_service = None

app = FastAPI(title="ADK Code Reviewer API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ADK Runner / Session service (shared across requests)
# ---------------------------------------------------------------------------
APP_NAME = "adk_code_reviewer"

# Persistent session storage using SQLite
# This ensures that session history is not lost when the backend reloads.
DB_FILE = Path(__file__).parent / "adk_reviewer_sessions.db"
# Use 4 slashes for absolute Windows paths in SQLAlchemy/aiosqlite
# and ensure forward slashes are used for the driver.
DB_PATH = f"sqlite+aiosqlite:///{DB_FILE.as_posix()}"

_session_service = None

def get_session_service():
    global _session_service
    if _session_service is None:
        # Fallback for manual scripts or unexpected states
        from google.adk.sessions import DatabaseSessionService
        _session_service = DatabaseSessionService(DB_PATH)
    return _session_service

def get_runner() -> Runner:
    return Runner(agent=root_agent, app_name=APP_NAME, session_service=get_session_service())

# ---------------------------------------------------------------------------
# Session metadata persistence
# This stores display names and user associations across restarts.
# ---------------------------------------------------------------------------
META_FILE = Path(__file__).parent / "reviewer_session_metadata.json"
_session_meta: dict[str, dict] = {}   # session_id -> {user_id, name, created_at, updated_at, preview}
_user_sessions: dict[str, list] = {}  # user_id   -> [session_id, ...] ordered newest-first


def _save_meta():
    try:
        with open(META_FILE, "w") as f:
            json.dump({"meta": _session_meta, "user_sessions": _user_sessions}, f)
    except Exception:
        pass


def _load_meta():
    global _session_meta, _user_sessions
    if META_FILE.exists():
        try:
            with open(META_FILE, "r") as f:
                data = json.load(f)
                _session_meta = data.get("meta", {})
                _user_sessions = data.get("user_sessions", {})
        except Exception:
            pass


_load_meta()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _register_session(user_id: str, session_id: str, name: str | None = None) -> dict:
    """Record session metadata and associate it with a user."""
    # Ensure user exists in metadata
    if user_id not in _user_sessions:
        _user_sessions[user_id] = []
    
    # Avoid duplicate registration
    if session_id in _session_meta:
        return _session_meta[session_id]

    meta = {
        "id":         session_id,
        "user_id":    user_id,
        "name":       name or f"Review {len(_user_sessions[user_id]) + 1}",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "preview":    "New review session",
    }
    _session_meta[session_id] = meta
    _user_sessions[user_id].insert(0, session_id)
    _save_meta()
    return meta


async def _ensure_session(session_id: str, user_id: str = "default") -> str:
    """Create ADK session if it doesn't exist yet. Returns session_id."""
    try:
        await get_session_service().create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        # Register metadata only on fresh creation
        if session_id not in _session_meta:
            _register_session(user_id, session_id)
    except Exception as e:
        # Check if it was "already exists" or a real error
        error_msg = str(e).lower()
        if "already exists" in error_msg or "unique constraint" in error_msg:
            pass
        else:
            import logging
            logging.error(f"Failed to ensure session {session_id}: {e}", exc_info=True)
            # Re-raise so the user sees a 500 instead of a broken stream later
            raise e
    return session_id


async def _sse_stream(message: str, session_id: str, user_id: str = "default"):
    """
    Core SSE generator - yields newline-delimited JSON events.
    Event types: delta, progress, metrics, error, done
    """
    agent_labels = {
        "ingestion_agent":          "📥 Ingesting codebase…",
        "adk_architecture_expert":  "🏗️ Reviewing ADK architecture…",
        "code_quality_expert":      "🧹 Reviewing code quality…",
        "security_expert":          "🔒 Reviewing security & deployment…",
        "code_validator_agent":     "🧪 Running code validation…",
        "synthesis_agent":          "📝 Synthesising report…",
        "metrics_agent":            "📊 Computing analysis metrics…",
        "critic_agent":             "🔍 Fact-checking report…",
        "reviser_agent":            "✏️ Applying revisions…",
        "html_agent":               "📄 Generating HTML report…",
    }
    seen_agents: set[str] = set()
    agent_buffers: dict[str, str] = {}

    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    try:
        import logging as _syslog
        _syslog.info(f"SSE: Starting stream for {session_id}")
        
        # Immediate feedback to the UI
        yield f"data: {json.dumps({'type': 'progress', 'message': '🚀 Connected. Starting analysis agents…'})}\n\n"
        
        async for event in get_runner().run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            author = getattr(event, "author", None)
            is_final = event.is_final_response()
            
            # _syslog.debug(f"SSE: Event from {author}, final={is_final}")

            # Emit agent progress label on first event per agent
            if author and author in agent_labels and author not in seen_agents:
                _syslog.info(f"SSE: Agent detected: {author}")
                if not is_final:
                    seen_agents.add(author)
                    yield f"data: {json.dumps({'type': 'progress', 'message': agent_labels[author]})}\n\n"
            
            # DEBUG: Log state keys when an agent finishes
            if author and is_final:
                try:
                    session = await get_session_service().get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
                    if session:
                        # Handle both dict (InMemory) and ContextState (Database)
                        keys = list(session.state.keys()) if isinstance(session.state, dict) else list(session.state.to_dict().keys())
                        _syslog.info(f"SSE: Agent COMPLETED: {author}. State keys now: {keys}")
                except Exception as e:
                    _syslog.error(f"SSE: Debug logging state keys failed: {e}")

            # Check if this author should stream as text directly to the UI
            stream_as_text = author in (None, "root_agent", "synthesis_agent", "reviser_agent")

            # Accumulate buffer for intermediate/metrics agents (including thoughts)
            if not stream_as_text and author and event.content and hasattr(event.content, 'parts') and event.content.parts:
                if author not in agent_buffers:
                    agent_buffers[author] = ""
                
                chunk_text = ""
                for part in event.content.parts:
                    # Capture regular text (or plan text if thought flag is set)
                    if hasattr(part, 'text') and part.text:
                        # If the part is marked as a thought, it's likely a plan/reasoning
                        if getattr(part, 'thought', False):
                            chunk_text += f"\n> [!TIP]\n> **Agent Plan:** {part.text}\n\n"
                        else:
                            chunk_text += part.text
                    
                    # Capture tool calls briefly as indicators
                    if hasattr(part, 'function_call') and part.function_call:
                        chunk_text += f"\n*Calling tool: `{part.function_call.name}`...*\n"
                
                if chunk_text:
                    agent_buffers[author] += chunk_text
                    
                    # For non-metrics agents, emit the log chunk in real-time
                    if author != "metrics_agent" and author not in ("review_pipeline", "review_fleet", "reporting_fleet"):
                        yield f"data: {json.dumps({'type': 'agent_log', 'data': {'author': author, 'text': agent_buffers[author]}})}\n\n"

            # When an intermediate/metrics agent completes, parse and emit its specific event
            if not stream_as_text and author and is_final:
                _syslog.info(f"SSE: Agent completed: {author}")
                raw = agent_buffers.get(author, "").strip()
                
                if author == "metrics_agent":
                    # Parse JSON and emit metrics event
                    if raw.startswith("```"):
                        raw = "\n".join(
                            l for l in raw.splitlines()
                            if not l.strip().startswith("```")
                        ).strip()
                    try:
                        metrics = json.loads(raw)
                        if session_id in _session_meta:
                            _session_meta[session_id]["metrics"] = metrics
                            _session_meta[session_id]["updated_at"] = _now_iso()
                            _save_meta()
                        yield f"data: {json.dumps({'type': 'metrics', 'data': metrics})}\n\n"
                    except json.JSONDecodeError:
                        pass
                
                elif author == "html_agent":
                    # Clean up markdown fences if the LLM output them despite instructions
                    if raw.startswith("```html"):
                        raw = raw[7:]
                    if raw.endswith("```"):
                        raw = raw[:-3]
                    raw = raw.strip()
                    yield f"data: {json.dumps({'type': 'html_report', 'data': raw})}\n\n"
                    
                continue  # don't stream anything else for this agent's completion

            # Stream text deltas (only for user, synthesis_agent, reviser_agent, root_agent)
            if stream_as_text and event.content and hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        yield f"data: {json.dumps({'type': 'delta', 'text': part.text})}\n\n"
                    elif hasattr(part, 'thought') and part.thought:
                        # Optionally stream thoughts as well if they are from the main agents
                        yield f"data: {json.dumps({'type': 'delta', 'text': f'\\n> [!NOTE]\\n> **Thinking:** {part.thought}\\n\\n'})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except* Exception as eg:
        # Unwrap Python 3.11+ ExceptionGroup (raised by asyncio.TaskGroup)
        import logging as _log
        inner_msgs = '; '.join(str(exc) for exc in eg.exceptions)
        _log.getLogger(__name__).error('SSE TaskGroup error(s): %s', inner_msgs, exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': f'❌ Agent error: {inner_msgs}'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

class UrlRequest(BaseModel):
    url: str
    session_id: str | None = None
    user_id: str = "default"


class PasteRequest(BaseModel):
    code: str
    session_id: str | None = None
    user_id: str = "default"


class RenameRequest(BaseModel):
    name: str


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "adk_code_reviewer"}


# ---------------------------------------------------------------------------
# Session Management Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/users")
async def list_users():
    """Return all users who have at least one session from DB."""
    try:
        response = await get_session_service().list_sessions(app_name=APP_NAME)
        user_counts = {}
        for s in response.sessions:
            user_counts[s.user_id] = user_counts.get(s.user_id, 0) + 1
            
        users = [{"user_id": uid, "session_count": count} for uid, count in user_counts.items()]
        return {"users": users}
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Failed to fetch users from DB: {e}", exc_info=True)
        # Fallback
        users = [
            {"user_id": uid, "session_count": len(sids)}
            for uid, sids in _user_sessions.items()
            if sids
        ]
        return {"users": users}


@app.get("/api/users/{user_id}/sessions")
async def list_sessions(user_id: str):
    """List all sessions for a given user from the database."""
    try:
        response = await get_session_service().list_sessions(app_name=APP_NAME, user_id=user_id)
        sessions_out = []
        for s in response.sessions:
            meta = _session_meta.get(s.id, {})
            dt = s.last_update_time
            dt_str = None
            if dt:
                # dt can be a datetime object or a float (timestamp)
                if isinstance(dt, (int, float)):
                    from datetime import datetime, timezone
                    dt_str = datetime.fromtimestamp(dt, tz=timezone.utc).isoformat()
                elif hasattr(dt, 'isoformat'): # Check if it's a datetime object
                    dt_str = dt.isoformat()
            
            if not dt_str: # Fallback if dt was None or couldn't be formatted
                dt_str = meta.get("updated_at", _now_iso())
                
            sessions_out.append({
                "id": s.id,
                "name": meta.get("name", f"Session {s.id[:8]}"),
                "created_at": meta.get("created_at", dt_str),
                "updated_at": dt_str,
                "preview": meta.get("preview", "Review Session")
            })
            
        # Sort newest first based on updated_at
        sessions_out.sort(key=lambda x: x["updated_at"], reverse=True)
        return {"user_id": user_id, "sessions": sessions_out}
    except Exception as e:
        import logging as _log
        _log.getLogger(__name__).error(f"Failed to fetch sessions from DB for {user_id}: {e}", exc_info=True)
        # Fallback
        sids = _user_sessions.get(user_id, [])
        sessions = [_session_meta[sid] for sid in sids if sid in _session_meta]
        return {"user_id": user_id, "sessions": sessions}


@app.post("/api/users/{user_id}/sessions")
async def create_session(user_id: str):
    """Create a new session for a user and register it with ADK."""
    sid = str(uuid.uuid4())
    await _ensure_session(sid, user_id)
    return _session_meta[sid]


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Remove a session from local metadata (ADK in-memory state is also dropped)."""
    meta = _session_meta.pop(session_id, None)
    if meta:
        uid = meta["user_id"]
        if session_id in _user_sessions.get(uid, []):
            _user_sessions[uid].remove(session_id)
        _save_meta()
    return {"status": "deleted", "session_id": session_id}


@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Retrieve the conversation history for a session from persistence."""
    if session_id not in _session_meta:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Fetch the session object from ADK's persistent service
        # DatabaseSessionService.get_session is async
        user_id = _session_meta[session_id].get("user_id", "default")
        session = await get_session_service().get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        if not session or not hasattr(session, 'events') or not session.events:
            return {
                "session_id": session_id, 
                "messages": [], 
                "meta": _session_meta.get(session_id, {})
            }

        # Extract messages into a format the frontend can easily digest
        messages = []
        for event in session.events:
            # Safely extract text parts
            text = ""
            if event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if hasattr(p, 'text') and p.text)
            
            author = getattr(event, "author", None)
            
            # Events in ADK might be ToolCall, ToolResponse, SystemMessage, AgentMessage, etc. 
            # We want to try finding a role, but default to author or 'model' if it's agent output
            role = getattr(event, "role", "model" if author else "user")

            if text or author:
                messages.append({
                    "role": role,
                    "text": text,
                    "author": author
                })

        # Debug log for history retrieval
        import logging as _log
        _log.getLogger(__name__).info(f"Retrieved {len(messages)} messages for session {session_id}")

        return {
            "session_id": session_id,
            "messages": messages,
            "meta": _session_meta.get(session_id, {})
        }
    except Exception as e:
        # Fail gracefully if session retrieval fails
        return {"session_id": session_id, "messages": [], "error": str(e)}


@app.patch("/api/sessions/{session_id}")
async def rename_session(session_id: str, body: RenameRequest):
    """Rename a session."""
    meta = _session_meta.get(session_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Session not found")
    meta["name"] = body.name.strip() or meta["name"]
    meta["updated_at"] = _now_iso()
    _save_meta()
    return meta


@app.post("/api/review/url")
async def review_url(body: UrlRequest):
    """Stream a GitHub / Bitbucket URL review."""
    if not body.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    sid = body.session_id or str(uuid.uuid4())
    await _ensure_session(sid, body.user_id)

    # Update session preview
    url_str = body.url.strip()
    if sid in _session_meta:
        _session_meta[sid]["preview"] = f"URL: {url_str[:60]}"
        _session_meta[sid]["updated_at"] = _now_iso()

    # Standard slow fallback message
    message = f"Please review this repository: {url_str}"
    tmp_path_for_cleanup = None

    # FAST PATH: Directly download GitHub repos as ZIPs to bypass slow LLM fetching
    import re
    gh_match = re.match(r"(?:https?://)?github\.com/([^/]+)/([^/]+)/?", url_str)
    
    if gh_match:
        owner = gh_match.group(1)
        repo = gh_match.group(2).replace(".git", "")
        
        try:
            # Use a short extraction path to avoid Windows MAX_PATH (WinError 206)
            extract_base = Path.home() / ".adk_gh_tmp"
            extract_base.mkdir(parents=True, exist_ok=True)
            tmp_dir = Path(tempfile.mkdtemp(dir=extract_base, prefix="gh_"))
            tmp_path_for_cleanup = tmp_dir
            
            zip_path = tmp_dir / "repo.zip"
            extract_dir = tmp_dir / "extracted"
            
            # Download the zipball
            import requests
            headers = {"Accept": "application/vnd.github+json", "User-Agent": "ADK-Code-Reviewer"}
            gh_token = os.environ.get("GITHUB_TOKEN", "")
            if gh_token:
                headers["Authorization"] = f"Bearer {gh_token}"
                
            resp = requests.get(f"https://api.github.com/repos/{owner}/{repo}/zipball", headers=headers, stream=True)
            resp.raise_for_status()
            
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # No extraction needed: passed directly to in-memory streaming ingestion
            target_path = str(zip_path).replace('\\', '/')
            message = (
                f"Please review the uploaded codebase from {url_str}.\n"
                f"Call parse_uploaded_files with file_paths=['{target_path}'] to read all source files, then perform a full code review."
            )
        except Exception as e:
            import logging
            logging.error(f"GitHub ZIP fast-path failed: {e}")
            if tmp_path_for_cleanup:
                shutil.rmtree(tmp_path_for_cleanup, ignore_errors=True)
                tmp_path_for_cleanup = None

    async def cleanup_after():
        try:
            async for chunk in _sse_stream(message, sid, body.user_id):
                yield chunk
        finally:
            if tmp_path_for_cleanup:
                shutil.rmtree(tmp_path_for_cleanup, ignore_errors=True)

    return StreamingResponse(
        cleanup_after(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Session-Id": sid,
        },
    )


@app.post("/api/review/zip")
async def review_zip(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
    user_id: str = Form(default="default"),
):
    """
    Stream a file review - accepts ZIP archives OR individual code files
    (.py, .js, .ts, .go, .java, etc.).
    """
    tmp_dir = tempfile.mkdtemp(prefix="adk_review_")
    filename = file.filename or "upload"
    is_zip = filename.lower().endswith(".zip")

    try:
        contents = await file.read()
        file_path = Path(tmp_dir) / filename
        file_path.write_bytes(contents)

        sid = session_id.strip() or str(uuid.uuid4())
        await _ensure_session(sid, user_id)

        if is_zip:
            # No extraction needed: pass ZIP directly to in-memory streaming agent
            target_path = str(file_path).replace('\\', '/')
            message = (
                f"Please review the uploaded codebase.\n"
                f"Call parse_uploaded_files with file_paths=['{target_path}'] to read all source files, then perform a full code review."
            )
        else:
            # Individual code file - pass file path directly
            target_path = str(file_path)
            message = (
                f"Please review the uploaded file: {filename}\n"
                f"Call parse_uploaded_files with file_paths=['{target_path}'] to read the file content, then perform a full code review."
            )

        async def cleanup_after():
            async for chunk in _sse_stream(message, sid, user_id):
                yield chunk
            shutil.rmtree(tmp_dir, ignore_errors=True)

        return StreamingResponse(
            cleanup_after(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Session-Id": sid,
            },
        )
    except zipfile.BadZipFile:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Invalid ZIP file - please upload a valid .zip archive or a code file.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        shutil.rmtree(tmp_dir, ignore_errors=True)
        # Return exact error message for easier debugging
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")


@app.post("/api/review/paste")
async def review_paste(body: PasteRequest):
    """Stream a pasted code review."""
    if not body.code.strip():
        raise HTTPException(status_code=400, detail="Code is required")

    sid = body.session_id or str(uuid.uuid4())
    await _ensure_session(sid, body.user_id)

    message = f"Please review the following code:\n\n```\n{body.code.strip()}\n```"
    return StreamingResponse(
        _sse_stream(message, sid, body.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Session-Id": sid,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8007)
