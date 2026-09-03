# 08 · Agent Architectures in Depth: From ReAct to Multi-agent

> [中文版](../08-agent-architectures.md) · English

> Part 8 of the series *LLMs from the Ground Up*, and the last of the main line. Part 6 introduced the basic agent loop; this chapter takes it apart down to the bone: the ReAct paradigm, the tool-calling mechanism, the graph/state-machine model, planning, multi-agent systems, and finally a decision map of "when to use what".

## Layer one: the truth about ReAct and tool calling

![ReAct and the tool-calling mechanism](../images/ag_react_tool_calling.png)

**ReAct = Reasoning + Acting.** Before it, agents either only "thought" (chain of thought, no action) or only "did" (calling tools directly, without explanation). ReAct interleaves the two in a loop: write a **Thought** (reasoning) → issue an **Action** (tool call) → receive an **Observation** (result) → write the next Thought. Each step's thinking is built on the new information observed in the previous step, so the agent can adjust as it goes: if the search results are wrong, the next Thought can change course.

**The four steps of tool calling:**

1. **Give the model the tool list**: each tool's name, description, and parameter schema go into the prompt; that is how the model "knows" which tools exist.
2. **The model emits a structured call**: modern models are specifically fine-tuned to output "I want to call search with parameters..." in a fixed format.
3. **The runtime parses and executes**: the agent framework (not the model) actually calls the function, API, or database.
4. **The result is fed back**: the execution result is appended as a new message to the model, starting the next round.

The one sentence to burn into memory: **the model only ever generates text.** Even "I want to call search" is just a structured textual request; the model itself cannot touch the outside world. An agent = an LLM + a loop + a set of tools + a runtime that executes.

Incidentally, "reasoning models" fold the Thought into the model's internal thinking rather than writing it out as explicit text. Both styles have the same purpose: to ground the Action in enough reasoning.

## Layer two: building the agent as a graph (state machine)

![A LangGraph state graph](../images/ag_state_machine.png)

The basic loop is a hard-coded straight line. Real agents need branching, conditional loops, human approval, pausing and resuming, and a while loop cannot express those clearly. Modern frameworks (LangGraph and others) model an agent as a **graph** with three abstractions:

- **State**: the flowing shared memory, most importantly the `messages` list, that ever-growing context. Every node reads it and appends to it.
- **Node**: one step of work, essentially a function that takes the current State and returns an update. "Call the LLM" is a node, "execute the tool" is a node, and a node can contain arbitrary code.
- **Edge**: control flow. A normal edge is always taken; a **conditional edge** runs a routing function after a node finishes, which looks at the State and decides where to go next.

The core of ReAct is a single conditional edge: after the `agent` node runs, check whether the last message has tool_calls; if yes go to the `tools` node, if not go to `END`. This also solves "when do we stop" for free: that conditional edge is the termination condition.

Why is upgrading to a graph worth it? Because **control flow goes from "hard-coded code" to "data you can inspect and modify"**: want human approval before a dangerous tool, insert a node and an edge; want to prevent infinite loops, add a counter to the State. State is a first-class object that can be checkpointed, so you can pause, resume, put a human in the loop, or even rewind and rerun from a given step. Multi-agent follows naturally too: each agent is a node or a subgraph.

## Layer three: planning

![A planning agent](../images/ag_planning.png)

ReAct is reactive: it only sees the next step, never the whole picture. Once a task gets long (a dozen or twenty steps, with dependencies), it tends to drift, repeat work, and walk into dead ends. And every step requires stuffing the entire context into a large model and computing again, which is slow and expensive. The planning approach is to **work out the overall plan of attack first, then act**.

**The three nodes of Plan-and-Execute:**

- **Planner**: have an LLM produce an explicit step-by-step plan first. Usually the strongest model, because decomposition is the hardest part.
- **Executor**: carry out the current step. Each step can itself be a small ReAct agent, and because the task is narrow, a cheaper small model will do. **The expensive planning happens once, the cheap execution runs per step**, which is a large efficiency dividend.
- **Replan** (a conditional edge): after a step, look at the result. Is it done? Does the plan still hold? If reality delivered a surprise, update the plan and continue. It is exactly this ability to change the plan that rescues a rigid plan that may have been wrong from the start.

Two "think harder" variants: **reflection (Reflexion)**, where the agent critiques its own output and revises it, suited to writing and code that need polishing; and **tree search (Tree of Thoughts / LATS)**, exploring several branches at once, scoring, and backtracking, suited to hard reasoning with dead ends, the most powerful and the most expensive.

The practical rule: match the weapon to the difficulty. Simple tool calls, use ReAct; long structured tasks, use Plan-and-Execute with replanning; output that needs polishing, add reflection; hard search, use tree search. Running tree search for one simple lookup is just burning money.

## Layer four: multi-agent

![Multi-agent topologies](../images/ag_multi_agent.png)

A single agent with 30 tools and one giant prompt performs worse: it picks the wrong tool, its context bloats, and one "persona" has to do everything. The reason for splitting into multiple agents is the same as for splitting code into modules: **specialization and isolation**.

**The supervisor topology (the most common)**: the supervisor is a routing node whose conditional edges dispatch tasks to specialized sub-agents; each sub-agent is a subgraph with its own loop and tools. The key design point is that **each sub-agent's context is isolated**: the long source documents it read internally and the logs from the 20 test runs it did never flow into the supervisor's context. The supervisor sees only summaries and stays clean.

The essence of multi-agent is **context isolation plus specialization**, not "more agents means smarter".

Costs and pitfalls: summarization loses detail (communication bandwidth is a real loss); errors propagate (a sub-agent returns a wrong result and the supervisor accepts it wholesale); coordination overhead is high, latency grows, and debugging is hard. The iron rule: **if one agent can do the job well, don't split.** The signals for splitting are too many tools to choose among, a need for different specialties, and a context that is blowing up.

Other topologies: a **pipeline** (a fixed sequence of handoffs, good for staged output), a **network with handoffs** (peer agents handing off dynamically, flexible but hard to control), and **debate/ensemble** (several independent solutions critiquing and voting, trading redundancy for reliability at multiplied cost).

## The overall map: when to use what

![The agent decision map](../images/ag_decision_map.png)

Start from the simplest possible ReAct agent, and add a layer only when you actually hit the corresponding problem:

- Need control, approval, pause/resume, loop prevention → build it as a graph / state machine
- Long tasks, many steps, prone to drift → planning plus replanning
- Output needs polishing → add reflection
- Hard reasoning with dead ends → tree search
- Too many tools, different specialties needed, context blowing up → multi-agent supervisor topology
- Extremely high reliability requirements and enough budget → debate / ensemble

Two interfaces run through every layer: **memory** (Part 7) plugs into State, and **tools** (layer one of this chapter) plug in through schemas.

The general principle: every layer you add costs money, latency, and debuggability, so the mechanism has to match the difficulty of the task. **Knowing whether to add a layer matters more than knowing how to build one.**

## Key takeaways

- ReAct interleaves reasoning and acting; tool calling has four steps; the model only generates text and the runtime executes.
- The graph model uses State/Node/Edge to turn control flow into data; the conditional edge is the termination condition; State can be checkpointed.
- Planning decomposes before executing, with replanning to correct course; reflection and tree search are more expensive upgrades.
- The essence of multi-agent is context isolation and specialization; if one agent suffices, don't split.
- Start with the simplest thing and add layers only when you hit a concrete problem.

## Question to think about

In Plan-and-Execute, why is "the strongest model for the Planner, a cheap small model for the Executor" usually such a good deal? And why does "State can be checkpointed" enable both human approval and rerunning from an arbitrary step?

---

*That completes the series. From tokens to vectors, from attention to generation, from training to inference systems, from RAG to memory and agent architectures: one complete chain from bottom to top. You can now trace any real AI product from the user's question all the way down to matrix multiplication, and back up to the answer.*
