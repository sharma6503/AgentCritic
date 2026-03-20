"""
Metrics Extractor Agent

Parses the review results and extracts structured JSON
with issue counts and multi-dimensional health scores.
"""

from google.adk import Agent
from ..config import Config
from ..prompts import METRICS_PROMPT
import json
import re
import logging
import io
import base64

logger = logging.getLogger(__name__)
_cfg = Config()

def _extract_metrics_json(raw_str: str) -> dict:
    """
    Sanitizes and parses a JSON string from the LLM, handling markdown fences.
    """
    raw = raw_str.strip()
    raw = re.sub(r'^```json\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'^```\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\s*```$', '', raw)
    
    match = re.search(r'(\{.*\})', raw, re.DOTALL)
    if match:
        raw = match.group(1)
        
    return json.loads(raw)

def _generate_metrics_plot(metrics: dict) -> str:
    """
    Generates a dual-pane bar chart and returns it as a Base64 encoded PNG string.
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        plt.switch_backend('Agg')
    except ImportError:
        logger.warning("Visualization libraries (matplotlib/seaborn) not found. Skipping plot generation.")
        return ""

    categories = metrics.get("category", {})
    scores = metrics.get("scores", {})
    
    sns.set_theme(style="whitegrid", palette="muted")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # Left: Findings by Category
    labels = list(categories.keys())
    counts = list(categories.values())
    if labels:
        sns.barplot(x=labels, y=counts, ax=ax1, color="#6366f1")
        ax1.set_title("Findings count", fontsize=10, fontweight='bold')
    
    # Right: Health Scores
    score_labels = ["Security", "Quality", "Architecture"]
    score_vals = [scores.get("security", 0), scores.get("quality", 0), scores.get("architecture", 0)]
    sns.barplot(x=score_labels, y=score_vals, ax=ax2, palette=["#ef4444", "#f59e0b", "#10b981"])
    ax2.set_ylim(0, 100)
    ax2.set_title("Health %", fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return img_b64

async def generate_metrics_chart_callback(callback_context):
    """Intercept the JSON output, plot a dual-pane chart, and save to state."""
    metrics_json_str = callback_context.state.get("review_metrics")
    if not metrics_json_str:
        return

    try:
        # 1. Parse JSON using helper
        metrics = _extract_metrics_json(metrics_json_str)
        
        # 2. Generate Plot using helper
        img_b64 = _generate_metrics_plot(metrics)
        
        # 3. Save to state
        callback_context.state["metrics_chart_b64"] = img_b64
        callback_context.state["review_metrics"] = metrics
        
    except Exception as e:
        logger.error(f"Metrics processing failed: {e}")

metrics_agent = Agent(
    name="metrics_agent",
    model=_cfg.agent_settings.expert_model,
    description="Extracts multi-dimensional health metrics from review results.",
    instruction=METRICS_PROMPT,
    output_key="review_metrics",
    after_agent_callback=generate_metrics_chart_callback,
    generate_content_config=_cfg.safety_config,
)
