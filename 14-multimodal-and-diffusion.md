# 14 · 多模态与扩散模型：图片怎么进 LLM、模型怎么画出一张图

> 中文 · [English](en/14-multimodal-and-diffusion.md)

> 系列《从零看懂大模型》第 14 篇。前 13 篇的模型只处理文字。这一篇把图片接进来，分两个方向：**看图**（图片怎么变成 LLM 能读的 token）和**画图**（扩散模型怎么从噪声里长出一张图）。两条路用的是不同的机制，但都建立在前面讲过的部件上：ViT 就是第 2 篇的 Transformer，CLIP 的对比学习就是第 1 篇的"语义相近 = 向量相近"，扩散模型的条件注入就是第 2 篇的 cross-attention。课本是 transformers 里的 CLIP、LLaVA 和 diffusers 里的调度器源码。

## 一、图片怎么变成一串向量：ViT

第 1 篇讲过文字进模型的第一步是分词再查表，每个 token 变成一个向量。图片没有"词"，Vision Transformer（ViT）的做法直接得近乎粗暴：**把图切成小方块，每个方块当一个 token。**

一张 336×336 的图，按 14×14 像素切，得到 24×24 = 576 个方块。每个方块 14×14×3 = 588 个数，过一个线性层变成一个向量，加上位置编码（第 2 篇），排成一串 576 个 token。之后就是标准的 Transformer：自注意力乘 N 层。图片里的"上下文"，就是方块和方块之间互相看。

这一步之后，图片和文字在模型内部**没有本质区别**：都是一串带位置的向量。所有多模态的花样都建立在这个事实上。

## 二、CLIP：让图和话落到同一个空间

![CLIP：两个编码器各自出一个向量，只比较、不融合](images/mm_clip_contrastive.png)

一个 ViT 训完能分类图片，但它的向量空间和文字模型的空间是两回事："狗"这个词的向量和一张狗的图的向量，离得多远没人管过。

2021 年的 CLIP 解决的就是这个。做法是**对比学习**：

- 两个编码器，一个图像塔（ViT），一个文本塔（Transformer），各自把输入压成一个向量，投到同一个维度。
- 一个 batch 里 N 张图配 N 句描述，算出 N×N 的相似度矩阵。对角线是真配对。
- 目标：把对角线拉高，其余全部压低。

transformers 的 `modeling_clip.py` 里，这个目标就几行：

```python
logits_per_text = torch.matmul(text_embeds, image_embeds.t()) * logit_scale.exp()   # N×N

def contrastive_loss(logits):
    return nn.functional.cross_entropy(logits, torch.arange(len(logits), device=logits.device))

def clip_loss(similarity):
    caption_loss = contrastive_loss(similarity)        # 每句话在 N 张图里选对自己的图
    image_loss = contrastive_loss(similarity.t())      # 每张图在 N 句话里选对自己的话
    return (caption_loss + image_loss) / 2.0
```

`torch.arange(N)` 就是标签：第 i 行的正确答案是第 i 列。**按行做一次 N 分类，按列做一次 N 分类，取平均。**没有人工标注类别，四亿对从网上抓的图文就是全部监督。

训完以后，两件事变得可能：

- **零样本分类。**想判断一张图是不是猫，不用训分类器，把"一张猫的照片"编码成向量，和图的向量比余弦。换成任何类别都行，因为文本塔认字。
- **图文互搜。**第 6 篇的向量检索直接可用：用文字搜图，用图搜图。

注意 CLIP 的两个编码器**从不融合**：图和话各走各的，最后只比一个数。这对检索够用，对"看着图回答问题"不够，回答需要图和问题在同一次注意力里互相看。那是下一节。

## 三、图片进 LLM：LLaVA 的三段式

![图片这条路：视觉塔 → Projector → 图像 token，和文字 token 拼成一个序列](images/mm_image_into_llm.png)

要让一个只会文字的 LLM 看图，最省事的办法不是重训，是**把图变成它认识的东西：一串和文字 embedding 同维度的向量，直接塞进序列**。LLaVA 是这条路最干净的实现，三个部件：

1. **视觉塔**：拿现成的 CLIP ViT-L/14（336 像素版），冻结。输出 576 个 1024 维向量。
2. **Projector**：一个两层 MLP，把 1024 维投到 LLM 的隐层维度（Vicuna-7B 是 4096）。**这是唯一从零训的部件。**
3. **LLM**：现成的语言模型。它收到的序列里，`<image>` 占位符的位置被替换成那 576 个向量。

transformers 的 `modeling_llava.py` 就是这三步：

```python
# 1. 视觉塔：取倒数第二层的输出，去掉 CLS
image_outputs = self.vision_tower(pixel_values, output_hidden_states=True)
selected_image_feature = image_outputs.hidden_states[vision_feature_layer]   # 默认 -2
selected_image_feature = selected_image_feature[:, 1:]                        # 丢掉 CLS token

# 2. Projector：1024 → 4096
image_features = self.multi_modal_projector(selected_image_feature)

# 3. 替换：input_ids 里等于 <image> 的位置，换成图像向量
inputs_embeds = self.get_input_embeddings()(input_ids)
special_image_mask = (input_ids == self.config.image_token_index).unsqueeze(-1).expand_as(inputs_embeds)
inputs_embeds = inputs_embeds.masked_scatter(special_image_mask, image_features)
```

第三步的 `masked_scatter` 值得盯住：**替换完以后，LLM 的 forward 和纯文字完全一样。**它不知道哪些向量来自图片。一张图就是 576 个"词"，问题里的文字 token 和它们在同一次注意力里互相看，所以能回答"图里左边那个人拿着什么"。

两个细节解释了它为什么能行：

- **取倒数第二层而不是最后一层。**CLIP 最后一层是为"和文字对齐后比一个数"优化的，丢掉了局部细节；倒数第二层保留更多空间信息。这是实验出来的经验，不是推导。
- **两阶段训练。**先冻住视觉塔和 LLM，只用几十万对图文描述训 Projector，让它学会"翻译"；再放开 LLM，用带图的指令数据微调（第 4 篇的 SFT）。第一阶段便宜，因为只有几百万参数在动。

### 之后的演进

LLaVA 的固定 576 token 有两个问题：小图浪费，大图和长图看不清。后来的模型（LLaVA-NeXT 的 AnyRes、Qwen-VL 的动态分辨率）把大图切成多个 336 的子图各自编码再拼，token 数随分辨率变。代价是一张高清图可能占几千 token，第 5 篇的窗口预算要算进去。

视频就是一串帧，每帧走一遍上面的路，token 数乘以帧数，所以视频模型都要在时间维上抽帧或压缩。音频同理，换一个音频编码器。**"多模态"在架构上的含义很朴素：换编码器，接 Projector，塞进同一个序列。**

## 四、扩散模型：从噪声里长出一张图

![扩散：正向加噪是固定公式，反向去噪是模型学的](images/mm_diffusion.png)

看图是把像素变向量。画图反过来，从"没有图"到"有图"。LLM 那套逐 token 生成对像素不合适：一张 512×512 的图有 78 万个像素，一个一个吐太慢，而且像素之间的依赖不是从左到右。

扩散模型换了一个思路，分两个方向：

**正向（加噪，固定公式，不学）。**取一张真图 x₀，一步一步往上加高斯噪声，T 步之后变成纯噪声。任意一步 t 的结果可以一次算出来，不用真的走 t 步。diffusers 的 `DDPMScheduler.add_noise` 就是这个公式：

```python
sqrt_alpha_prod = alphas_cumprod[timesteps] ** 0.5
sqrt_one_minus_alpha_prod = (1 - alphas_cumprod[timesteps]) ** 0.5
noisy_samples = sqrt_alpha_prod * original_samples + sqrt_one_minus_alpha_prod * noise
```

`alphas_cumprod[t]` 是一个从 1 单调降到接近 0 的数：t 小时基本是原图，t 大时基本是噪声。

**反向（去噪，模型学）。**训一个网络，输入"加了 t 步噪声的图"和 t，**预测加进去的那个噪声**。训练循环是三行：

```python
noise = torch.randn_like(latents)
timesteps = torch.randint(0, num_train_timesteps, (batch,))
noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

noise_pred = unet(noisy_latents, timesteps, encoder_hidden_states=text_embeds).sample
loss = F.mse_loss(noise_pred, noise)
```

预测噪声等价于预测"这张图应该往哪个方向变才更像真图"。生成时从纯噪声开始，让网络预测噪声、减掉一部分、再预测、再减，走几十步，噪声里逐渐长出一张图。每一步减多少由调度器决定，这就是 DDPM、DDIM、DPM-Solver 这些名字的区别：同一个网络，不同的走法，步数从一千降到二十。

### 文字怎么指挥画面

上面的网络没有文字也能生成，只是生成"训练集里随机的一张图"。要让它按描述画，把文字塞进去：

- 描述先过一个文本编码器，早期就是 **CLIP 的文本塔**（第二节训好的那个），得到一串向量。
- 去噪网络的每一层里加 **cross-attention**（第 2 篇）：图像特征当 Q，文字向量当 K 和 V。图的每个区域去"看"描述里的每个词，决定这里该画什么。

还有一个几乎所有文生图都在用的技巧，**无分类器引导**（classifier-free guidance）：训练时随机把描述抹掉，让网络同时学会"有描述"和"没描述"两种预测；生成时两种都算，取差值放大：

```python
noise_pred = noise_uncond + guidance_scale * (noise_cond - noise_uncond)
```

`guidance_scale` 通常 7 左右。它把"因为描述而产生的那部分变化"放大了七倍，所以图更贴描述、更锐利，也更容易过饱和。你在各种画图工具里调的那个"提示词相关性"就是它。

### 在小图上画，最后再放大：潜空间扩散

直接在 512×512×3 的像素上跑几十步 UNet，太贵。Stable Diffusion 的关键改动是先训一个 **VAE**，把图压缩 8 倍：512×512×3 变成 64×64×4 的"潜表示"。扩散全部在这个小空间里做，最后一步用 VAE 的解码器放大回像素。计算量降了几十倍，这是它能在消费级显卡上跑的原因。

代价是 VAE 有损：小字、细密纹理、手指这些高频细节容易糊，早期文生图"画不好手"一部分来自这里。

### 之后的演进

去噪网络从 UNet 换成 Transformer（DiT），让第 13 篇的 scaling law 在图像上也成立；"预测噪声"换成"预测从噪声到图的直线速度"（flow matching，SD3 和 Flux 用的），训练更稳、步数更少。**骨架没变：固定的加噪公式，学出来的去噪网络，文字通过 cross-attention 进来。**

## 五、看图和画图，为什么是两套

理解用"编码器 + LLM"，生成用"扩散"，是因为两件事的输出不同。理解的输出是文字，交给已经很会写字的 LLM 最省事；生成的输出是像素，自回归逐像素太慢、像素也没有天然顺序，扩散并行去噪更合适。

近两年出现了把两者合进一个模型的尝试：把图像也变成离散 token 让 LLM 直接生成（视觉 tokenizer），或者在一个 Transformer 里同时跑自回归和扩散两个头。哪条路会赢还没定，本篇只讲已经稳定的两套。

## 本篇要点

- ViT 把图切成方块当 token，之后和文字一样走 Transformer；图和文在模型内部都是带位置的向量串。
- CLIP 用对比学习把图和话对齐到同一空间，损失是"按行、按列各做一次 N 分类"；两个编码器不融合，适合检索和零样本分类。
- LLaVA 用冻结的 CLIP 视觉塔加一个新训的 Projector，把图变成 576 个和文字同维的向量塞进序列；LLM 不知道哪些 token 来自图。
- 扩散模型：加噪是固定公式，去噪网络学预测噪声；文字通过 cross-attention 注入，无分类器引导放大描述的影响；潜空间扩散用 VAE 压缩 8 倍换来速度。
- 理解走编码器加 LLM，生成走扩散，因为输出一个是文字一个是像素。

## 思考题

LLaVA 为什么只训 Projector 就能让 LLM "看见"，而不需要动 LLM 的任何参数？（提示：第 1 篇的 embedding 表在 LLM 眼里是什么。）`guidance_scale` 设成 1 和设成 0 分别等价于什么？

---

*相关代码：`src/transformers/models/clip/modeling_clip.py`（`clip_loss`）、`src/transformers/models/llava/modeling_llava.py`（`get_image_features`、`masked_scatter` 替换）、`diffusers/schedulers/scheduling_ddpm.py`（`add_noise`）、`examples/text_to_image/train_text_to_image.py`（训练循环）。*
