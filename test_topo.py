import ast
from collections import defaultdict, deque
import os

raw = """
--- main.py ---
from app.api import router
from app.config import config
print("main")

--- app/api.py ---
from .models import User
from app.services import user_service
print("api")

--- app/models.py ---
from .base import BaseModel
class User(BaseModel): pass

--- app/base.py ---
class BaseModel: pass

--- app/services.py ---
from .models import User
from parent_module import Something # external/missing
import os
print("services")

--- app/config.py ---
print("config")

--- app/cycle_a.py ---
from app.cycle_b import B
class A: pass

--- app/cycle_b.py ---
from app.cycle_a import A
class B: pass
"""

logic_files = {}

lines = raw.splitlines()
i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith("--- ") and line.endswith(" ---"):
        fname = line.strip("- ")
        ext = os.path.splitext(fname)[1].lower()
        content_buf = []
        i += 1
        while i < len(lines) and not (lines[i].startswith("--- ") and lines[i].endswith(" ---")):
            content_buf.append(lines[i])
            i += 1
        
        file_block = f"\n--- {fname} ---\n" + "\n".join(content_buf)
        logic_files[fname] = file_block
        continue
    i += 1

graph = defaultdict(list)
in_degree = defaultdict(int)
py_files = {f: c for f, c in logic_files.items() if f.endswith('.py')}

# --- NEW TOPO ALGO HERE ---
# 1. Map files to module namespaces (e.g., 'app/api.py' -> 'app.api')
module_to_file = {}
for fname in py_files:
    # Convert 'app/api.py' to 'app.api'
    mod_name = fname.replace("\\", "/").replace(".py", "").replace("/", ".")
    module_to_file[mod_name] = fname
    # Also store the __init__.py package name if applicable
    if mod_name.endswith(".__init__"):
        module_to_file[mod_name[:-9]] = fname

# Helper to resolve relative imports
def resolve_import(module: str, level: int, current_fname: str) -> str | None:
    if level == 0:
        return module_to_file.get(module)
    
    # Relative import processing
    parts = current_fname.replace("\\", "/").split("/")
    # Remove filename (e.g. api.py)
    parts.pop()
    
    # Go up directories based on level
    for _ in range(level - 1):
        if parts:
            parts.pop()
        else:
            return None # Went past root
            
    base_mod = ".".join(parts)
    if module:
        full_mod = f"{base_mod}.{module}" if base_mod else module
    else:
        full_mod = base_mod
        
    return module_to_file.get(full_mod)

for fname, block in py_files.items():
    in_degree[fname] += 0 # Ensure node exists in degree map
    source = block.split(f"--- {fname} ---")[1] if f"--- {fname} ---" in block else block
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dep_fname = resolve_import(alias.name.split('.')[0], 0, fname)
                    if dep_fname and dep_fname != fname:
                        grapph_list = graph[dep_fname]
                        if fname not in grapph_list:
                            grapph_list.append(fname)
                            in_degree[fname] += 1
            elif isinstance(node, ast.ImportFrom):
                level = node.level
                module = node.module or ""
                # We check the module level
                dep_fname = resolve_import(module, level, fname)
                
                # Further check if it's actually importing a submodule directly from within the module (like from app import api)
                if not dep_fname and node.names:
                   for alias in node.names:
                       sub_mod = f"{module}.{alias.name}" if module else alias.name
                       dep_fname_sub = resolve_import(sub_mod, level, fname)
                       if dep_fname_sub and dep_fname_sub != fname:
                            grapph_list = graph[dep_fname_sub]
                            if fname not in grapph_list:
                                grapph_list.append(fname)
                                in_degree[fname] += 1
                                
                if dep_fname and dep_fname != fname:
                    grapph_list = graph[dep_fname]
                    if fname not in grapph_list:
                        grapph_list.append(fname)
                        in_degree[fname] += 1
    except SyntaxError:
        pass # Ignore unparseable code snippets

# 3. Kahn's Algorithm
sorted_py_files = []
queue = deque([f for f in py_files if in_degree[f] == 0])

while queue:
    curr = queue.popleft()
    sorted_py_files.append(curr)
    for dependent in graph[curr]:
        in_degree[dependent] -= 1
        if in_degree[dependent] == 0:
            queue.append(dependent)

# Cycle Resolution
# If there are nodes left with in_degree > 0, they are in a cycle.
cyclic_files = [f for f in py_files if in_degree[f] > 0]
if cyclic_files:
    print(f"Cycles detected in: {cyclic_files}")
    # Iteratively break cycles by artificially setting the lowest in-degree node's dependencies to 0
    while cyclic_files:
        # Find the node with the lowest in-degree to break the cycle with minimal disruption
        target = min(cyclic_files, key=lambda f: in_degree[f])
        in_degree[target] = 0
        queue.append(target)
        
        while queue:
            curr = queue.popleft()
            sorted_py_files.append(curr)
            for dependent in graph[curr]:
                if in_degree[dependent] > 0:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        cyclic_files = [f for f in py_files if in_degree[f] > 0]

print("--- SORTED OUTPUT ---")
for f in sorted_py_files:
    print(f)
