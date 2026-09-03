# llm_learning · LLMs from the Ground Up

> [中文版](../README.md) · English

> One complete chain from the bottom to the top: how text becomes vectors → how attention understands context → how the model generates → where the weights come from → how LLMs are served efficiently → how RAG and agents are built → how memory systems and agent architectures are designed.
>
> Every chapter uses the **real source code** of top open-source projects as its textbook (transformers, vLLM, LlamaIndex, mem0, LangGraph, peft/trl), with diagrams, explaining the mechanism rather than piling up jargon. Written for readers with an engineering background who want a systematic understanding of modern AI.

## Table of contents

| # | Chapter | In one line |
|---|---|---|
| 01 | [Tokens and Embeddings: How Text Becomes Numbers](01-tokens-and-embeddings.md) | The model only handles vectors; tokenization, lookup, semantic space |
| 02 | [Attention and the Transformer: How the Model Understands Context](02-attention-and-transformer.md) | Q/K/V, positional encoding, multi-head, blocks and stacking |
| 03 | [Generation: From Logits to Text](03-generation-logits-to-text.md) | lm_head, the three sampling knobs, autoregression, KV cache |
| 04 | [Training and Fine-tuning: Where the Weights Come From](04-training-and-finetuning.md) | Gradient descent, pre-training, LoRA, alignment |
| 05 | [Inference Systems: How LLMs Are Served Efficiently](05-inference-systems.md) | PagedAttention, continuous batching, quantization |
| 06 | [The Application Layer: RAG and Agents](06-rag-and-agents.md) | Application map, RAG pipeline, reranking, the agent loop |
| 07 | [AI Memory Systems: Agents That Remember Across Sessions](07-ai-memory-systems.md) | Read/write loop, memory types, mem0 source and prompts |
| 08 | [Agent Architectures in Depth: From ReAct to Multi-agent](08-agent-architectures.md) | ReAct, graphs/state machines, planning, multi-agent, decision map |
| 09 | [In Practice: From Reading Code to Opening PRs in Top Projects](09-contributing-in-practice.md) | Pattern-hunting methodology + two real cases (LlamaIndex / mem0) |

## The main line in one picture

```
Text ──tokenize/lookup──▶ Vectors ──attention × N layers──▶ Context-aware vectors ──lm_head/softmax/sampling──▶ Next token ──loop──▶ Text
                                        ▲                                                                       │
                     Training: predict next token → compute loss → gradient descent (04)                        │
                     Serving: PagedAttention / continuous batching / quantization (05)                           │
                                                                                                                ▼
                 Applications: RAG adds knowledge · Agents add actions · Memory adds recall (06/07/08)
```

## How to read

- Read in order. 01–03 are the main line from input → processing → output, 04–05 cover where the model comes from and how it is served, 06 onward turns to the application layer, and 07/08 are two deep dives.
- Every chapter ends with a **question to think about**; the answer is usually picked up in the next chapter.
- 09 is a bonus chapter about method rather than theory: how to find bugs, file issues, and open PRs yourself in AI projects with tens of thousands of stars. All issue/PR numbers are public records.

## Images

Every figure in `images/` is provided as both `.svg` (vector) and `.png` (bitmap). The chapters reference the PNGs by relative path so they preview directly on GitHub.

## Real code used as textbooks

| Project | File / module | Chapters |
|---|---|---|
| transformers | `src/transformers/models/llama/modeling_llama.py` | 01–03 |
| peft / trl | LoRA layer implementation, SFT / DPO trainers | 04 |
| vLLM | `BlockManager`, `Scheduler` | 05 |
| LlamaIndex | retriever / query engine / node postprocessor | 06 |
| mem0 | `mem0/memory/main.py`, `mem0/configs/prompts.py` | 07 |
| LangGraph | `StateGraph` and conditional edges | 08 |

## Planned

- Fine-tuning in practice: runnable LoRA / DPO code and pitfalls (in progress)
- Evaluation and context engineering
- Multimodal and diffusion models

## License

Text and images are licensed under [CC BY-NC-SA 4.0](../LICENSE): free to share, adapt, and use for learning, with attribution, non-commercially, and under the same license. Quoted third-party source snippets follow their own open-source licenses (all Apache-2.0 / MIT).

Issues pointing out mistakes or suggesting additions are welcome.
