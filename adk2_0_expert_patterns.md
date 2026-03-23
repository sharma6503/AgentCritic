# ADK 2.0 Expert Patterns & Architecture Guide

This guide provides an expert-level overview of the Agent Development Kit (ADK) 2.0, focusing on the new graph-based **Workflow Runtime** and the structured **Task API**. It includes real-world samples from the official ADK 2.0 alpha repository.

---

## 1. Core Architecture: Graph-Based Runtime

ADK 2.0 shifts from simple linear delegation to a **Graph-Based Runtime**. Every complex agent is essentially a `Workflow` (which inherits from `Agent`), where logic is defined as a directed graph of nodes and edges.

### Key Components
- **Nodes**: Can be an `Agent`, a simple Python `function`, a `Tool`, or even another nested `Workflow`.
- **Edges**: Defined as a list of tuples: `(from_node, to_node1, to_node2, ...)` or `(from_node, {route_name: to_node})`.
- **Events**: The primary mechanism for communication. All nodes receive a `node_input` and return an `Event`.
- **Start/End**: Sentinel nodes `START` and `END` define the entry and exit points.

---

## 2. Fundamental Workflow Patterns

### 2.1 Sequential Chaining
Nodes execute one after another in a deterministic line.
```python
edges=[("START", generate_fruit_agent, generate_benefit_agent)]
```

### 2.2 Conditional Routing (Branching)
Decision logic using `Event(route=...)`.
```python
def route_on_category(category: InputCategory):
  yield Event(route=category.category)

edges=[
    ("START", classify_input, route_on_category),
    (route_on_category, {"question": answer_q, "statement": comment_s}),
]
```

### 2.3 Iterative Looping (Self-Correction)
Routing back to a previous node or the same node for refinement.
```python
edges=[
    ("START", generate_headline, evaluate_headline, route_headline),
    (route_headline, {"unrelated": generate_headline}), # Loop back to generator
    (route_headline, {"tech-related": headline_agent}),
]
```

---

## 3. Advanced Execution Patterns

### 3.1 Dynamic Node Generation
Using `@node` decorators to programmatically orchestrate other nodes using `ctx.run_node()`. This allows for logic that isn't easily represented as static edges.

**Sample Code (`workflow_samples/dynamic_nodes`):**
```python
from google.adk.workflow import node

@node(rerun_on_resume=True)
async def orchestrate(ctx: Context, node_input: str) -> str:
  yield Event(state={"topic": node_input})

  while True:
    # Programmatically run nodes
    headline = await ctx.run_node(generate_headline)
    feedback = Feedback.model_validate(
        await ctx.run_node(evaluate_headline, node_input=headline)
    )
    if feedback.grade == "tech-related":
      yield headline
      break
```

### 3.2 Built-in Error Handling (Retries)
ADK 2.0 provides `RetryConfig` to handle transient failures (e.g., API rate limits) at the node level.

**Sample Code (`workflow_samples/retry`):**
```python
from google.adk.workflow import RetryConfig

@node(retry_config=RetryConfig(max_retries=5, initial_delay=1))
def get_weather(ctx: Context) -> str:
  if random.random() < 0.7:
    raise HTTPError(...) # Automatically retried up to 5 times
  yield "sunny"
```

### 3.3 Multi-Trigger Synchronization
A single node can be triggered by multiple predecessors, acting as a synchronization point.
```python
edges=[(
    "START",
    (make_uppercase, count_characters, reverse_string), # Three parallel nodes
    send_message, # Triggered when ANY of the above complete (depending on logic)
)]
```

---

## 4. State Management Depth

State in ADK 2.0 can be managed in three primary ways:

1.  **Direct Context Access**: Modifying `ctx.state` directly.
2.  **Explicit Events**: Returning `Event(state={"key": "value"})`.
3.  **Automatic Parameter Injection**: Nodes can declare parameters that match keys in the state, and ADK will inject them automatically.

**Sample Code (`workflow_samples/state`):**
```python
def process_initial_input(ctx, node_input: str):
  ctx.state["original_text"] = node_input # Direct Access

def update_state_via_event(node_input: str):
  yield Event(state={"uppercased": node_input.upper()}) # Via Event

def read_state_via_param(appended_text: str): # Parameter Injection
  return f"Final Result: {appended_text}!"
```

---

## 5. Human-in-the-Loop (HITL)

Pausing execution for review or feedback using `RequestInput`.

**Sample Code (`workflow_samples/request_input`):**
```python
from google.adk.events import RequestInput

def request_human_review(draft: str):
  yield RequestInput(message=f"Please review: {draft}")

def handle_review(node_input: str):
  if node_input == "approve":
    yield Event(route="approved")
  else:
    yield Event(state={"feedback": node_input}, route="revise")
```

---

## 6. The Task API & Delegation

The Task API (`mode="task"`) enables structured, multi-turn interactions where sub-agents work toward a specific goal (e.g., filling a schema).

**Sample Code (`task_samples/task_sub_agent`):**
```python
order_collector = Agent(name="order_collector", mode="task", output_schema=list[OrderItem])
payment_collector = Agent(name="payment_collector", mode="task", output_schema=PaymentInfo)

root_coordinator = Agent(
    name="coordinator",
    sub_agents=[order_collector, payment_collector],
    tools=[place_order],
    instruction="Coordinate order and payment collection."
)
```

---

## 7. Expert Best Practices

- **Node Idempotency**: Especially important for loops and HITL where nodes may be re-run on resumption.
- **Granular Edges**: Keep individual nodes focused. Use `Workflow` composition (Nested Workflows) for complex sub-systems.
- **Type Safety**: Leverage Pydantic models for `input_schema` and `output_schema` to catch errors early in the chain.
- **State Partitioning**: Use `output_key` on Agents to prevent state collisions in parallel branches.
