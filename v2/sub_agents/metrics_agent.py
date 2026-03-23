"""
Metrics Agent - V2
"""

from google.adk import Agent
from ..prompts import METRICS_PROMPT
import json
import re
import io
import base64
import logging

logger = logging.getLogger(__name__)

# Re-using the refactored helper functions from v1 (which are already in V2 sub_agents or utils)
# I'll include them here for completeness since this is a replication.

def _extract_metrics_json(raw_str: str) -> dict:
    raw = raw_str.strip()
    raw = re.sub(r'^```json\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'^```\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\s*```$', '', raw)
    match = re.search(r'(\{.*\})', raw, re.DOTALL)
    if match: raw = match.group(1)
    return json.loads(raw)

def _generate_metrics_plot(metrics: dict) -> str:
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        plt.switch_backend('Agg')
    except ImportError:
        return ""
        
    categories = metrics.get("category", {})
    scores = metrics.get("scores", {})
    
    sns.set_theme(style="whitegrid", palette="muted")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    labels = list(categories.keys())
    counts = list(categories.values())
    if labels:
        sns.barplot(x=labels, y=counts, ax=ax1, color="#6366f1")
    
    score_labels = ["Security", "Quality", "Architecture"]
    score_vals = [scores.get("security", 0), scores.get("quality", 0), scores.get("architecture", 0)]
    sns.barplot(x=score_labels, y=score_vals, ax=ax2, palette=["#ef4444", "#f59e0b", "#10b981"])
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120)
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return img_b64

from google.adk.agents.callback_context import CallbackContext
import logging

# ... (helper functions _extract_metrics_json, _generate_metrics_plot from previous)

def process_metrics_callback(callback_context: CallbackContext):
    """
    Callback: Processes raw LLM metrics JSON and generates plot.
    """
    state = callback_context.state
    raw_str = state.get("review_metrics", "")
    if not raw_str: return
    
    try:
        metrics = _extract_metrics_json(raw_str)
        state["scores_json"] = metrics
        state["metrics_plot_b64"] = _generate_metrics_plot(metrics)
        state["overall_score"] = metrics.get("scores", {}).get("overall", 0)
    except Exception as e:
        logger.error(f"Failed to process metrics: {e}")

metrics_agent = Agent(
    name="metrics_agent",
    model="gemini-2.0-flash",
    mode="single_turn",
    instruction=METRICS_PROMPT,
    output_key="review_metrics",
    after_agent_callback=process_metrics_callback
)
