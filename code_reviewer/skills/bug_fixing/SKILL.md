---
name: bug-fixing
description: A skill focused on providing high-impact code refactors and specific bug fixes based on review findings.
---

# 🛠️ Bug Fixing Skill

Use this skill when the user (or another agent) identifies a specific code quality issue, bug, or maintainability concern that requires a concrete fix.

## Instructions

1. **Analyze the Finding:** Identify the root cause of the issue (e.g., deep nesting, lack of error handling, poor naming).
2. **Propose a Fix:** Provide a specific code snippet that resolves the issue while adhering to the 'Clean Code' principles.
3. **Show Before/After:** When possible, present the "Before" (original) and "After" (fixed) code blocks for clarity.
4. **Context Preservation:** Ensure the fix doesn't break surrounding logic or change intended functionality.

## Workflow: The 'Fix-It' Loop
- **Stage 1 (Diagnosis):** Explain WHY the current code is suboptimal.
- **Stage 2 (Transformation):** Apply refactoring patterns (e.g., Extract Method, Replace Temp with Query).
- **Stage 3 (Validation):** Briefly explain why the new version is better (performance, readability, or reliability).

## Resources
Refer to `references/refactoring_patterns.md` for specific implementation guides.
