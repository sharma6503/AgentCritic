# 🚀 ADK 2.0 Best Practices

Follow these guidelines to build robust and scalable multi-agent systems.

## 1. Graph-Based Orchestration
**Best Practice:** Use `Workflow` (or `SequentialAgent`/`ParallelAgent`) to define clear execution paths.
**Avoid:** Rigid, deeply nested `if/else` logic for agent control flow.

## 2. Stateless Sub-Agents
**Best Practice:** Agents should communicate via a shared `state` object and define an `output_key`.
**Avoid:** Agents directly mutating global variables or each other's internal state.

## 3. Tool Modularity
**Best Practice:** Encapsulate tool groups into `SkillToolset` or separate modules. 
**Avoid:** Attaching dozens of loose tools to a single agent.

## 4. Callback Placement
**Best Practice:** Use `before_agent_callback` for pre-processing (state injection, input validation) and `after_agent_callback` for post-processing/cleanup.

## 5. Explicit Constraints
**Best Practice:** Use `global_instruction` on the root agent for brand-wide persona and `instruction` for task-specific guidance on sub-agents.

## 6. Resource Management
**Best Practice:** Use `ContextCacheConfig` to manage long-running sessions and reduce token usage.
