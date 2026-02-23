import zipfile
import tempfile
import time
from pathlib import Path

# Create a dummy zip file
tmp_zip_path = Path(tempfile.gettempdir()) / "test_dummy.zip"
with zipfile.ZipFile(tmp_zip_path, "w") as zf:
    zf.writestr("test1.py", b"print('hello world 1')\n" * 1000)
    zf.writestr("test2.py", b"print('hello world 2')\n" * 1000)
    zf.writestr("test3.txt", b"print('hello world 3')\n" * 1000)
    zf.writestr("node_modules/test.js", b"console.log('skip me')")
    # Zip bomb simulation - 1 MB of zeros
    zf.writestr("huge_file.py", b"0" * 1_000_000)

print(f"Created ZIP: {tmp_zip_path}")

from code_reviewer.tools.file_tool import parse_uploaded_files

t0 = time.time()
result = parse_uploaded_files([str(tmp_zip_path)])
t1 = time.time()

print(f"Time Taken: {t1 - t0:.4f}s")
print(f"Status: {result.get('status')}")
print(f"Summary: {result.get('summary')}")
print(f"File Count: {result.get('file_count')}")
print(f"Skipped: {result.get('skipped')}")

if "huge_file.py: too large" in result.get('skipped', []):
    print("SUCCESS: Zip bomb mitigation blocked huge_file.py correctly")

tmp_zip_path.unlink()
