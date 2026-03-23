# 🧩 Refactoring Patterns Reference

This document provides standardized patterns for fixing common code quality issues.

## 1. Extract Method
- **Problem:** A function is too long or complex.
- **Fix:** Move a logical sub-section of the code into a new, descriptively named function.
- **Benefit:** Improves readability and testability.

## 2. Replace Temp with Query
- **Problem:** A local variable is used to hold the result of an expression.
- **Fix:** Move the expression into its own function and call it instead of using the variable.
- **Benefit:** Redundancy reduction and better modularity.

## 3. Early Return (Guard Clause)
- **Problem:** Deeply nested `if-else` blocks for error handling.
- **Fix:** Check for error conditions at the start of the function and return early.
- **Benefit:** Reduces cognitive load and "arrow code" anti-patterns.
