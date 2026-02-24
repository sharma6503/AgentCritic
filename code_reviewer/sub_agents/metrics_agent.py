"""
Metrics Extractor Agent

Parses the synthesis_result markdown report and extracts structured JSON
with issue counts by severity and category. Used to power the Analysis Card
in the Next.js frontend.

Uses gemini-2.0-flash (fastest model) — this is a simple extraction task.
"""

from google.adk import Agent
from ..config import Config
from ..prompts import METRICS_PROMPT
import json

_cfg = Config()

async def generate_metrics_chart_callback(callback_context):
    """Intercept the JSON output, plot a chart, and save it to state as base64."""
    metrics_json_str = callback_context.state.get("review_metrics")
    if not metrics_json_str:
        return

    try:
        # 1. Parse JSON
        raw = metrics_json_str.strip()
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("```")).strip()
        metrics = json.loads(raw)
        
        # 2. Extract Data
        categories = metrics.get("category", {})
        
        if not categories:
            return
            
        labels = list(categories.keys())
        counts = list(categories.values())
        
        # 3. Plot with Matplotlib/Seaborn
        import matplotlib.pyplot as plt
        import seaborn as sns
        import io
        import base64
        
        # Use seaborn style for premium look
        sns.set_theme(style="whitegrid", palette="muted")
        
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x=labels, y=counts, ax=ax, color="#6366f1")
        
        ax.set_title("Findings by Category", fontsize=14, pad=15)
        ax.set_ylabel("Number of Findings", fontsize=12)
        ax.set_xlabel("Review Domain", fontsize=12)
        
        # Add value labels on top of bars
        for i, v in enumerate(counts):
            ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
            
        plt.tight_layout()
        
        # 4. Save to Base64 memory buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, transparent=True)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        # 5. Save to ADK state for HTML Agent
        callback_context.state["metrics_chart_b64"] = img_b64
        
        # 6. Save as ADK Artifact (optional hard copy)
        from google.genai import types
        artifact = types.Part(inline_data=types.Blob(data=buf.getvalue(), mime_type="image/png"))
        await callback_context.save_artifact(filename="metrics_visualization.png", artifact=artifact)
        
    except Exception as e:
        import logging
        logging.error(f"Failed to generate metrics chart: {e}")

metrics_agent = Agent(
    name="metrics_agent",
    model=_cfg.agent_settings.expert_model,  # gemini-2.0-flash — fast
    description=(
        "Extracts structured metrics JSON from the synthesis_result markdown report. "
        "Outputs issue counts by severity and category for frontend visualisation."
    ),
    instruction=METRICS_PROMPT,
    output_key="review_metrics",
    after_agent_callback=generate_metrics_chart_callback,
    generate_content_config=_cfg.safety_config,
)
