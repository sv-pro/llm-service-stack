# Phase 3: Multi-Step Playbooks — Implementation Plan

**Timeline:** Weeks 9-12 (4 weeks)
**Goal:** Implement LangGraph workflow orchestration and three-path API
**Status:** 📋 Designed → 🔄 Ready to Start

---

## Overview

Phase 3 implements the core of the Reflective Intelligence Platform by enabling multi-step workflows through LangGraph. This phase delivers the **Re^Re loop infrastructure** where playbooks can Reason → Act → Reflect → Re-reason iteratively.

**Key Deliverables:**
1. LangGraph workflow engine with state management
2. Tool registry with 5+ adapters (LLM, HTTP, MCP, etc.)
3. Three-path API implementation (Semantic, Syntactic, Intent)
4. Execution persistence and rollback support
5. Budget enforcement and cost tracking

---

## Week 9: LangGraph Foundation

### Day 1-2: Setup & Dependencies

**Tasks:**
- [ ] Add LangGraph to dependencies
  ```bash
  # pyproject.toml or requirements.txt
  langgraph>=0.1.0
  langgraph-checkpoint-sqlite>=0.1.0
  ```
- [ ] Create directory structure
  ```
  src/
    workflows/
      __init__.py
      base.py          # Base workflow classes
      state.py         # Playbook state models
      nodes.py         # Workflow node implementations
      graphs.py        # Graph definitions
    tools/
      __init__.py
      registry.py      # Tool registry
      adapters/
        __init__.py
        llm.py        # LLM tool adapter
        http.py       # HTTP API adapter
        mcp.py        # MCP adapter
  ```
- [ ] Set up basic imports and test infrastructure

**Deliverables:**
- Dependencies installed
- Directory structure created
- Basic test file structure

---

### Day 3-4: Playbook State Model

**Tasks:**
- [ ] Define `PlaybookState` TypedDict
  ```python
  from typing import TypedDict, List, Dict, Any

  class PlaybookState(TypedDict):
      # Core state
      intent: str                      # Original intent/request
      context: Dict[str, Any]          # Execution context
      steps_completed: List[str]       # Step execution history
      artifacts: List[Dict]            # Generated artifacts
      budget_used: float               # Cost tracking

      # Control flow
      current_step: str                # Current step ID
      should_continue: bool            # Continue execution flag
      error: Optional[str]             # Error state

      # Reflection
      quality_score: float             # Quality evaluation
      improvement_suggestions: List[str]  # Reflective insights
  ```

- [ ] Create state management utilities
  - State serialization/deserialization
  - State validation
  - State transitions

- [ ] Implement SQLite checkpoint backend
  ```python
  from langgraph.checkpoint.sqlite import SqliteSaver

  # Initialize checkpoint storage
  checkpoint_saver = SqliteSaver(db_path="./data/checkpoints.db")
  ```

- [ ] Write unit tests for state model

**Deliverables:**
- `src/workflows/state.py` with PlaybookState
- State management utilities
- Checkpoint persistence
- Unit tests

---

### Day 5: Workflow Nodes - Part 1 (Reason + Act)

**Tasks:**
- [ ] Implement `analyze_intent` node
  ```python
  async def analyze_intent_node(state: PlaybookState) -> PlaybookState:
      """
      REASON phase: Analyze the intent and determine execution plan
      """
      intent = state["intent"]

      # Extract parameters from intent
      # Determine required tools
      # Plan execution steps

      state["current_step"] = "execute_tool"
      state["should_continue"] = True
      return state
  ```

- [ ] Implement `execute_tool` node
  ```python
  async def execute_tool_node(state: PlaybookState) -> PlaybookState:
      """
      ACT phase: Execute the selected tool
      """
      tool_name = state["context"]["selected_tool"]
      tool_input = state["context"]["tool_input"]

      # Execute tool via registry
      result = await tool_registry.execute(tool_name, tool_input)

      # Track cost
      state["budget_used"] += result.cost

      # Store artifact
      state["artifacts"].append(result.artifact)

      state["current_step"] = "evaluate_result"
      return state
  ```

- [ ] Write unit tests for nodes

**Deliverables:**
- `analyze_intent_node` implementation
- `execute_tool_node` implementation
- Node unit tests

---

### Day 6-7: Workflow Nodes - Part 2 (Reflect + Re-reason)

**Tasks:**
- [ ] Implement `evaluate_result` node
  ```python
  async def evaluate_result_node(state: PlaybookState) -> PlaybookState:
      """
      REFLECT phase: Evaluate execution outcomes
      """
      last_artifact = state["artifacts"][-1]

      # Quality scoring (can use LLM for evaluation)
      quality_score = await evaluate_quality(last_artifact)
      state["quality_score"] = quality_score

      # Check if goal is met
      goal_met = quality_score > 0.7

      state["current_step"] = "decide_next" if goal_met else "re_reason"
      return state
  ```

- [ ] Implement `decide_next` node
  ```python
  async def decide_next_node(state: PlaybookState) -> PlaybookState:
      """
      RE-REASON phase: Decide next action based on results
      """
      # Check budget constraints
      if state["budget_used"] >= state["context"]["budget_max"]:
          state["should_continue"] = False
          return state

      # Determine if more steps needed
      steps_remaining = state["context"]["max_steps"] - len(state["steps_completed"])

      if steps_remaining > 0:
          # Generate improvement suggestions
          state["improvement_suggestions"] = await generate_improvements(state)
          state["current_step"] = "analyze_intent"  # Loop back
      else:
          state["should_continue"] = False

      return state
  ```

- [ ] Write integration tests for node chaining

**Deliverables:**
- `evaluate_result_node` implementation
- `decide_next_node` implementation
- Integration tests

---

## Week 10: Tool Registry & Graph Assembly

### Day 8-9: Tool Registry

**Tasks:**
- [ ] Design `ToolRegistry` interface
  ```python
  class ToolRegistry:
      def __init__(self):
          self._tools: Dict[str, Tool] = {}

      def register(self, tool: Tool) -> None:
          """Register a tool"""
          self._tools[tool.name] = tool

      async def execute(self, tool_name: str, input_data: Dict) -> ToolResult:
          """Execute a tool by name"""
          tool = self._tools.get(tool_name)
          if not tool:
              raise ToolNotFoundError(f"Tool '{tool_name}' not found")

          # Validate input schema
          tool.validate_input(input_data)

          # Execute
          result = await tool.execute(input_data)

          # Validate output schema
          tool.validate_output(result.data)

          return result

      def list_tools(self) -> List[str]:
          """List registered tools"""
          return list(self._tools.keys())
  ```

- [ ] Implement `Tool` base class
  ```python
  from abc import ABC, abstractmethod

  class Tool(ABC):
      def __init__(self, name: str, description: str):
          self.name = name
          self.description = description
          self.input_schema: Dict = {}
          self.output_schema: Dict = {}

      @abstractmethod
      async def execute(self, input_data: Dict) -> ToolResult:
          """Execute the tool"""
          pass

      def validate_input(self, data: Dict) -> None:
          """Validate input against schema"""
          # JSON schema validation
          pass

      def validate_output(self, data: Dict) -> None:
          """Validate output against schema"""
          pass
  ```

- [ ] Implement LLM tool adapter
  ```python
  class LLMTool(Tool):
      def __init__(self, model: str):
          super().__init__(
              name=f"llm_{model}",
              description=f"Call {model} LLM"
          )
          self.model = model

      async def execute(self, input_data: Dict) -> ToolResult:
          # Use existing LiteLLM integration
          response = await litellm_call(
              model=self.model,
              messages=input_data["messages"]
          )

          return ToolResult(
              data={"response": response.choices[0].message.content},
              cost=response.usage.total_cost,
              metadata={"model": self.model}
          )
  ```

- [ ] Write tool registry tests

**Deliverables:**
- `src/tools/registry.py` with ToolRegistry
- `src/tools/base.py` with Tool base class
- `src/tools/adapters/llm.py` with LLMTool
- Unit tests

---

### Day 10-11: Additional Tool Adapters

**Tasks:**
- [ ] Implement HTTP API adapter
  ```python
  class HTTPTool(Tool):
      def __init__(self, name: str, base_url: str, method: str = "GET"):
          super().__init__(name, f"HTTP {method} to {base_url}")
          self.base_url = base_url
          self.method = method

      async def execute(self, input_data: Dict) -> ToolResult:
          async with httpx.AsyncClient() as client:
              response = await client.request(
                  method=self.method,
                  url=f"{self.base_url}/{input_data.get('path', '')}",
                  json=input_data.get("body"),
                  headers=input_data.get("headers", {})
              )

              return ToolResult(
                  data={"response": response.json()},
                  cost=0.0,  # External API cost
                  metadata={"status_code": response.status_code}
              )
  ```

- [ ] Implement MCP adapter stub
  ```python
  class MCPTool(Tool):
      """Model Context Protocol tool adapter"""

      def __init__(self, name: str, mcp_server_url: str):
          super().__init__(name, f"MCP tool: {name}")
          self.mcp_server_url = mcp_server_url

      async def execute(self, input_data: Dict) -> ToolResult:
          # MCP protocol implementation
          # For now, stub with basic structure
          return ToolResult(
              data={"message": "MCP stub - not yet implemented"},
              cost=0.0,
              metadata={"mcp_server": self.mcp_server_url}
          )
  ```

- [ ] Add custom Python function adapter
  ```python
  class PythonFunctionTool(Tool):
      """Execute arbitrary Python function as tool"""

      def __init__(self, name: str, func: Callable):
          super().__init__(name, func.__doc__ or "Python function")
          self.func = func

      async def execute(self, input_data: Dict) -> ToolResult:
          result = await self.func(**input_data)
          return ToolResult(
              data={"result": result},
              cost=0.0,
              metadata={"function": self.func.__name__}
          )
  ```

- [ ] Write adapter tests

**Deliverables:**
- `src/tools/adapters/http.py`
- `src/tools/adapters/mcp.py`
- `src/tools/adapters/python_function.py`
- Integration tests

---

### Day 12-13: Graph Assembly

**Tasks:**
- [ ] Create workflow graph
  ```python
  from langgraph.graph import StateGraph, END

  def create_playbook_graph() -> StateGraph:
      """
      Create the playbook execution graph

      Graph flow:
      analyze_intent → execute_tool → evaluate_result → decide_next
                                                              ↓
                                                        (loop or END)
      """
      workflow = StateGraph(PlaybookState)

      # Add nodes
      workflow.add_node("analyze_intent", analyze_intent_node)
      workflow.add_node("execute_tool", execute_tool_node)
      workflow.add_node("evaluate_result", evaluate_result_node)
      workflow.add_node("decide_next", decide_next_node)

      # Add edges
      workflow.add_edge("analyze_intent", "execute_tool")
      workflow.add_edge("execute_tool", "evaluate_result")

      # Conditional edge: continue or end?
      workflow.add_conditional_edges(
          "evaluate_result",
          should_continue,
          {
              True: "decide_next",
              False: END
          }
      )

      # Loop back or end
      workflow.add_conditional_edges(
          "decide_next",
          lambda state: state["should_continue"],
          {
              True: "analyze_intent",
              False: END
          }
      )

      # Set entry point
      workflow.set_entry_point("analyze_intent")

      return workflow
  ```

- [ ] Add checkpoint integration
  ```python
  # Compile graph with checkpoint support
  app = workflow.compile(checkpointer=checkpoint_saver)
  ```

- [ ] Implement execution function
  ```python
  async def execute_playbook(
      intent: str,
      context: Dict[str, Any],
      budget_max: float = 1.0
  ) -> PlaybookState:
      """
      Execute a playbook workflow
      """
      initial_state: PlaybookState = {
          "intent": intent,
          "context": {**context, "budget_max": budget_max},
          "steps_completed": [],
          "artifacts": [],
          "budget_used": 0.0,
          "current_step": "analyze_intent",
          "should_continue": True,
          "error": None,
          "quality_score": 0.0,
          "improvement_suggestions": []
      }

      # Execute with checkpoint thread
      config = {"configurable": {"thread_id": f"playbook_{uuid.uuid4()}"}}

      final_state = await app.ainvoke(initial_state, config)

      return final_state
  ```

- [ ] Write graph execution tests

**Deliverables:**
- `src/workflows/graphs.py` with graph creation
- `execute_playbook()` function
- End-to-end workflow tests

---

### Day 14: Budget Enforcement & Rollback

**Tasks:**
- [ ] Implement budget tracking
  ```python
  def check_budget(state: PlaybookState) -> PlaybookState:
      if state["budget_used"] >= state["context"]["budget_max"]:
          state["error"] = "Budget exceeded"
          state["should_continue"] = False
      return state
  ```

- [ ] Add budget checkpoint
  ```python
  # Add budget check before each expensive operation
  workflow.add_node("check_budget", check_budget)
  workflow.add_edge("analyze_intent", "check_budget")
  workflow.add_conditional_edges(
      "check_budget",
      lambda state: state.get("error") is None,
      {
          True: "execute_tool",
          False: END
          }
  )
  ```

- [ ] Implement rollback support
  ```python
  async def rollback_playbook(thread_id: str, checkpoint_id: str):
      """Rollback to a specific checkpoint"""
      # Load checkpoint
      state = await checkpoint_saver.aget(thread_id, checkpoint_id)

      # Resume from checkpoint
      # This allows restarting execution from a known good state
      return state
  ```

- [ ] Write budget and rollback tests

**Deliverables:**
- Budget enforcement in workflow
- Rollback functionality
- Tests for budget limits and rollback

---

## Week 11-12: Three-Path API Implementation

### Week 11, Day 15-17: Path 1 (Semantic Gateway)

**Tasks:**
- [ ] Update `/v1/responses` endpoint
  ```python
  from src.api.models import ResponseRequest, ResponseObject

  @app.post("/v1/responses")
  async def responses_endpoint(request: ResponseRequest) -> ResponseObject:
      """
      Full OpenAI Responses API compliance
      Supports: reasoning tokens, tool execution, structured outputs
      """
      # Execute via playbook if applicable
      playbook_result = await execute_playbook(
          intent=request.input,
          context={"model": request.model}
      )

      # Format as ResponseObject
      response = ResponseObject(
          id=f"resp_{uuid.uuid4()}",
          object="response",
          created=int(time.time()),
          model=request.model,
          output=playbook_result["artifacts"][-1]["data"],
          usage={
              "prompt_tokens": 0,  # Calculate from playbook
              "completion_tokens": 0,
              "reasoning_tokens": 0,  # Track LLM reasoning steps
              "total_tokens": 0
          },
          metadata={
              "playbook_executed": True,
              "steps_completed": len(playbook_result["steps_completed"]),
              "budget_used": playbook_result["budget_used"]
          }
      )

      return response
  ```

- [ ] Add reasoning token tracking
- [ ] Add tool execution metadata
- [ ] Write API tests

**Deliverables:**
- Updated `/v1/responses` endpoint
- Reasoning token tracking
- Tool metadata support
- API integration tests

---

### Week 11, Day 18-19: Path 2 (Syntactic Sugar)

**Tasks:**
- [ ] Update `/v1/chat/completions` for internal tracking
  ```python
  @app.post("/v1/chat/completions")
  async def chat_completions_endpoint(request: ChatCompletionRequest):
      """
      Legacy compatibility with internal reasoning tracking
      """
      # Execute same playbook logic internally
      playbook_result = await execute_playbook(
          intent=request.messages[-1].content,
          context={"model": request.model}
      )

      # Format as ChatCompletion (hide reasoning tokens)
      response = ChatCompletionResponse(
          id=f"chatcmpl_{uuid.uuid4()}",
          object="chat.completion",
          created=int(time.time()),
          model=request.model,
          choices=[{
              "index": 0,
              "message": {
                  "role": "assistant",
                  "content": playbook_result["artifacts"][-1]["data"]
              },
              "finish_reason": "stop"
          }],
          usage={
              "prompt_tokens": 0,
              "completion_tokens": 0,
              "total_tokens": 0
              # Note: reasoning_tokens NOT exposed
          }
      )

      # Add upgrade hint header
      response.headers["X-Upgrade-Available"] = "/v1/responses"
      response.headers["X-Gateway-Reasoning-Tokens"] = str(
          playbook_result.get("reasoning_tokens", 0)
      )

      return response
  ```

- [ ] Add internal reasoning tracking
- [ ] Add upgrade hint headers
- [ ] Write compatibility tests

**Deliverables:**
- Updated `/v1/chat/completions`
- Internal reasoning tracking
- Migration hint headers
- Backward compatibility tests

---

### Week 12, Day 20-22: Path 3 (Intent Handling)

**Tasks:**
- [ ] Implement `/v1/intents` endpoint
  ```python
  @app.post("/v1/intents")
  async def intents_endpoint(request: IntentRequest) -> IntentResponse:
      """
      Intent→Template→Playbook execution
      """
      # Resolve intent
      intent = await resolve_intent(request.input)

      # Get playbook for intent
      playbook = await get_playbook_for_intent(intent.id)

      # Execute playbook
      result = await execute_playbook(
          intent=request.input,
          context={
              "intent_id": intent.id,
              "confidence": intent.confidence,
              **request.context
          }
      )

      return IntentResponse(
          intent=intent.name,
          confidence=intent.confidence,
          playbook_id=playbook.id,
          artifacts=result["artifacts"],
          cost=result["budget_used"],
          execution_log=result["steps_completed"]
      )
  ```

- [ ] Implement intent resolution stub
  ```python
  async def resolve_intent(input_text: str) -> Intent:
      """
      Resolve input to intent (stub for Phase 4)
      For now, just return a default intent
      """
      return Intent(
          id="default",
          name="DefaultIntent",
          confidence=1.0,
          embedding=[]
      )
  ```

- [ ] Add execution logging
- [ ] Write intent API tests

**Deliverables:**
- `/v1/intents` endpoint
- Intent resolution stub
- Execution logging
- API tests

---

### Week 12, Day 23-24: Shared Infrastructure & Testing

**Tasks:**
- [ ] Ensure all three paths use same caching
  ```python
  # All paths should go through semantic cache
  @lru_cache(maxsize=1000)
  def get_cached_response(cache_key: str):
      # Unified cache lookup
      pass
  ```

- [ ] Ensure all paths use same cost tracking
  ```python
  # Track costs in same ledger
  await cost_ledger.record(
      request_id=request_id,
      path="responses" | "chat/completions" | "intents",
      cost=total_cost
  )
  ```

- [ ] Write integration tests for all three paths
- [ ] Performance testing (target: <2s response time)
- [ ] Load testing (target: 100 req/s)

**Deliverables:**
- Unified caching across paths
- Unified cost tracking
- Integration test suite
- Performance benchmarks

---

### Week 12, Day 25-26: Dashboard Updates

**Tasks:**
- [ ] Add path selector to Playground
  ```jsx
  <select value={selectedPath} onChange={e => setSelectedPath(e.target.value)}>
    <option value="responses">Path 1: Responses API</option>
    <option value="chat">Path 2: Chat Completions</option>
    <option value="intents">Path 3: Intents</option>
  </select>
  ```

- [ ] Update request history to show path used
- [ ] Add playbook execution visualization
- [ ] Update cost tracking to show path breakdown

**Deliverables:**
- Dashboard supports all three paths
- Execution visualization
- Path-based analytics

---

### Week 12, Day 27-28: Documentation & Polish

**Tasks:**
- [ ] Write API documentation
  - Path 1: Responses API guide
  - Path 2: Chat Completions compatibility guide
  - Path 3: Intents API guide
- [ ] Update CHANGELOG.md
- [ ] Create migration guide (Path 2 → Path 1)
- [ ] Add code examples for each path
- [ ] Final testing and bug fixes

**Deliverables:**
- Complete API documentation
- Migration guides
- Code examples
- Bug-free release

---

## Success Criteria

### Must Have ✅
- [ ] LangGraph workflows execute successfully
- [ ] Tool registry supports 5+ tool types
- [ ] All three API paths implemented and functional
- [ ] Budget enforcement working
- [ ] Rollback functionality tested
- [ ] 100% test coverage for critical paths
- [ ] All 187 existing tests still passing

### Nice to Have 🎯
- [ ] MCP adapter fully implemented (not just stub)
- [ ] Advanced rollback with partial execution replay
- [ ] Real-time execution progress tracking
- [ ] Workflow visualization in dashboard

### Performance Targets 📊
- [ ] API response time <2s (P95)
- [ ] Workflow execution overhead <100ms
- [ ] Tool execution latency <500ms
- [ ] Budget check overhead <10ms

---

## Risk Mitigation

### Risk 1: LangGraph Learning Curve
**Mitigation:** Start with simple linear workflows, add complexity iteratively

### Risk 2: Tool Registry Complexity
**Mitigation:** Implement adapters incrementally (LLM first, then HTTP, then MCP)

### Risk 3: Three-Path API Divergence
**Mitigation:** Share maximum code between paths, extract common logic

### Risk 4: Performance Regression
**Mitigation:** Benchmark after each major change, keep existing cache optimizations

---

## Next Steps After Phase 3

1. **Phase 4:** Intent Routing (Weeks 13-16)
   - Replace stub intent resolution with real semantic matching
   - Implement intent registry with vector search
   - Build first 5 playgrounds

2. **Phase 5:** Feedback Loop (Weeks 17-18)
   - Add outcome evaluation
   - Implement feedback collection UI
   - Start learning from execution results

---

**Last Updated:** 2025-11-08
**Owner:** Core Platform Team
**Status:** Ready for execution
