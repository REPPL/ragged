# Ragged v0.8 Roadmap - Agent Capabilities

**Status:** Planned

**Duration:** 60-80 hours (AI implementation)

**Focus:** Intelligent agents for complex workflows and tool use

**Breaking Changes:** None

---

## Overview

Version 0.8 introduces agent capabilities for handling complex, multi-step tasks that require planning, tool use, and iterative refinement. This addresses a major feature gap identified in the ecosystem analysis—agentic workflows and multi-agent orchestration.

**Dependencies:** Requires v0.7 completion (enterprise foundation, authentication)

**Strategic Context:** Brings ragged in line with RAGFlow's multi-agent orchestration and AnythingLLM's no-code agent builder, while maintaining privacy-first principles.

---

## AGENT-001: Agent Framework Foundation (25-30 hours)

**Problem:** No framework for agentic workflows; all queries are single-shot with no planning or tool use.

**Inspiration:** RAGFlow's multi-agent orchestration, Haystack's agent nodes, AnythingLLM's agent builder.

**Implementation:**
1. Research agent frameworks (ReAct, Plan-and-Execute, ReWOO) [4-5 hours]
2. Design agent architecture (planner, executor, tools) [6-8 hours]
3. Implement agent orchestrator [8-10 hours]
4. Add tool registry and execution environment [4-5 hours]
5. Create agent state management and memory [3-4 hours]

**Agent architecture:**
```python
class Agent:
    def __init__(self, tools: list[Tool], memory: Memory):
        self.planner = Planner()      # Create execution plan
        self.executor = Executor()    # Execute tool calls
        self.tools = ToolRegistry(tools)
        self.memory = memory          # Conversation memory

    async def run(self, task: str) -> AgentResponse:
        # 1. Plan: Break down task into steps
        plan = await self.planner.create_plan(task, self.tools)

        # 2. Execute: Run each step with tools
        for step in plan.steps:
            tool_result = await self.executor.run_step(step, self.tools)
            self.memory.add(step, tool_result)

        # 3. Synthesize: Generate final response
        return await self.synthesize(plan, self.memory)
```

**Agent types:**
- **Research Agent:** Multi-document analysis, citation gathering
- **Summarization Agent:** Hierarchical summarization of large corpuses
- **Question-Answering Agent:** Multi-hop reasoning across documents
- **Custom Agent:** User-defined workflows

**Files:**
- `src/agents/base.py` (abstract agent, ~300 lines)
- `src/agents/planner.py` (task planning, ~350 lines)
- `src/agents/executor.py` (step execution, ~400 lines)
- `src/agents/orchestrator.py` (agent management, ~250 lines)
- `tests/agents/test_agent.py` (~300 lines)

**Manual Testing:**
- Create research agent task: "Find all mentions of X across documents and summarize"
- Verify planning creates logical steps
- Confirm tool execution successful
- Validate final synthesis quality

**Success:** Agent framework functional; multi-step tasks execute correctly with tool use

---

## AGENT-002: Tool Library (20-25 hours)

**Problem:** Agents need tools to interact with external systems; no tool abstraction exists.

**Inspiration:** Haystack's tool nodes, LangChain's tool ecosystem.

**Implementation:**
1. Design tool abstraction and interface [4-5 hours]
2. Implement core RAG tools (query, search, summarize) [6-8 hours]
3. Add document tools (list, filter, metadata) [4-5 hours]
4. Create external tools (web search, calculator, date) [4-5 hours]
5. Add tool validation and safety checks [2-3 hours]

**Core RAG tools:**
- `VectorSearchTool`: Semantic search across documents
- `BM25SearchTool`: Keyword search
- `HybridSearchTool`: Combined vector + BM25
- `SummarizeTool`: Summarize document/chunk
- `CitationTool`: Extract citations for claims
- `MetadataFilterTool`: Filter by metadata

**External tools:**
- `WebSearchTool`: Search web for current information (optional, privacy risk)
- `CalculatorTool`: Mathematical calculations
- `DateTimeTool`: Current date/time operations
- `PythonREPLTool`: Execute Python code (sandboxed)

**Tool interface:**
```python
class Tool(ABC):
    name: str
    description: str
    parameters: dict  # JSON schema

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute tool with validated parameters."""
        pass
```

**Files:**
- `src/agents/tools/base.py` (abstract tool, ~200 lines)
- `src/agents/tools/rag_tools.py` (RAG-specific tools, ~400 lines)
- `src/agents/tools/external_tools.py` (external tools, ~300 lines)
- `src/agents/tools/registry.py` (tool registry, ~150 lines)
- `tests/agents/tools/test_tools.py` (~350 lines)

**Manual Testing:**
- Execute each tool individually
- Verify parameter validation
- Test tool chaining (one tool output → next tool input)
- Confirm safety checks prevent harmful operations

**Success:** Tool library complete; agents can use tools reliably; safety validated

---

## AGENT-003: Visual Workflow Builder Backend (15-20 hours)

**Problem:** Creating agent workflows requires code; no visual interface for non-programmers.

**Inspiration:** RAGFlow's visual DAG workflow editor—highly requested feature.

**Implementation:**
1. Design workflow graph data structure [3-4 hours]
2. Implement workflow parser and validator [5-6 hours]
3. Create workflow execution engine [5-6 hours]
4. Add workflow serialization (JSON) [2-3 hours]

**Workflow structure:**
```json
{
  "name": "Research Workflow",
  "nodes": [
    {"id": "1", "type": "query", "tool": "HybridSearchTool", "params": {}},
    {"id": "2", "type": "filter", "tool": "MetadataFilterTool", "params": {}},
    {"id": "3", "type": "summarize", "tool": "SummarizeTool", "params": {}}
  ],
  "edges": [
    {"from": "1", "to": "2"},
    {"from": "2", "to": "3"}
  ]
}
```

**Workflow features:**
- **DAG validation:** Prevent cycles, validate connections
- **Conditional branching:** If/else based on tool results
- **Parallel execution:** Run independent branches concurrently
- **Error handling:** Retry, fallback, skip strategies

**Files:**
- `src/agents/workflow/graph.py` (DAG structure, ~250 lines)
- `src/agents/workflow/parser.py` (JSON → graph, ~200 lines)
- `src/agents/workflow/executor.py` (run workflow, ~300 lines)
- `tests/agents/workflow/test_workflow.py` (~250 lines)

**Note:** Frontend visual editor deferred to v0.9 Web UI Completion. This is backend only.

**Manual Testing:**
- Create workflow JSON file
- Execute workflow with test data
- Verify conditional branching works
- Test parallel execution performance

**Success:** Workflow backend functional; JSON workflows execute correctly; ready for v0.9 UI

---

## AGENT-004: Multi-Agent Orchestration (Experimental) (15-20 hours)

**Problem:** Complex tasks require multiple specialized agents working together; no coordination framework.

**Inspiration:** RAGFlow's multi-agent capabilities for complex tasks.

**Status:** EXPERIMENTAL - Validate use cases before production

**Implementation:**
1. Research multi-agent coordination patterns [3-4 hours]
2. Implement agent communication protocol [5-6 hours]
3. Create task delegation and routing [4-5 hours]
4. Add agent conflict resolution [2-3 hours]
5. Implement shared memory/context [1-2 hours]

**Multi-agent patterns:**
- **Hierarchical:** Manager agent delegates to specialist agents
- **Collaborative:** Agents share findings and build on each other's work
- **Competitive:** Multiple agents solve independently, best result selected
- **Sequential:** Chain of specialists (research → analyze → summarize)

**Example workflow:**
```python
# Research task requiring multiple agents
task = "Analyze market trends across 100 documents and create investment thesis"

# 1. Document Agent: Find relevant documents
docs = await document_agent.run("Find market trend documents")

# 2. Analysis Agent: Analyze each document
analyses = await analysis_agent.run("Extract trends", docs)

# 3. Synthesis Agent: Create thesis
thesis = await synthesis_agent.run("Create thesis", analyses)
```

**Files:**
- `src/agents/orchestration/coordinator.py` (multi-agent coord, ~350 lines)
- `src/agents/orchestration/communication.py` (agent messaging, ~200 lines)
- `src/agents/orchestration/delegation.py` (task routing, ~250 lines)
- `tests/agents/orchestration/test_multi_agent.py` (~300 lines)

**Manual Testing:**
- Create multi-agent workflow (3+ agents)
- Verify agents communicate correctly
- Test task delegation logic
- Validate result synthesis from multiple agents

**Success:** Multi-agent coordination functional; complex tasks complete successfully

**Known Risk:** Complexity may outweigh benefits for personal use cases; validate demand

---

## AGENT-005: CLI Agent Commands (10-15 hours)

**Problem:** No CLI interface for agent workflows; users can't interact with agents.

**Implementation:**
1. Create agent execution command [4-5 hours]
2. Add workflow management commands [3-4 hours]
3. Implement tool listing and testing [2-3 hours]
4. Add agent templates library [1-2 hours]

**CLI commands:**
```bash
# Execute agent task
ragged agent run research "Analyze sentiment across documents"

# List available agents
ragged agent list

# Create agent from template
ragged agent create --template research-agent --name my-agent

# Execute workflow file
ragged workflow run research-workflow.json

# List available tools
ragged agent tools list

# Test tool execution
ragged agent tools test VectorSearchTool --params '{"query": "test"}'
```

**Agent templates:**
- `research-agent`: Multi-document research and citation
- `summarization-agent`: Hierarchical summarization
- `qa-agent`: Multi-hop question answering
- `custom-agent`: Blank template for user customization

**Files:**
- `src/main.py` (add agent commands)
- `src/cli/commands/agent.py` (new, ~350 lines)
- `src/agents/templates/` (agent templates, ~400 lines total)
- `tests/cli/test_agent_commands.py` (~200 lines)

**Manual Testing:**
- Run each CLI command
- Execute agent from template
- Verify workflow execution from JSON file
- Test tool listing and execution

**Success:** CLI provides full agent control; templates accelerate user adoption

---

## Success Criteria

**Automated Tests:**
- [ ] Agent planning creates valid execution plans
- [ ] Agent executor runs steps with tools correctly
- [ ] Tool registry validates parameters
- [ ] Workflow parser rejects invalid DAGs
- [ ] Workflow executor handles conditional branching
- [ ] Multi-agent coordination routes tasks correctly
- [ ] CLI agent commands execute without errors
- [ ] All existing tests pass

**Manual Testing:**
- [ ] Create multi-step research agent task
- [ ] Execute workflow JSON file successfully
- [ ] Use tool directly via CLI
- [ ] Run multi-agent workflow (3+ agents)
- [ ] Create agent from template
- [ ] Verify agent memory persists context across steps

**Quality Gates:**
- [ ] Agent success rate >80% for well-defined tasks
- [ ] Tool execution latency <1 second per tool
- [ ] Workflow validation catches all invalid DAGs
- [ ] Agent templates cover 3+ common use cases
- [ ] Documentation complete for all agent features
- [ ] Multi-agent overhead <20% vs single agent

---

## Known Risks

- **Complexity:** Agent reasoning may be unpredictable; extensive testing needed
- **Performance:** Multi-step workflows may be slow; optimize tool execution
- **User adoption:** Agents may be too complex for average users; provide good templates
- **Privacy:** External tools (web search) compromise privacy—make optional and clearly documented
- **Tool safety:** Python REPL and other powerful tools need sandboxing
- **Multi-agent overhead:** Coordination may not justify complexity for simple tasks

---

## Next Steps

After v0.8 completion:
- **v0.9:** Web UI Completion (visual workflow editor frontend, block editor, PWA)
- **v1.0:** Personal Knowledge Platform (polish, stability, v1.0 release)

See: `roadmap/version/v0.9/README.md`

---

## Related Documentation

- [Previous Version](../v0.7/README.md) - Enterprise foundation
- [Next Version](../v0.9/README.md) - Web UI completion
- [Planning](../../planning/version/v0.8/) - Design goals for v0.8 (if exists)
- [Version Overview](../README.md) - Complete version comparison
- [Projects to Learn From](../../../research/projects-to-learn-from.md) - RAGFlow multi-agent inspiration

---
