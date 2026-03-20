import os
import sys

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

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
