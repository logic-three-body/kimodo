# 03 - 推理源码级解析 (Source Code Level Inference Analysis)

为了彻底摸清推理流程，我们从张量流动的角度剖析代码：`kimodo/model/kimodo_model.py` 下的 `_generate()` 循环和降噪核函数。以下将展示所有相关的矩阵（Tensor）形状和内部运算环节。

## 1. `_generate()` 的输入准备

当执行 `model.generate()` 时，函数内部会调用更为内核的 `_generate(...)`，输入包含了批量的大小（Batch `B`）、目标时间帧长度（Frames `T`），以及网络要输出的动作向量维度（`D` 即 `motion_rep.motion_rep_dim`，在 SOMA 骨态下常为 328）。

```python
# 1. 文本编码阶段
text_feat, text_length = self.text_encoder(texts)  # 返回 [B, max_len, llm_dim]
text_pad_mask = torch.arange(max_len) < text_length[:, None]  # 注意力 Mask [B, max_text_len]

# 2. 运动张量的随机初始化初始化维度
shape = (batch_size, max_frames, self.motion_rep.motion_rep_dim)
cur_mot = torch.randn(shape, device=self.device)  # 产出纯噪声图像张量 x_T [B, T, D]
```

同样地，你的输入约束经过转化，得到了两个极高维度的占位张量（如果有提供约束的话）：
* `motion_mask`: `[B, T, D]`，由 0 和 1 构成的遮罩。
* `observed_motion`: `[B, T, D]`，强制要求固定到该坐标点的信息。

## 2. DDIM 反向采样长循环 (DDIM Loop)

扩散过程本质是在迭代降低输入噪声 `cur_mot` 的过程：
```python
# 生成步长索引，比如从 100 倒数到 0 [99, 98, ..., 0]
indices = list(range(num_denoising_steps))[::-1] 

for i in progress_bar(indices):
    t = torch.tensor([i] * cur_mot.size(0), device=self.device)  # timestep 张量: [B]
    with torch.inference_mode():
        # 调用下一步的单次降噪函数
        cur_mot = self.denoising_step(
            cur_mot,                    # 此时的含噪图 [B, T, D]
            pad_mask,                   # [B, T]
            text_feat,                  # 文本条件 [B, max_len, llm_dim]
            text_pad_mask,              # [B, max_len]
            t,                          # 当前时间步 [B]
            first_heading_angle,        # 起始方向
            motion_mask,                # 约束掩码
            observed_motion,            # 约束坐标
            num_denoising_steps,
            cfg_weight,
            cfg_type=cfg_type,
        )
```
每跑一步循环，`cur_mot` 会被剥离一层细微的 `eps` 预测出来的高斯噪声。

## 3. 单步前向网络：`denoising_step()` 及 CFG 实现

`denoising_step()` 包含两个重大行为：查询主干网络返回 `pred_clean`，并应用扩散积分算法步。由于 Kimodo 全线采用包含“无分类器提示（CFG）”的引导模型 `ClassifierFreeGuidedModel`。内部的运算路径是这样的：

**CFG 引导提取 (`pred_clean` 生成过程):**
```python
# self.denoiser 是 ClassifierFreeGuidedModel 实例。
# 它内部其实把输入的数据 x 堆叠（concat）了两次（有条件、无条件计算一次），送入 Transformer。
pred_clean = self.denoiser(
    cfg_weight,          # [B] 的放标参数 （如 2.0 倍）
    motion,              # [B, T, D]
    pad_mask,            # ...其它一众参数
    cfg_type=cfg_type,   # 比如 'separated' 处理多个蒙版
)

# ClassifierFreeGuidedModel 内部发生的 CFG 插值公式 (简单版表述)：
# x_out = x_uncond + cfg_weight * (x_cond - x_uncond)
```

**应用 DDIM 数向后步退 (`self.sampler`)：**
```python
# self.sampler 是 DDIMSampler(self.diffusion)
# 返回了 x_{t-1}，即距离无损干净图像近了一步的动作张量
x_tm1 = self.sampler(use_timesteps, motion, pred_clean, t)
```

## 4. 后处理与防滑步 (Foot Skate Reduction)

当经过了 100 次 `denoising_step` 之后，`cur_mot` 是理论上完美的 `x_0` 预测向量（[B, T, D]）。

然后在上层调用 `postprocess()` 进行剥离还原（把这个复杂的抽象隐特征 `local_root_dim` 展开变回可懂的关节角度矩阵和位置矩阵）：
```python
# _generate 完毕后，回到 generate 模块的底部：
motion = self.postprocess(z)

# 为防止动作在播放时存在摩擦滑移（尤其是 Root 根运动时的积累误差），需通过硬解算约束修复步伐：
motion = reduce_foot_skate(motion)  
```
`reduce_foot_skate()` 使用逆运动学（IK - Inverse Kinematics）的梯度或解析算法强行把在踩地时间段内本应在静止阈值下的脚底板坐标归零对齐，从而产生了顺滑清晰的最终运动。
