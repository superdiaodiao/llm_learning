# 03 · Generation: From Logits to Text

> [中文版](../03-generation-logits-to-text.md) · English

> Part 3 of the series *LLMs from the Ground Up*. The first two chapters covered how text becomes vectors and how attention processes those vectors over and over. This chapter covers the last link: how the model "spits out the next token", and why a KV cache is needed.

## From vector to probability

![From the final vector to the next token](../images/m3_logits_sampling.png)

After dozens of blocks, every position holds a vector that "understands its context". Turning it into a word takes two steps.

**lm_head: vector → vocabulary scores.** Look at this line in `LlamaForCausalLM`:

```python
self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)
```

It projects the last layer's output vector (say 4096-dimensional) into **a list of scores as long as the vocabulary**: about 128,000 of them, one per token. This list of scores is called the **logits**.

An elegant detail: `_tied_weights_keys` in the code ties `lm_head.weight` and `embed_tokens.weight` to the same matrix. In other words, the "text → vector" lookup table from Part 1 is reused in reverse for "vector → text". One table does both jobs.

**softmax: scores → probabilities.** Logits are just scores of arbitrary magnitude; softmax squashes them into a probability distribution summing to 1: "the next token is `mat` with 62%, `floor` with 20%...".

## Three sampling knobs

Given a probability distribution, how do you pick a token? Three common knobs:

- **temperature** adjusts how peaked the distribution is. Low temperature sharpens it so you almost always pick the most likely token (deterministic, conservative, prone to repetition); high temperature flattens it so rarer tokens get picked more often (diverse, creative, more likely to go off the rails). `temperature=0` degenerates to always picking the maximum (greedy).
- **top-k** only considers the k highest-scoring tokens and throws the rest away, blocking absurd tokens from the long tail.
- **top-p (nucleus sampling)** accumulates probability from highest to lowest and cuts off once it reaches p (say 0.9). The number of candidates adapts to how confident the model is: when it is sure, only a few remain; when it is unsure, the set widens automatically.

An important distinction: **none of this sampling logic lives in the model file.** The model is only responsible for producing logits; picking the token is done by `.generate()` (`GenerationMixin`). The model gives probabilities, the sampling strategy decides. The two are decoupled.

## Autoregression: one token at a time

Pick a token → append it to the input → run the whole model again → pick the next one. One token at a time, until the end-of-sequence token is generated. This is "autoregressive generation": at each step the model predicts a single token and feeds its own output back in as the next input.

## KV cache: don't recompute what hasn't changed

![Why the KV cache is necessary](../images/m3_kv_cache.png)

Autoregression has a built-in waste. Each new token requires another pass through the model; the naive approach recomputes the K and V of every previous token at every step, but the K/V of those old tokens **haven't changed at all**. Pure waste, and the waste grows quadratically with length, so long texts get slower and slower.

The KV cache's solution: **compute each token's K and V once and store them.** Every subsequent step then does just three things: compute Q/K/V for the new token, append the new K/V to the cache, and let the new token's Q attend to all the Ks in the cache. In the real code this is `past_key_values.update(key_states, value_states, layer_idx)` inside attention.

Why cache K/V but not Q? Because **Q is only useful in the one moment when "the current token looks around"**; once used it has no further purpose. K/V, on the other hand, are the information each token "offers to others", and they are fetched again at every later step.

## A thread left hanging

The KV cache makes long-text generation feasible, but it keeps growing and eats a lot of GPU memory. Managing this cache efficiently is the central problem of inference engines like vLLM. Part 5 explains how PagedAttention solves it.

## Three chapters, one line

At this point a complete main line is in place: **text → vectors (Part 1) → repeated processing by attention (Part 2) → projection to probabilities, sampling, and looping generation (Part 3)**. You can now explain a large language model from input to output, start to finish.

## Key takeaways

- `lm_head` projects the vector into vocabulary scores (logits), softmax turns them into probabilities; the output matrix often shares the same table as the input embedding.
- temperature adjusts sharpness, top-k truncates by count, top-p truncates by cumulative probability; sampling lives outside the model.
- Autoregression generates one token at a time; the KV cache stores old tokens' K/V to avoid quadratic recomputation.

## Question to think about

If you want the model to produce reproducible, stable, factual answers, how should you set temperature / top-k / top-p? What is the cost of setting them that way?
