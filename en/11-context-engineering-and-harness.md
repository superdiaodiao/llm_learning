# 11 · Context Engineering and the Agent Harness: Skills, Hooks, MCP, and Evaluation

> [中文版](../11-context-engineering-and-harness.md) · English

> Part 11 of the series *LLMs from the Ground Up*. "Harness", "skills", "MCP" are the hottest words of the moment; this part puts them back into one unified frame: **Agent = Model + Harness**. The model is the engine, the harness is the whole car; context engineering is that car's operating system, evaluation is its dashboard.

## The frame first: Agent = Model + Harness

The model does exactly one thing: read the context, generate text. What turns it into an agent that gets work done is everything outside it: the loop, tool execution, what goes into the context each turn, memory reads and writes, checks before and after tool calls, permission guardrails, spawning sub-agents, error handling, logging. That whole set is the **harness**.

It became hot suddenly because the industry noticed: **the same model in a different harness has wildly different capability.** Improvement in the models themselves has slowed, while the room to improve the harness has turned out to be large. The loop and state machine (Part 8), tool calling (Part 8), memory (Part 7), planning and multi-agent (Part 8) covered earlier are all harness components. This part fills in the rest: context assembly, skills, hooks, MCP, evaluation.

## One: context engineering, the window is a scarce resource

![Context window budget](../images/ce_window_budget.png)

### Why "prompt engineering" became "context engineering"

In the single-turn era, one carefully written prompt was enough. With agents, the context is **assembled dynamically by a program every turn**: system prompt, tool table, retrieval results, memory, history, tool returns... seven or eight sources competing for one finite window. The craft shifted from "wording a paragraph" to "designing an assembly pipeline".

### The biggest enemy is tool output

A user message is typically a few dozen tokens, but one grep returns thousands of lines, a log runs to tens of thousands of tokens, an API response is mostly useless fields. Without compression, a few turns blow the window; worse, the key information gets **buried**: the model's attention is finite, and the more is crammed in, the less each item gets. So the main battleground for compression is tool results: summarize or trim before they enter the window, keep the original outside, and hand the model a handle it can "fetch when needed". When a conversation runs long, compress the early history into a summary (compaction).

### Five assembly principles

1. **Progressive disclosure.** Do not stuff every instruction into the system prompt. Build an index and load what is needed when it is needed; skills are this idea.
2. **Compression and truncation.** Focus on tool results and over-long history.
3. **Position and attention.** The model is most sensitive to the beginning and the end and tends to "lose" the middle (lost in the middle). Key rules go at the start, the current task at the end, large blocks of material in the middle.
4. **Isolation.** Hand the dirty work to a sub-agent, let it dig through raw material in its own window, and bring back only the summary. The main context stays clean.
5. **Cache alignment.** Recall Parts 3 and 5: the KV cache caches a prefix. Prompt caching at the API layer is **reusing the KV cache of a prefix across requests**, on the condition that the prefix is identical to the character. So the system prompt and tool table go first and stay stable; timestamps and random ids go later. Change the prefix and the whole cache is invalidated, and a long conversation costs several times more. This is a textbook case of applying the underlying principle directly to engineering.

## Two: the harness's three programmable points

![Skills, Hooks, MCP](../images/ce_skills_hooks_mcp.png)

### Skills: turning "experience" into files

A skill is a folder: `SKILL.md` (a name, a one-line "when to use", and a body of step-by-step how-to) plus optional scripts, templates, and reference docs. The runtime mechanism is progressive disclosure: the harness puts every skill's one-line description into the context as an index, and loads the full text of one only when the task matches it.

Why did it take off? Because **experience that used to be locked in prompts and in people's heads has become files that can be versioned, shared, and reused**; that directly spawned a skills ecosystem. Relation to Part 7: skills are explicit, distributable **procedural memory**.

Easiest confusion, with tools: **tools give hands (functions that can be called), skills give experience (a manual on how to do things)**. The manual may call tools.

### Hooks: deterministic discipline

There is an interception point before and after each tool call. `PreToolUse` can validate arguments, block dangerous commands, require human approval, rewrite arguments; `PostToolUse` can compress a large output into a summary before it is fed back, redact, log.

The key: **hooks are code, not prompt.** Write "please don't delete files" in the system prompt and the model may forget or be talked around; a hook executes one hundred percent of the time. This is the fundamental reason a harness is more reliable than a prompt: **what should be guaranteed by code, do not leave to the model's good behaviour.**

### MCP: a uniform interface for tools

Without a standard, every agent framework writes its own adapter for every tool (N frameworks × M tools); with MCP (Model Context Protocol), a tool provider writes one "server" and the agent side implements one "client" (N + M). An MCP server exposes a set of tools each with `name / description / parameter schema`, which is exactly where step ① of Part 8's tool calling, the "tool table", comes from. It can also expose resources (readable data) and prompt templates. It took off because it solves an ecosystem problem, not a technical puzzle.

### How the three fit together

Take "file an issue on a repo": the `github-issue` skill in the index matches and its manual loads (check for duplicates first, write to the template, how to label); the `search_issues` / `create_issue` the manual calls come from the MCP GitHub server; `create_issue` is a public write, so a `PreToolUse` hook stops it and asks for human confirmation, and `PostToolUse` writes an audit log line. **Skills give experience, MCP gives hands, Hooks give discipline.** All three live outside the model; all three are deterministic engineering.

## Three: evaluation, how do you know an agent got better or worse

![Agent evaluation](../images/ce_evaluation.png)

### What to evaluate: three levels

- **Single step**: was the right tool chosen this time, were the arguments right, is the output format valid. Precisely decidable, and cheapest.
- **Trajectory**: was the whole path reasonable, did it loop, repeat, or call tools it should not have. Look at node transitions in the graph model.
- **Outcome**: was the task ultimately completed, is the answer right, is it good. Most important, and hardest to judge.

### How to score: choose by "can it be decided precisely"

**Whatever can be decided precisely, never hand to an LLM judge.** Tool choice, arguments, format, classification, extraction, arithmetic: anything with a unique answer gets exact matching against a gold standard, which is cheap, stable, and automatable. Many teams reach for LLM scoring first, and the judge itself turns out unstable, making the evaluation less reliable than what it evaluates. Keep the LLM judge for genuinely open-ended answers, and give it an **explicit rubric** to score item by item, then calibrate its biases with human spot checks (judges generally favour longer answers and ones in their own house style).

**Comparison is far more stable than scoring.** Giving one answer a 7 versus an 8 swings a lot, but "is A or B better" is far more consistent. For version comparisons prefer pairwise comparison, which is exactly the form of Part 10's DPO preference data: evaluation and alignment use the same signal, one to measure, one to train.

### Wire it into the iteration loop

Change a prompt, swap a skill, add a tool → run the regression evaluation set → see which cases got better or worse → merge or roll back. Like unit tests. Two practical principles:

- **The evaluation set grows from real failures.** Do not start by fabricating thousands of synthetic cases. Every time a bad example appears, freeze it into a regression case; a few dozen real cases beat thousands of synthetic ones.
- **Observability is the precondition.** Record every node transition and every tool call as a trace, so a bad outcome can be traced back to the step where it went wrong.

**Changing without testing is gambling.** Of everything in building AI applications, this is the least often done seriously and the one that opens the widest gap.

## Key takeaways

- Agent = Model + Harness; the same model in a different harness has wildly different capability, which is why harness engineering has become the focus.
- Context is a scarce resource: progressive disclosure, compress tool results, mind position, isolate dirty work, keep the prefix stable to hit the cache.
- Skills are distributable procedural memory, Hooks are deterministic guardrails, MCP is the uniform interface for tools.
- Evaluation has three levels, single step / trajectory / outcome; what can be decided precisely does not go to an LLM judge; comparison beats scoring; the evaluation set grows from real failures and is wired into the iteration loop.

## Question to think about

Why would "putting a timestamp at the start of the system prompt" multiply the API cost of a long conversation several times over? (Hint: recall what Part 3's KV cache caches.)

---

*This part deliberately leaves out some currently hot new terms that have no stable definition yet, as well as tricks like "use a particular tone to save tokens"; they carry no transferable principle, and writing them into a tutorial only guarantees it goes stale.*
