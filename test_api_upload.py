import requests
import json
import zipfile
import tempfile
from pathlib import Path

# Create a dummy zip file
tmp_zip_path = Path(tempfile.gettempdir()) / "test_api_dummy.zip"
with zipfile.ZipFile(tmp_zip_path, "w") as zf:
    zf.writestr("test1.py", b"import os\nprint('hello world 1')\n")
    zf.writestr("test2.py", b"import test1\nprint('hello world 2')\n")

print(f"Created ZIP: {tmp_zip_path}")
print("Sending request to http://localhost:8001/api/review/zip...")

try:
    with open(tmp_zip_path, "rb") as f:
        files = {"file": ("test_api_dummy.zip", f, "application/zip")}
        data = {"user_id": "test_user"}
        resp = requests.post("http://localhost:8001/api/review/zip", files=files, data=data, stream=True)
        
    for line in resp.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            print(line_str)
            if "❌ Agent error" in line_str:
                print("FOUND ERROR!")
                break
except Exception as e:
    print(f"Failed to call API: {e}")
finally:
    tmp_zip_path.unlink()
