---
name: architecture-validation
description: A specialized skill for validating codebase architecture against ADK 2.0 best practices and modular design principles.
---

# 🏗️ Architecture Validation Skill

Use this skill when performing a structural audit of a codebase to ensure it follows modern architectural patterns, specifically Google ADK 2.0 standards.

## Instructions

1. **Structural Audit:** Evaluate the directory structure for logical separation of concerns (e.g., `agents`, `tools`, `utils`, `config`).
2. **ADK 2.0 Compliance:**
   - Verify usage of `Workflow` or `ParallelAgent`/`SequentialAgent` for orchestration.
   - Check if sub-agents are properly modularized.
   - Validate state management patterns (using `output_key` and state-based communication).
3. **Layering Check:** Ensure no circular dependencies and that clear boundaries exist between layers (e.g., UI, Business Logic, Data).
4. **Consistency Audit:** Check for consistent naming, usage of shared utils, and adherence to project-wide config patterns.

## Resources
Refer to the following resources for detailed architectural guidance:
- [ADK 2.0 Best Practices](references/adk_2.0_best_practices.md)
- [ADK 1.x Architectural Patterns](references/adk_1_x_patterns.md)
