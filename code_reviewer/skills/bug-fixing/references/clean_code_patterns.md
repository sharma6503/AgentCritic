# 🧹 Clean Code Refactoring Patterns

Use these patterns to transform suboptimal code into high-quality, maintainable logic.

## 1. Guard Clauses
**Problem:** Deeply nested `if` statements (arrow code).
**Fix:** Reverse the logic and return early.

```python
# Before
def process_data(data):
    if data:
        if "user" in data:
            if data["user"].is_active:
                # ... core logic ...
                return True
    return False

# After
def process_data(data):
    if not data or "user" not in data:
        return False
    
    if not data["user"].is_active:
        return False
        
    # ... core logic ...
    return True
```

## 2. Compose Method
**Problem:** Long, complex functions doing too many things.
**Fix:** Break down into small, single-purpose helper functions.

## 3. Replace Temp with Query
**Problem:** Local variables holding results of computations used multiple times.
**Fix:** Extract the computation into a property or method.

## 4. Introduce Parameter Object
**Problem:** Functions with too many positional or keyword arguments.
**Fix:** Group related arguments into a Data Class or Pydantic model.

## 5. Explicit Over Implicit
**Problem:** Using `global` or relying on side effects.
**Fix:** Pass state explicitly and return new state.
