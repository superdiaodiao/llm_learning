# 05 · Inference Systems: How LLMs Are Served Efficiently

> [中文版](../05-inference-systems.md) · English

> Part 5 of the series *LLMs from the Ground Up*. Part 3 left a thread hanging: the KV cache eats a lot of GPU memory. This chapter gives the industry's answer. The textbook is vLLM, the de facto standard inference engine, and its three levers: PagedAttention, continuous batching, and quantization.

## A model that "runs" is far from a model that "serves"

A model running on your GPU and a model serving hundreds or thousands of people at once, cheaply, are two different things. Three problems sit in between: how not to waste memory, how not to leave the GPU idle, and how to trade precision for throughput. The value of an inference engine like vLLM is that it does these three things well.

## Lever one: PagedAttention, managing memory

![PagedAttention](../images/m5_paged_attention.png)

The naive KV cache approach reserves a large **contiguous** block of GPU memory per request, sized for the maximum possible length. The problem is that actual usage is much smaller, leaving a lot of blank space, and it fragments: total free memory may be enough while no new request fits because the free space is cut into pieces.

PagedAttention borrows the operating system's idea of "virtual memory paging": cut the KV cache into fixed-size blocks, allocate them on demand, allow them to be non-contiguous, and keep a **block table** recording "logical block N → which physical slot". Reads follow the table to find blocks, so logically it is still a contiguous sequence. Fragmentation drops to nearly zero, and the number of requests a single GPU can serve concurrently multiplies. The real code is vLLM's `BlockManager`.

In one sentence: replace "reserve one large contiguous block" with "allocate small blocks dynamically plus a mapping table", and waste falls from over half to almost nothing.

## Lever two: continuous batching, managing scheduling

![Static batching vs continuous batching](../images/m5_continuous_batching.png)

**Static batching** gathers requests into a batch and runs them together. But each output has a different length, so a slot that finishes early can only sit idle until the slowest one is done, leaving the GPU largely idle (the dashed cells in the upper half of the figure).

**Continuous batching** shrinks the scheduling granularity from "a whole batch" to "each step": after every generated step, finished sequences are evicted and waiting requests are slotted in, so the GPU always has work. Throughput can multiply several times over. The real code is vLLM's `Scheduler`.

These two innovations are a natural pair: precisely because the KV cache is paged, dynamically "slotting in / evicting" becomes cheap, just allocating or freeing a few blocks. Otherwise, swapping large contiguous blocks in and out would be extremely expensive.

## Lever three: quantization, managing precision

Model weights are usually fp16 (2 bytes per number). Quantization compresses them to int8 (1 byte) or even int4 (half a byte): memory usage drops 2–4×, and inference gets faster too (large-model inference is mostly bottlenecked on moving data), at the cost of a little precision. The KV cache itself can be quantized as well. Common methods include GPTQ and AWQ. This is a trade: **a little quality for throughput and cost**.

## The three levers together

PagedAttention manages **memory**, continuous batching manages **scheduling**, quantization manages **precision**. Together they turn a model that "runs" into a system that serves high concurrency at low cost. This is also one of the areas where the industry is shortest on people.

## Key takeaways

- The naive KV cache reserves large contiguous blocks, causing heavy waste and fragmentation; PagedAttention solves it with paging plus a block table.
- Static batching leaves the GPU idle; continuous batching schedules per step and refills as soon as a slot frees.
- Quantization trades lower precision for memory and speed.
- Paging makes dynamic scheduling cheap; the two reinforce each other.

## Question to think about

Why does PagedAttention make continuous batching easier? (Hint: think about what kind of memory management "dynamically slotting in / evicting requests" requires.)
