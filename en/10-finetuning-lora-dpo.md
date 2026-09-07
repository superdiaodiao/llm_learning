# 10 · Fine-tuning in Practice: LoRA and DPO

> [中文版](../10-finetuning-lora-dpo.md) · English

> Part 10 of the series *LLMs from the Ground Up*. Part 4 covered the principles of training; this one brings them down to code that runs: LoRA supervised fine-tuning (SFT) with peft, then DPO preference alignment with trl. The textbooks are peft's `tuners/lora/layer.py` and trl's `SFTTrainer` / `DPOTrainer`.

## What fine-tuning can and cannot do

First, a common misconception to correct: **fine-tuning is not a good way to "teach the model new knowledge".** The knowledge carried by billions of parameters in the weights barely moves under a few thousand examples; to inject new knowledge, the RAG of Part 6 is the more reliable route. What fine-tuning is good at is teaching **format, style, and behaviour**: how to answer, in what tone, under what rules.

Fine-tuning has two steps: SFT teaches the model "how to say it", DPO teaches it "which way of saying it is better".

## Step one: the SFT pipeline

![SFT pipeline and LoRA](../images/ft_sft_pipeline_lora.png)

Of the seven steps, three are the easiest to overlook and the most decisive:

**The data format is conversation.** SFT data is not two columns of "input → output" but a list of `messages` conversations, `[{"role":"user",...},{"role":"assistant",...}]`. A few hundred to a few tens of thousands of **high-quality** examples is enough; quality matters far more than quantity.

**The chat template.** Every model has its own conversation format (special tokens marking who is speaking), and `apply_chat_template` applies it. Use the wrong template and the model learns the wrong separators, then answers off the mark at inference time.

**Compute the loss only on the "answer".** In a conversation, the user's turn is the question and the assistant's turn is the answer to be learned. If the loss is computed over the whole sequence, the model wastes capacity learning to "recite the user's question". The fix is to set the labels of the prompt part to `-100` (which cross-entropy ignores) so only assistant tokens contribute gradient. In trl that is one switch: `assistant_only_loss=True`.

## What LoRA really is in peft

peft replaces each target linear layer with "base + bypass", and the core is one line:

```python
result = base_layer(x) + lora_B(lora_A(dropout(x))) * scaling   # peft/tuners/lora/layer.py
```

Three design details:

- **Initialization**: `A` is random (kaiming), `B` is **all zeros**. At the start of training `B·A = 0`, so the model behaves exactly like the base: a smooth start from "as is", rather than scrambling the model on step one.
- **scaling = lora_alpha / r**: `r` is the rank of the bypass (the expressive power of the delta), `alpha` controls its magnitude. Rules of thumb: r = 8 to 64, alpha = 2r.
- **Merging**: `get_delta_weight` computes `B @ A × scaling`; merging adds it straight into `W` for zero extra inference cost. Left unmerged, one base can hot-swap several adapters.

Where to attach it: by default on attention's `q/k/v/o` projections (those `q_proj` layers from Part 2), sometimes on the MLP too. The base stays frozen; what is saved is the gradients and optimizer state for billions of parameters, which is a few times over, not tens of times (Part 4 has the number: the LoRA paper reports 1.2TB → 350GB). The base weights and activations cannot be saved, and reaching a consumer card takes QLoRA on top, see pitfall 4 below.

### Minimal code that runs

```python
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig

model_id = "Qwen/Qwen2.5-0.5B-Instruct"          # a small model; runs on a laptop
tok   = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto")

lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                  target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                  task_type="CAUSAL_LM")
model = get_peft_model(model, lora)
model.print_trainable_parameters()               # trainable < 1%

ds = load_dataset("json", data_files="train.jsonl")   # one {"messages": [...]} per line

cfg = SFTConfig(output_dir="out", num_train_epochs=2, per_device_train_batch_size=4,
                learning_rate=2e-4, assistant_only_loss=True, logging_steps=10)
trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds["train"], processing_class=tok)
trainer.train()

model.save_pretrained("out/adapter")             # saves only the adapter, tens of MB
merged = model.merge_and_unload()                # merge into the base when needed
merged.save_pretrained("out/merged")
```

Under thirty lines is a complete LoRA fine-tune. `SFTTrainer` handles the chat template, tokenization, and loss masking for you; `get_peft_model` swaps each `q_proj` for the "base + bypass" layer above.

## Step two: DPO preference alignment

![DPO vs RLHF](../images/ft_dpo_vs_rlhf.png)

SFT has only "reference answers", no "comparisons": of two fluent answers, which is better (more helpful, more honest, less verbose) is something it cannot teach. That is what alignment is for.

**Why classic RLHF is hard.** Three stages: SFT → train a reward model on preference data to learn "scoring" → use PPO reinforcement learning to make the policy chase high scores while a KL penalty stops it drifting too far from the reference model. Effective, but heavy: policy, reference, reward, and value, four models in memory at once, and PPO is notoriously unstable.

**DPO's insight.** It can be shown mathematically that the optimal policy for the RLHF objective has a closed form, so the "reward" can be expressed in reverse through the policy itself: the implicit reward is `β·log(π/π_ref)`. Substitute that back into the preference-learning loss and the reward model folds into the policy, leaving a classification-style loss applied directly on preference pairs. No reward model to train, no reinforcement learning to run.

**How to read the loss.** For each `(prompt, chosen, rejected)`: make **chosen's improvement relative to the reference model** exceed **rejected's improvement relative to the reference model** by as much as possible. Two details matter most:

- **The reference model is not superfluous.** Without it, the model could make the loss tiny just by driving rejected's probability to zero, crushing its language ability along the way (mode collapse). The reference model anchors the change as a "relative improvement". With LoRA it is nearly free: switch the adapter off and the base is π_ref.
- **β is the reins.** Small β lets the model stray further from the reference (learns hard, drifts easily); large β keeps it close (stable, learns little). 0.1 is common.

### Minimal code that runs

```python
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOTrainer, DPOConfig

model_id = "out/merged"                       # the merged SFT model from the previous step: the starting point, and the reference model
tok   = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto")

ds = load_dataset("json", data_files="prefs.jsonl")   # one {"prompt": ..., "chosen": ..., "rejected": ...} per line

lora = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj","k_proj","v_proj","o_proj"],
                  task_type="CAUSAL_LM")
cfg = DPOConfig(output_dir="out_dpo", beta=0.1, learning_rate=5e-6,
                num_train_epochs=1, per_device_train_batch_size=2, logging_steps=10)
trainer = DPOTrainer(model=model, ref_model=None,      # ref_model=None + LoRA → the base with the adapter switched off is used as the reference automatically
                     args=cfg, train_dataset=ds["train"],
                     processing_class=tok, peft_config=lora)
trainer.train()
trainer.save_model("out_dpo/adapter")
```

## Practical pitfalls

1. **Preference data quality decides everything.** The difference between chosen and rejected must be the exact dimension you mean to teach (say "concise vs verbose"); otherwise the model learns spurious correlations in the noise.
2. **The DPO learning rate should be an order of magnitude below SFT's** (5e-7 to 5e-6 for full fine-tuning, a little higher for LoRA). DPO over-optimizes easily: the training loss looks great while the model starts emitting strange output. Watch the `rewards/margins` trl prints; a steady rise is fine, a spike usually means overfitting.
3. **Do not reverse the order: SFT first, then DPO.** DPO assumes the model already speaks decently and adjusts its preferences on top. DPO straight on a base model works far worse.
4. **Out of memory? Use QLoRA.** Load the base in 4-bit (`BitsAndBytesConfig(load_in_4bit=True)`) and keep training the LoRA bypass in 16-bit. A single 24GB consumer card can fine-tune a 7B-class model.

## Key takeaways

- Fine-tuning teaches format, style, and behaviour; it is poor at injecting knowledge. SFT teaches "how to say it", DPO teaches "which is better".
- Three keys to SFT: conversation format, chat template, loss on the answer only.
- LoRA's core is one line, `base(x) + B(A(x))·α/r`; B starts at zero, scaling = α/r, mergeable and hot-swappable.
- DPO folds the reward model into the policy, the reference model prevents collapse, β is the reins; SFT first, then DPO.

## Question to think about

Why does LoRA initialize B to zero rather than both A and B at random? In DPO the absolute probability of the rejected answer falls; why does that not mean the model has "learned something bad", and when is it genuinely a problem?
