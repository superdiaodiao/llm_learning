# 01 · Tokens and Embeddings: How Text Becomes Numbers

> [中文版](../01-tokens-and-embeddings.md) · English

> Part 1 of the series *LLMs from the Ground Up*. This chapter answers the most basic question, and the one most often skipped: the model doesn't understand text at all, so what is it actually processing?

## The conclusion first

From start to finish, a large language model only does math on **vectors**. Text is just the outermost input/output "skin". The very first thing that happens to a sentence entering the model is that it gets cut into tokens, turned into numbers, and then into vectors. Once you understand this step, attention, generation, and training all have something to stand on.

![How text becomes vectors](../images/m1_tokens_embeddings.png)

## Step one: tokenization

The model does not process text by character or by word, but by **token**, a sub-word unit that sits between the two. Take BPE (Byte Pair Encoding), the mainstream family of tokenizers: common words are kept whole (`the`), rare words are split into sub-word pieces (`tokenization` → `token` + `ization`).

Why this compromise? A vocabulary of whole words explodes (millions of entries, and it still misses unseen words); a vocabulary of single letters makes sequences too long and each symbol carries too little information. Sub-words are the sweet spot: the vocabulary stays at tens of thousands to a hundred-odd thousand entries, yet it can express any rare word.

Each token maps to an integer id in the vocabulary. After the tokenizer, `"the cat sat"` becomes a list of numbers, something like `[1996, 4937, 2938]`.

## Step two: lookup (embedding)

With ids in hand, the next step is **a table lookup**. This table is the embedding matrix, with shape `[vocab_size, hidden_dim]`; for Llama 3 that is roughly `[128000, 4096]`. The id is the row number: pull out that row and you have the token's vector, 4096 floating-point numbers.

That's all there is to it. In real code, this step is `LlamaModel.embed_tokens`, which is essentially an `nn.Embedding` lookup table.

## The key insight: this table is *learned*

At the start of training, the embedding matrix is random numbers; every word's vector is garbage. During training, the model keeps adjusting these numbers to serve the goal of "predict the next token", and gradually the regularities that are useful for prediction emerge: **words with similar meanings end up with similar vectors**.

This is a by-product of training, not something designed by hand. Yet it has astonishing geometric structure. The classic example is `king - man + woman ≈ queen`: vector arithmetic ends up matching semantic relations. In the figure, the "royalty" cluster and the "animals" cluster sit far apart while words within a cluster sit close together, for exactly this reason.

"Similar" is measured by the angle between vectors (cosine similarity). Remember this, because it is exactly what RAG retrieval computes (see Part 6).

## Two things that are easy to confuse

**Meaning ≠ spelling.** `cat` and `kitten` are spelled very differently, yet their vectors are close. That's because the vectors come from "what contexts does this word appear in", not from which letters it is made of. The model does see spelling indirectly (through sub-words), but "meaning" comes entirely from that learned table.

**Token-level vs document-level embeddings.** This chapter is about token-level embeddings: one vector per token, living inside the model. RAG retrieval uses **document-level** embeddings: a whole passage compressed into a single vector. Different granularity, same core idea.

## A cliffhanger

`"the cat sat on the mat"` contains two `the`s. Their lookup results are **identical**, because the lookup only knows the id; it has no idea which position the word is in or what surrounds it. This causes two problems:

- **Position is lost.** "Dog bites man" and "man bites dog" use the same words; the order changes everything, but a pure lookup can't tell them apart.
- **Context is lost.** The `bank` in "river bank" and the `bank` in "bank account" share one id and one vector.

So the lookup only gives the "dictionary meaning": a raw vector detached from context and position. What turns it into a "contextual meaning" is the subject of the next chapter: attention and positional encoding.

## Key takeaways

- The model only handles vectors; text is first cut into tokens, then looked up into vectors.
- The embedding matrix is a lookup table learned during training; similar words have similar vectors as a by-product of optimization.
- Similarity is measured by cosine (angle), and that is exactly what RAG retrieval computes.
- The lookup gives context-free vectors; position and context have to be added by attention.

## Question to think about

Why are the vectors for `cat` and `kitten` so close even though they are spelled differently? (Hint: think about what signal the embeddings are learned from.)
