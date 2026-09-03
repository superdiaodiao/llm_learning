# 07 · AI Memory Systems: Agents That Remember Across Sessions

> [中文版](../07-ai-memory-systems.md) · English

> Part 7 of the series *LLMs from the Ground Up*. RAG gives the model external knowledge, agents give it the ability to act, and memory gives it persistent recall across sessions. This chapter uses the real source code of mem0, a popular open-source memory layer, as its textbook.

## Why memory is needed

The model is stateless: the weights are frozen, the context window is finite, and every conversation starts over. It cannot "remember" the preference you mentioned in the last conversation, and in a long conversation the early parts get pushed out of the window. A memory system is persistent recall bolted on outside the model.

## How a memory system works: RAG plus a write policy

![The read/write loop of an AI memory system](../images/mem_system_loop.png)

**The read side is just RAG.** A new message comes in, relevant memories are retrieved semantically from long-term storage, injected into the context, and then the model generates.

**The write side is the new part.** After each interaction, an LLM extracts the points worth keeping from the conversation ("the user prefers a window seat") and writes them back to the store. And not by blindly appending, but with an **add / update / delete** policy: if the user changed their mind, update; if something is stale, delete. This "extraction plus conflict resolution" is the hard core of a memory system.

### Types of memory

- **Working memory**: the context window itself (this conversation, fast but small, gets pushed out).
- **Episodic memory**: things that happened in the past.
- **Semantic memory**: stable facts about the user or the world (name, preferences, employer).
- **Procedural memory**: learned methods and skills.

### Two tiers of memory, like an OS's RAM and disk

Working memory is like RAM, long-term memory like disk. MemGPT's insight was to let the model decide for itself what to page into context and what to write back out, the way an operating system pages memory. It is the same wisdom as PagedAttention in Part 5, applied at a different layer.

### Why it is still an active research area

The difficulty is all in the judgment calls: what to remember (remember everything and it's noise, remember too little and you miss things), how to resolve conflicts (old and new preferences clash), how to forget (old memories decaying over time), and retrieval quality (semantic vs exact). None of these have standard answers.

## mem0's write pipeline (real source code)

mem0's `_add_to_vector_store` is a staged pipeline that turns the concepts above into code:

**Read first, then decide how to write.** Before writing, it runs a vector search to pull up existing related memories:

```python
query_embedding = self.embedding_model.embed(parsed_messages, "search")
existing_results = self.vector_store.search(query=..., vectors=query_embedding, top_k=10, ...)
```

Writing is "context-aware": you have to know what has already been recorded before you can judge which parts of a new message are worth keeping and which are duplicates.

**Let the LLM decide what is worth remembering.** Existing memories, the new message, and the recent conversation are fed to the LLM together, and an extraction prompt makes it produce the points worth keeping. The judgment of "what to remember" is delegated to the model, not hard-coded as rules.

A few engineering details worth learning from:

- **Id mapping to prevent hallucination**: the real ids of memories are UUIDs, and showing them to the LLM directly invites mistakes and invented ids. The code temporarily maps UUIDs to `"0" "1" "2"` for the model, then maps the results back.
- **Hash-based deduplication**: an md5 is computed for each piece of text to be stored, and if it was stored before it is skipped. The cheapest possible way to block exact duplicates.
- **Audit history**: every memory operation writes a history record with `event: ADD/UPDATE/DELETE` and the old and new values. An "update" doesn't lose the old information, and a "delete" is a soft delete that stays on file.
- **A fast lane and a slow lane**: if you don't want to pay an LLM for smart extraction, there is a "dumb" path that stores the raw messages directly.

## The life of a memory: two design philosophies

![The mem0 memory lifecycle](../images/mem_mem0_lifecycle.png)

The user first says "I usually use Python", and later says "I've switched to Rust". How should that be handled?

- **The classic design (UPDATE, edit in place)**: change the content under the same memory_id, keep `created_at`, and push the old value into history. Overwrite, keep one record.
- **mem0 V3's new design (additive, append and link)**: add a new record, "moved from Python to Rust", pointing back to the old one via `linked_memory_ids`. Accumulate rather than overwrite, gradually building a memory graph.

The two philosophies have different trade-offs, which shows that memory-system design is still evolving. The thread running through both is an **append-only history ledger**: adds, updates, and deletes all leave a trace, so you can always trace how a memory evolved and why it disappeared.

Two more layers sit underneath: **hybrid retrieval** (vectors plus BM25 keywords, storing both embeddings and lemmatized text) and an **entity graph** (entities extracted with spaCy into a separate `_entities` collection, supporting cross-memory retrieval).

## The "brain" of a memory system is a prompt

All of mem0's intelligence in judging "what is worth remembering" is not an algorithm but a prompt of several thousand words in natural language, fed to an ordinary LLM. This is a counterintuitive but important realization: **in modern AI systems, complex judgment is often encoded in clearly written prose rather than in code.** Memory quality is roughly equal to prompt quality.

That prompt is essentially a manual of lessons learned, each rule a pothole someone stepped in:

- **When in doubt, record it**: better to record too much (deduplication downstream will handle it) than to miss something. It specifically warns against "first-topic dominance", where the model records the first topic in great detail and skips the rest as filler.
- **Hold on to specifics, don't generalize**: `Ferrari 488 GTB` must not become "sports car", because once generalized the user can no longer find it.
- **Don't distort the original meaning**: "wasn't asleep until 2" is not "slept until 2". Recording something wrong is worse than not recording it.
- **Ground time references**: "last week" must be converted into an absolute date, because "went to Paris last week" is useless six months later.
- **No invention, no guessing**: you may not infer gender or age from a name; every detail needs a source.
- **Examples beat lectures**: most of the prompt is "input → expected output" examples (few-shot).

The part of a memory system with the highest AI content is exactly this prompt, together with the extraction, deduplication, and linking logic.

## Key takeaways

- Memory = reading (RAG retrieval) + writing (LLM extraction + deduplication + add/update/delete + history trail).
- Working memory is the context window, long-term memory is external storage; MemGPT manages both with the OS paging idea.
- mem0 reads before writing, maps ids to prevent hallucination, deduplicates by hash, and keeps an append-only ledger; V3 shifts from "update in place" to "append and link".
- The judgment of "what to remember" is encoded in a prompt that closes off the model's failure modes one by one.

## Question to think about

Why does mem0 replace UUIDs with small integers like `"0" "1" "2"` when handing existing memories to the LLM for judgment?

---

*Related code: `mem0/memory/main.py` (write pipeline and add/update/delete), `mem0/configs/prompts.py` (extraction prompt).*
