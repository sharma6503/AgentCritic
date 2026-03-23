# ADK 1.x Architectural Patterns

This document outlines the core architectural patterns and best practices for ADK 1.x (pre-Skill system).

## Multi-Agent Composition
- **AgentTool**: The primary way to compose agents. A high-level agent can use another agent as a tool.
- **SequentialAgent / ParallelAgent / LoopAgent**: Used for deterministic workflow control.
- **Root Agent**: Every ADK App has a single root agent that orchestrates the overall task.

## State Management
- **Context State**: Agents share a common `state` dictionary within a session. This is for short-term working memory.
- **Persistent State**: Use `DatabaseSessionService` for state that must survive restarts.
- **Session ID**: Uniquely identifies a single conversation.

## Tool Integration
- **FunctionTool**: For exposing standard Python functions to agents.
- **MCP Tool**: For integrating with Model Context Protocol servers.
- **Lifecycle Tools**: Tools like `read_codebase` or `parse_uploaded_files` that handle ingestion.

## Best Practices
1. **Clear Descriptions**: Agent names and descriptions must be clear for the LLM to choose the right sub-agent.
2. **Modular Tools**: Keep tools focused on a single responsibility.
3. **Structured Output**: Use `output_key` to ensure agents write their final result to a specific state location.
4. **Resilience**: Use `ReflectAndRetryToolPlugin` to handle transient model errors.
