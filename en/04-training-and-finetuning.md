# 04 · Training and Fine-tuning: Where the Weights Come From

> [中文版](../04-training-and-finetuning.md) · English

> Part 4 of the series *LLMs from the Ground Up*. The first three chapters explained how the model computes; this one explains where those weights come from. Pre-training, fine-tuning, LoRA, alignment: they are all variants of one and the same move.

## What is "learning", exactly?

Many matrices have shown up so far: the embedding lookup table, each layer's `q_proj`/`k_proj`/`v_proj`, the MLPs. They are full of numbers, billions of them in total, collectively called the **weights**. At the start these numbers are random and the model can do nothing. Training is one loop:

1. **Look at a batch of text and predict the next token** (the main line of the first three chapters).
2. **Check the answer and compute the loss.** The loss measures how "surprised" the model was: the higher the probability it assigned to the true next token, the lower the loss.
3. **Backpropagate and nudge every weight a tiny bit in the direction that lowers the loss.**

![Gradient descent](../images/m4_gradient_descent.png)

The curve in the figure is the "loss landscape", and training is the search for a valley in it. Each step moves downhill along the slope; that is **gradient descent** (the gradient is the slope direction at your current position, telling you which way to move). Repeat that loop hundreds of millions of times over trillions of tokens, and the weights are gradually carved from random numbers into something that can predict language. "Similar words have similar vectors" from Part 1 is a by-product of exactly this process.

## Fine-tuning: standing on someone else's foundation

Pre-training from scratch costs millions of dollars. **Fine-tuning** means taking an already pre-trained model (it is already near a valley), running a few more steps of gradient descent on your own small dataset, and nudging it a bit further toward your specific task. Far cheaper.

But full fine-tuning updates **all** those billions of weights, and GPU memory can't take it. Hence LoRA.

## LoRA: freeze the big matrix, train two small ones

![LoRA low-rank adaptation](../images/m4_lora.png)

The original weight `W` is frozen, and a bypass is hung beside it: two thin matrices multiplied together, `B × A`, treated as the "delta" and added on top. The effective weight becomes `W + B×A`, and training updates only `B` and `A`, often less than 1% of the original parameter count.

Why does this work? Because the adjustment fine-tuning needs is in fact "low-rank": you don't need the expressive power of the whole big matrix, the product of two thin ones is enough.

So what actually gets saved? Full fine-tuning has to store a gradient and optimizer state for **every** weight (Adam adds two momentum terms on top), and that is the bulk of the memory; LoRA cuts it down to just the handful of bypass parameters. But the frozen base weights still have to sit in GPU memory, and the activations needed for backpropagation still have to be stored — so the saving is **a few times over, not tens of times**: the LoRA paper reports 1.2TB → 350GB on GPT-3 175B, about 3x. What actually fits large-model fine-tuning onto a consumer-grade card is stacking base-weight quantization on top of LoRA (QLoRA compresses the frozen weights to 4 bits).

The **checkpoint**, though, shrinks astonishingly: storing only `B` and `A` takes it from hundreds of GB down to tens of MB, so one base model can carry any number of tiny adapters and switch between them at will. The real-code textbook is HuggingFace's `peft` library.

## Alignment: making the model give the answers humans want

Pre-training plus fine-tuning teaches the model to "predict plausible text", but plausible text is not the same as a good answer; text on the internet is all sorts of things. **Alignment** is the step that teaches the model to produce what humans actually want: helpful, harmless, honest.

One mainstream method is **DPO**: feed the model pairs of examples (a better answer and a worse one) and directly optimize it to prefer the better one. That step is why the chat models you use day to day follow instructions and stay on the rails. The code textbook is the `trl` library.

## Reasoning: teaching the model to think before it answers

There is one more step after alignment, and it is the biggest change of the last two years.

The model emits one token at a time and cannot go back. So how does it solve a problem that takes several steps? The answer is almost disarmingly plain: **it emits its thinking as tokens too**, generating a scratchpad first (break the problem down, try a calculation, check it) and only then the final answer. This is chain of thought. It works because every step is just one easy next-token prediction; a hard problem has been decomposed into a chain of easy ones. The cost is that thinking spends tokens, which is why reasoning modes are slower and pricier.

The real question is how to make the model **think well**. Hand-written demonstrations (SFT) can only teach it to imitate; they cannot teach a solution it has never seen. o1 and DeepSeek-R1 took a different road: **reinforcement learning with verifiable rewards (RLVR)**. Give it a large set of problems with checkable answers (math, code), let it generate its own reasoning and answer, reward the correct ones and not the others, then use gradient descent to move toward "the kind of thinking that got it right". **Nobody tells it how to think, only whether it thought correctly.** The common algorithm is GRPO: sample a group of answers to the same problem and use their relative quality within the group as the signal, which does away with the separate value model of RLHF.

What comes out is emergent. The R1 paper records the model spontaneously learning to go back and check, to change approach, to write "wait, let me look at this again"; nobody demonstrated any of that.

This step is still the same move: compute the loss, run gradient descent, nudge the weights. Only the signal has changed, from "does this look like what a human wrote" to "is the answer right".

## The life of a model

Stringing the five steps together:

> Random weights →(pre-training: gradient descent over trillions of tokens)→ a base model that can predict language →(fine-tuning / LoRA: further training on a small dataset)→ specialized for a task →(alignment / DPO: tuned to human preferences)→(reasoning RL: tuned on whether answers are right)→ the chat assistant you use.

All five steps are the same move: **compute the loss, run gradient descent, nudge the weights.** What changes is only which data is used, which weights are tuned, and how the loss is defined.

## Key takeaways

- Training = predict the next token → compute loss → gradient descent to nudge weights, repeated hundreds of millions of times.
- Fine-tuning continues training on top of pre-training; LoRA freezes the original weights and trains two small low-rank matrices, saving the memory for gradients and optimizer state (a few times over; the base weights and activations cannot be saved, and reaching a consumer card takes base-weight quantization on top), while the checkpoint shrinks to tens of MB.
- Alignment (e.g. DPO) uses human preference data to get better answers out of the model.
- Reasoning models emit their thinking as tokens; reinforcement learning with verifiable rewards (RLVR / GRPO) teaches them to think well, by telling them only whether they got it right, never how to think.
- Pre-training, fine-tuning, alignment, and reasoning RL are the same move under different configurations.

## Question to think about

LoRA freezes the original weight W and trains only the small matrices B and A. Why does it lose almost no quality? And exactly which part of the training memory does it save, versus which part it cannot? (Hint: the phrase "low-rank delta"; and the difference between "gradients and optimizer state" and "activations".)

Reasoning RL uses only "was the answer right" as its signal. Why does that teach better reasoning than hand-written demonstrations of thinking (SFT)? (Hint: what is the ceiling of SFT?)
