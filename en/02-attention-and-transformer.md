# 02 · Attention and the Transformer: How the Model "Understands" Context

> [中文版](../02-attention-and-transformer.md) · English

> Part 2 of the series *LLMs from the Ground Up*. The previous chapter ended with a cliffhanger: two identical `the`s come out of the lookup with identical vectors, so what now? This chapter gives the answer, using the real `modeling_llama.py` from HuggingFace transformers as the textbook.

## Start with something surprising

Llama, a large model running inside countless products, has a core implementation, `modeling_llama.py`, of only a few hundred lines. And the **entire math** of attention is just four of them:

```python
attn_weights = torch.matmul(query, key_states.transpose(2, 3)) * scaling   # ① Q·Kᵀ scores
attn_weights = attn_weights + attention_mask                               # ② causal mask
attn_weights = nn.functional.softmax(attn_weights, dim=-1, ...)            # ③ scores → weights
attn_output  = torch.matmul(attn_weights, value_states)                    # ④ weights·V, weighted blend
```

This chapter explains these four lines thoroughly.

## Self-attention: every word looks around

![One self-attention computation](../images/m2_self_attention.png)

Each word's vector first passes through three linear layers, `q_proj`, `k_proj`, `v_proj`, which project it into three roles:

- **Query (Q)**: what I am looking for.
- **Key (K)**: the label I show to others.
- **Value (V)**: the content I can actually contribute.

A library analogy: your search term is the Query, each book's label is its Key, and the dot product of the two is the relevance; finally you blend the contents of the books (Values) according to relevance.

Take `cat`. Its Query is dotted with the Key of every word in the sentence, giving a set of relevance scores; softmax squashes them into weights that sum to 1; then a weighted sum over all the words' Values gives `cat`'s new vector. In that new vector, `cat` is still mostly itself, but it has absorbed a bit of `the` and a good deal of `sat`: it now "knows it is sitting".

All three projection matrices are learned. The model figures out on its own what information to put into Q, K, and V.

### The causal mask

When generating text, each word may only look at the words to its left; it must not peek at a future that hasn't been generated yet. This is done by adding negative infinity to the scores of "future positions" before the softmax, so after the softmax those positions get weight 0. That is what `attention_mask` on line ② does.

## Positional encoding: the answer to the cliffhanger

Back to the two `the`s. Look at this line in `LlamaAttention.forward`:

```python
query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)
```

This is **RoPE (Rotary Position Embedding)**. It "rotates" the Q and K vectors by an angle that depends on the token's position: position 1 and position 5 are rotated by different angles. So the two originally identical `the`s each carry their own positional information when attention is computed. Add the fact that attention blends each word with **different neighbors**, and the two `the`s come out completely different.

The division of labor in one sentence: **the lookup gives the dictionary meaning, RoPE gives position, attention gives contextual meaning.**

## Multi-head: several viewpoints at once

The output of `q_proj` is reshaped into `num_heads × head_dim`: the same attention mechanism runs many copies in parallel, each copy (a "head") computing in its own subspace. After training, different heads spontaneously specialize: some track grammatical relations, some track pronoun references, some track long-range dependencies. Finally `o_proj` stitches all the heads' results back together. **One head is one viewpoint; multiple heads are multiple viewpoints looking at once.**

## Zooming out to the block and the whole model

![Inside a decoder block, and the stack](../images/m2_decoder_block_stack.png)

### A block does two things: communicate, then digest

`LlamaDecoderLayer` wraps attention in a standard structure:

- **Attention = horizontal communication between words.** Each word looks at the others and absorbs context.
- **MLP = each word processing on its own, vertically.** After communicating, each word takes its updated vector and passes it through a feed-forward network alone, to "digest". No communication between words happens in this step.

One layer = one round of "first look at each other, then think individually". The whole transformer is these two moves alternating over and over.

### Residuals: a bypass highway

The line `hidden_states = residual + hidden_states` in the code means a layer's output is not a rewrite from scratch, but `original value + the delta this layer computed`. There are two reasons for this design. First, **no information is lost**: even if a layer computes nothing useful, the original value passes through untouched. Second, **it stays trainable**: in a network dozens of layers deep, without this bypass the gradient vanishes by the time it reaches the bottom layers; the residual gives the gradient a direct route.

Each layer only has to learn "what to add on top of what's already there", not "rebuild everything from zero".

### Why stack dozens of layers

The key: **each layer's input is a half-finished product from the layer below.** At layer 1, `bank` can only see its raw neighbors; at layer 2, the neighbors `bank` sees have already had context kneaded into them by layer 1. The higher you go, the richer and more abstract the context concentrated in each word's vector. Like an assembly line: shallow stations recognize words and phrases, deep stations assemble meaning and logic on top of the half-finished parts. Llama-3-8B stacks 32 layers; larger models stack over a hundred.

What `LlamaModel` does, in one sentence: lookup → N stacked blocks → final normalization.

## Key takeaways

- The core of attention is Q/K/V: match Query against Key for relevance, blend Values by weight.
- RoPE injects position, attention injects context; together they give the same word different representations in different positions.
- Multi-head = parallel viewpoints; a block = attention (communicate) + MLP (digest) + residual (bypass).
- Stacking layers means processing half-finished products layer by layer, rising from "recognizing words" to "understanding".

## Question to think about

If you removed the residual connections and kept only attention and MLP, what would go wrong in a deep network? (Hint: think from two angles, "information flow" and "gradient flow".)
