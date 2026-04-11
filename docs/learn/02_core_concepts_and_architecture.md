# 02 - 核心概念与模型架构层 (Core Concepts and Architecture)

在深入分析具体的推理代码前，必须先掌握 Kimodo 使用的核心组件与宏观模型结构。以下内容将结合源码中的实际类名与张量（Tensor）维度进行深度拆解。

## 1. 约束系统 (Constraints)

除了文本生运动，Kimodo 最强大的功能是**空间约束**。核心源码位于 `kimodo/constraints.py`。
约束帮助模型在生成（采样）的过程中动态修正（通过加 Mask）运动张量。所有的约束都继承自 `ConstraintSet`，并通过 `TYPE_TO_CLASS` 字典进行注册管理：

*   **`Root2DConstraintSet`**: 约束人物顺着二维平面轨迹走。它要求输入 `frame_indices` [K]（哪些帧受限），以及 `smooth_root_2d` 坐标 [K, 2]。
*   **`FullBodyConstraintSet`**: 全身关键帧约束。接受 `global_joints_positions` [K, num_joints, 3] 和 `global_joints_rots` [K, num_joints, 3, 3] 旋转矩阵。
*   **`EndEffectorConstraintSet`**: 末端效应器约束。更具象的子类包含 `LeftHandConstraintSet` 和 `RightFootConstraintSet`。它们在运行 `update_constraints` 周期时，提取并固定目标骨骼索引的坐标（如 `RightFoot` 索引）。

在计算图中，这些约束最终被转化为与运动特征（Motion Feature）相同大小的 `motion_mask` [B, T, D]（其值为 0 或 1），以及 `observed_motion` [B, T, D] 两个张量。

## 2. 两阶段降噪器 (Two-Stage Denoiser)

核心源码位置：`kimodo/model/twostage_denoiser.py`。
Kimodo 采用了“先根节点（Root），后身体（Body）”的阶段化生成策略，网络主体是 `TwostageDenoiser(nn.Module)` 类。

在 `TwostageDenoiser` 的 `__init__` 函数中，模型实例化了两个相互独立的 Transformer 主干网络：

1.  **`self.root_model = TransformerEncoderBlock(...)` (Stage 1)**
    处理根节点轨迹生成。若启用了 `concat` 蒙版模式（`motion_mask_mode`），它的输入维度是原维度翻倍，输出则是 `global_root_dim`（通常尺寸为 5，即 `[x, z, vx, vz, heading]` 速度与航向数据）。
2.  **`self.body_model = TransformerEncoderBlock(...)` (Stage 2)**
    处理全身运动降噪。它将上一步生成的 `[B, T, 5]` 的全局根节点轨迹转化为局部根节点表示 `local_root_dim`，然后与原身体特征拼接：
    `x_new = torch.cat([root_motion_local, body_x], axis=-1)`
    预测输出维度为全身特征的残差 `body_output_dim = input_dim - 5`。

每次的 `forward()`，特征序列先被灌入 `root_model` 预测轨迹，随即拼凑进 `body_model` 的输入中预测局部姿态。这是让 Kimodo 不会产生方向迷失的关键网络层设计。

## 3. 文本编码系统 (Text Encoder)

**源码位置**: `kimodo/model/text_encoder_api.py`

在生成过程中，文本必须转为可以与图像张量交互的注意力建（Key/Value）。文本字符串列表（如 `texts=["a person walking"]`）交由 Text Encoder 组件：
- 模型不会每次本地加载巨型 LLM，而是请求 API 端点（即 `LLM2Vec-Meta-Llama-3-8B`）。
- API 返回 `text_feat`（文本嵌入，规模为 `[B, max_text_len, llm_dim]`）以及文本有效长度掩码 `text_pad_mask` `[B, max_text_len]`。

## 4. 组装在一起：主模型类 (`Kimodo`)

**源码位置**: `kimodo/model/kimodo_model.py`

系统中一切的入口类名为 `Kimodo(nn.Module)`。它在初始化时配置四大组件：
```python
self.denoiser = ClassifierFreeGuidedModel(self.denoiser, cfg_type=cfg_type)
self.motion_rep = denoiser.motion_rep          # 包含特征维度的核心抽象 (motion_rep_dim)
self.diffusion = Diffusion(num_base_steps=num_base_steps) # 一般是 cosine schedule 1000 步
self.sampler = DDIMSampler(self.diffusion)     # 决定反向迭代逻辑
self.text_encoder = text_encoder               # 预存的文本编码 API 对象
```

当 `load_model()`（`kimodo/model/load_model.py`）被调用时，其实就是往 `Kimodo` 这个壳子里载入具体训练好权重。

在下个章节中，我们将解析 `Kimodo._generate` 的内部张量流。
