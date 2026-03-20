import os
import sys
import json

# Project root is CURRENT directory
project_root = os.getcwd()
sys.path.insert(0, project_root)

print(f"Project Root: {project_root}")

try:
    from code_reviewer.sub_agents.html_agent import html_agent
    print("SUCCESS: html_agent imported.")
except Exception as e:
    print(f"ERROR: Failed to import html_agent: {e}")

template_path = os.path.join(project_root, "code_reviewer", "templates", "report_template.html")
if os.path.exists(template_path):
    print(f"SUCCESS: Template found at {template_path}")
else:
    print(f"ERROR: Template NOT found at {template_path}")

# Check reporting directory
reports_dir = os.path.join(project_root, "reports")
print(f"Reports directory: {reports_dir} (Exists: {os.path.exists(reports_dir)})")

# Test metrics parsing logic from html_agent (simulated)
dummy_metrics = {
    "scores": {
        "security": 85,
        "quality": 92,
        "architecture": 78,
        "overall": 85
    }
}

def get_score_html(val, label):
    if not isinstance(val, (int, float)):
        return f'<div class="score-pill"><span>{label}:</span> <span>--</span></div>'
    color = "#10b981" # Green
    if val < 40: color = "#ef4444" 
    elif val < 70: color = "#f97316" 
    elif val < 90: color = "#f59e0b" 
    return f'<div class="score-pill" style="border-left: 4px solid {color};"><span>{label}</span><strong>{val}%</strong></div>'

scorecard = f"""
    <div class="scorecard">
        {get_score_html(dummy_metrics['scores'].get("security"), "Security")}
        {get_score_html(dummy_metrics['scores'].get("quality"), "Quality")}
        {get_score_html(dummy_metrics['scores'].get("architecture"), "Architecture")}
        {get_score_html(dummy_metrics['scores'].get("overall"), "Overall")}
    </div>
"""
print("SUCCESS: Scorecard HTML generated successfully (Simulation).")
print(scorecard)
