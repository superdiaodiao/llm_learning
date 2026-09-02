# llm_learning · 从零看懂大模型

> 一条从底到顶的完整链路：文字怎么变成向量 → attention 怎么理解上下文 → 模型怎么生成 → 权重怎么训练出来 → 大模型怎么被高效服务 → RAG 与 Agent 怎么落地 → 记忆系统与 Agent 架构怎么设计。
>
> 每一篇都以顶尖开源项目的**真实源码**为课本（transformers、vLLM、LlamaIndex、mem0、LangGraph、peft/trl），配示意图，讲透原理而不是堆概念。面向有工程背景、想系统理解现代 AI 的读者。

## 目录

| # | 篇目 | 一句话 |
|---|---|---|
| 01 | [Token 与 Embedding：文字如何变成数字](01-tokens-and-embeddings.md) | 模型只处理向量；分词、查表、语义空间 |
| 02 | [Attention 与 Transformer：模型如何理解上下文](02-attention-and-transformer.md) | Q/K/V、位置编码、多头、block 与堆叠 |
| 03 | [生成：从 logits 到文字](03-generation-logits-to-text.md) | lm_head、采样三旋钮、自回归、KV cache |
| 04 | [训练与微调：模型的权重从哪来](04-training-and-finetuning.md) | 梯度下降、预训练、LoRA、对齐 |
| 05 | [推理系统：大模型怎么被高效服务](05-inference-systems.md) | PagedAttention、连续批处理、量化 |
| 06 | [应用层：RAG 与 Agent](06-rag-and-agents.md) | 应用地图、RAG 流水线、重排、Agent 循环 |
| 07 | [AI 记忆系统：让 Agent 跨会话不失忆](07-ai-memory-systems.md) | 读写循环、记忆分类、mem0 源码与提示词 |
| 08 | [Agent 架构深入：从 ReAct 到多 Agent](08-agent-architectures.md) | ReAct、图/状态机、规划、多 agent、决策图 |
| 09 | [实战篇：从看懂代码到给顶尖项目提 PR](09-contributing-in-practice.md) | 模式狩猎方法论 + LlamaIndex / mem0 两个真实案例 |

## 主线一图

```
文字 ──分词/查表──▶ 向量 ──attention × N 层──▶ 懂上下文的向量 ──lm_head/softmax/采样──▶ 下一个词 ──循环──▶ 文本
                                    ▲                                                        │
                        训练：预测下一个词 → 算 loss → 梯度下降（04）                          │
                        服务：PagedAttention / 连续批处理 / 量化（05）                        │
                                                                                            ▼
                          应用：RAG 外挂知识 · Agent 外挂行动 · 记忆外挂记性（06/07/08）
```

## 怎么读

- 按序号读。01–03 是输入→加工→输出的主线，04–05 讲模型的来源与服务，06 起转向应用层，07/08 是两个深入方向。
- 每篇结尾有一道**思考题**，答案往往在下一篇被回收。
- 09 是番外，讲方法不讲原理：怎么在几万星的 AI 项目里自己发现 bug、提 issue、提 PR——所有 issue/PR 编号都是公开记录。

## 图片

`images/` 里每张图同时提供 `.svg`（矢量）与 `.png`（位图）。文章内按相对路径引用 PNG，GitHub 上可直接预览。

## 涉及的真实代码课本

| 项目 | 文件 / 模块 | 对应篇目 |
|---|---|---|
| transformers | `src/transformers/models/llama/modeling_llama.py` | 01–03 |
| peft / trl | LoRA 层实现、SFT / DPO 训练器 | 04 |
| vLLM | `BlockManager`、`Scheduler` | 05 |
| LlamaIndex | retriever / query engine / node postprocessor | 06 |
| mem0 | `mem0/memory/main.py`、`mem0/configs/prompts.py` | 07 |
| LangGraph | `StateGraph` 与条件边 | 08 |

## 计划中

- 微调实战：LoRA / DPO 的可运行代码与避坑（进行中）
- 评估与上下文工程
- 多模态与扩散模型

## 许可

文字与图片采用 [CC BY-NC-SA 4.0](LICENSE) 许可：可自由转载、改编、用于学习，需署名、非商用、以相同方式共享。引用的第三方源码片段遵循其各自的开源许可（均为 Apache-2.0 / MIT）。

欢迎提 issue 指出错误或补充内容。
