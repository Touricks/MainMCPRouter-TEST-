# Conditional Edges in LangGraph: Complete Guide

## What Are Conditional Edges?

Conditional edges are dynamic routing mechanisms in LangGraph that determine the next node to execute based on the current state. Unlike regular edges that always flow to the same destination, conditional edges evaluate a function to decide where to route the execution flow.

## Basic Syntax

```python
builder.add_conditional_edges(
    source_node,           # The node to route from
    routing_function,      # Function that returns the next node
    path_map              # Optional: maps function outputs to node names
)
```

## Current Implementation Analysis

Your ReAct agent uses a simple but effective conditional edge pattern:

```python
# From src/react_agent/graph.py
def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Binary routing: tools or end"""
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(f"Expected AIMessage")
    
    # Decision point
    if not last_message.tool_calls:
        return "__end__"  # Terminate
    return "tools"        # Continue to tools
```

## Advanced Routing Patterns

### 1. Multi-Path Routing with Priority

```python
from typing import Literal

def advanced_router(state: State) -> Literal["research", "analyze", "summarize", "__end__"]:
    """Route based on content analysis and state"""
    last_message = state.messages[-1]
    
    # Check for specific intents
    if "search" in last_message.content.lower() or "find" in last_message.content.lower():
        return "research"
    
    # Check if we have data to analyze
    if state.get("data_collected") and not state.get("analysis_complete"):
        return "analyze"
    
    # Check if we need summarization
    if state.get("analysis_complete") and not state.get("summary_generated"):
        return "summarize"
    
    # Check for tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    
    return "__end__"

# Add to graph
builder.add_conditional_edges(
    "call_model",
    advanced_router
)
```

### 2. State-Based Routing with Fallbacks

```python
def state_aware_router(state: State) -> str:
    """Route based on conversation state and history"""
    
    # Track attempt count
    attempt_count = state.get("attempt_count", 0)
    
    # Check if we're stuck in a loop
    if attempt_count > 3:
        return "fallback_handler"
    
    # Check message history for patterns
    recent_messages = state.messages[-3:]
    tool_calls_count = sum(
        1 for msg in recent_messages 
        if isinstance(msg, AIMessage) and msg.tool_calls
    )
    
    # Too many tool calls might indicate issues
    if tool_calls_count >= 3:
        return "human_review"
    
    # Normal routing
    last_message = state.messages[-1]
    if isinstance(last_message, AIMessage):
        if last_message.tool_calls:
            return "tools"
        elif "NEED_CLARIFICATION" in last_message.content:
            return "clarification_node"
    
    return "__end__"
```

### 3. Conditional Edges with Path Mapping

```python
def intent_classifier(state: State) -> str:
    """Classify intent and return a code"""
    last_message = state.messages[-1]
    content = last_message.content.lower()
    
    if "explain" in content or "how" in content:
        return "explain"
    elif "code" in content or "implement" in content:
        return "code"
    elif "test" in content:
        return "test"
    elif "document" in content:
        return "doc"
    else:
        return "general"

# Use path_map to map outputs to actual node names
builder.add_conditional_edges(
    "intent_processor",
    intent_classifier,
    path_map={
        "explain": "explanation_generator",
        "code": "code_generator",
        "test": "test_writer",
        "doc": "documentation_writer",
        "general": "call_model"
    }
)
```

### 4. Weighted/Probabilistic Routing

```python
import random
from typing import Literal

def weighted_router(state: State) -> Literal["fast_model", "accurate_model", "expert_model"]:
    """Route to different models based on complexity"""
    
    last_message = state.messages[-1]
    content = last_message.content
    
    # Calculate complexity score
    complexity_score = 0
    
    # Length-based scoring
    if len(content) > 500:
        complexity_score += 2
    elif len(content) > 200:
        complexity_score += 1
    
    # Keyword-based scoring
    complex_keywords = ["analyze", "complex", "detailed", "comprehensive"]
    complexity_score += sum(1 for kw in complex_keywords if kw in content.lower())
    
    # Technical term detection
    technical_terms = ["algorithm", "architecture", "implementation", "optimization"]
    complexity_score += sum(2 for term in technical_terms if term in content.lower())
    
    # Route based on score
    if complexity_score >= 5:
        return "expert_model"
    elif complexity_score >= 2:
        return "accurate_model"
    else:
        return "fast_model"
```

### 5. Conditional Edges with Error Handling

```python
def safe_router(state: State) -> str:
    """Router with comprehensive error handling"""
    try:
        last_message = state.messages[-1]
        
        # Check for error states
        if state.get("error_count", 0) > 2:
            return "error_recovery"
        
        # Check for timeout conditions
        if state.get("execution_time", 0) > 30:
            return "timeout_handler"
        
        # Check message type
        if isinstance(last_message, AIMessage):
            if last_message.tool_calls:
                # Validate tool calls
                for tool_call in last_message.tool_calls:
                    if tool_call.get("name") not in state.get("available_tools", []):
                        return "invalid_tool_handler"
                return "tools"
            else:
                return "__end__"
        else:
            return "message_processor"
            
    except Exception as e:
        # Log error and route to error handler
        print(f"Routing error: {e}")
        return "error_handler"
```

## Implementation Examples for Your ReAct Agent

### Example 1: Adding Quality Check Routing

```python
# Modify your graph.py to add quality checking
def enhanced_route_model_output(state: State) -> Literal["__end__", "tools", "quality_check"]:
    """Enhanced routing with quality checking"""
    last_message = state.messages[-1]
    
    if not isinstance(last_message, AIMessage):
        raise ValueError(f"Expected AIMessage")
    
    # Check if response needs quality validation
    if "CONFIDENCE: LOW" in last_message.content:
        return "quality_check"
    
    # Original logic
    if not last_message.tool_calls:
        return "__end__"
    return "tools"

# Add quality check node
async def quality_check_node(state: State, runtime: Runtime[Context]) -> Dict:
    """Validate and potentially retry with better prompting"""
    # Implementation here
    pass

# Update graph construction
builder.add_node("quality_check", quality_check_node)
builder.add_conditional_edges("call_model", enhanced_route_model_output)
builder.add_edge("quality_check", "call_model")  # Loop back after quality check
```

### Example 2: Adding Multi-Step Planning

```python
def planning_router(state: State) -> Literal["planner", "executor", "validator", "__end__"]:
    """Route through planning, execution, and validation phases"""
    
    # Check current phase
    phase = state.get("phase", "planning")
    
    if phase == "planning" and not state.get("plan_complete"):
        return "planner"
    elif phase == "execution" and state.get("plan_complete"):
        return "executor"
    elif phase == "validation" and state.get("execution_complete"):
        return "validator"
    else:
        return "__end__"

# Create a more sophisticated graph
builder = StateGraph(State)
builder.add_node("planner", planning_node)
builder.add_node("executor", execution_node)
builder.add_node("validator", validation_node)

builder.add_edge("__start__", "call_model")
builder.add_conditional_edges("call_model", planning_router)
```

### Example 3: Adding Parallel Processing Paths

```python
from langgraph.graph import END

def parallel_router(state: State) -> List[str]:
    """Route to multiple nodes in parallel"""
    last_message = state.messages[-1]
    paths = []
    
    # Determine which parallel paths to take
    if "analyze" in last_message.content.lower():
        paths.append("data_analyzer")
    if "visualize" in last_message.content.lower():
        paths.append("visualizer")
    if "report" in last_message.content.lower():
        paths.append("report_generator")
    
    # Always include a default path if no specific paths
    if not paths:
        paths.append("call_model")
    
    return paths

# For parallel execution (LangGraph supports this)
builder.add_conditional_edges(
    "dispatcher",
    parallel_router,
    # All paths will execute in parallel
)
```

## Best Practices

### 1. Type Safety
Always use `Literal` types for your return values:
```python
from typing import Literal

def router(state: State) -> Literal["node1", "node2", "__end__"]:
    # This ensures type checking catches invalid node names
    pass
```

### 2. State Validation
Always validate state before making routing decisions:
```python
def safe_router(state: State) -> str:
    if not state.messages:
        return "initialization"
    
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        return "message_handler"
    
    # Continue with routing logic
```

### 3. Logging and Debugging
Add logging to understand routing decisions:
```python
import logging

def logged_router(state: State) -> str:
    result = route_logic(state)
    logging.info(f"Routing decision: {result}, State: {state.get('phase')}")
    return result
```

### 4. Avoid Infinite Loops
Implement loop detection:
```python
def loop_aware_router(state: State) -> str:
    # Track node visits
    visits = state.get("node_visits", {})
    current_node = "call_model"
    
    # Increment visit count
    visits[current_node] = visits.get(current_node, 0) + 1
    
    # Detect loops
    if visits[current_node] > 5:
        return "__end__"  # Force termination
    
    # Normal routing continues...
```

### 5. Fallback Handling
Always have a fallback route:
```python
def robust_router(state: State) -> str:
    try:
        # Complex routing logic
        return complex_routing(state)
    except Exception as e:
        # Fallback to safe default
        return "__end__"
```

## Testing Conditional Edges

```python
# Test your routing functions independently
def test_route_model_output():
    # Create mock state
    mock_state = State(
        messages=[
            AIMessage(content="Hello", tool_calls=[{"name": "search"}])
        ]
    )
    
    # Test routing
    assert route_model_output(mock_state) == "tools"
    
    # Test without tool calls
    mock_state.messages = [AIMessage(content="Final answer")]
    assert route_model_output(mock_state) == "__end__"
```

## Common Patterns

### 1. ReAct Loop (Current Implementation)
- Model → Tools → Model → End

### 2. Plan-Execute Loop
- Planner → Executor → Validator → End

### 3. Hierarchical Routing
- Dispatcher → Sub-graphs → Aggregator → End

### 4. Error Recovery Loop
- Try → Catch → Retry/Fallback → End

### 5. Human-in-the-Loop
- Model → Human Review → Model → End

## Debugging Tips

1. **Visualize your graph**: Use LangGraph's built-in visualization
2. **Add state tracking**: Include routing history in state
3. **Use breakpoints**: Debug routing functions step by step
4. **Log extensively**: Track every routing decision
5. **Unit test routers**: Test routing functions in isolation

## Conclusion

Conditional edges are the control flow mechanism that makes LangGraph agents intelligent and adaptive. By mastering these patterns, you can create sophisticated agent behaviors that handle complex scenarios gracefully.

Your current ReAct implementation uses the simplest form effectively. Consider enhancing it with:
- Error handling routes
- Quality check loops
- Parallel processing paths
- State-based routing logic

The key is to start simple and add complexity only when needed for your specific use case.