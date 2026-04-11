# 05 - 进阶拓展与训练理论推衍 (Advanced Topics and Training Theory)

由于你手头的 Kimodo 代码库只有采样（`sampler` 和 `generate`），身为源码级开发者，你一定会好奇：如何用它设计训练流程？我们要关注哪些数据管道机制？

## 1. 原理模拟：缺失的 `train.py` 会长什么样？

如果我们今天需要重构这个代码的训练端（Training Pipeline），它的 `training_step` 方法会如何编写呢？在原论文架构中，它是这样被反向工程出来的：

### 1.1 扩散时间步的生成调度
在真实训练中，你会用到项目内预留好的 `kimodo/model/diffusion.py`。
```python
# 提取论文中设定的 Cosine Schedule Betas：
betas = get_beta_schedule(num_diffusion_timesteps=1000)
# alpha_bar_t 的数学公式通过 cumprod 得出：
alphas_cumprod_base = torch.cumprod(1.0 - betas, dim=0) 
```

### 1.2 前向加噪（Forward Diffusion）过程
假设在 Dataloader 吐出了干净运动张量 `x_start` [B, T, 328]：
```python
# 生成随机 timestep [B]
t = torch.randint(0, 1000, (B,), device=device) 
noise = torch.randn_like(x_start) # 真实噪音 [B, T, 328]

# 这一行调用了扩散机制 q_sample，把干净的数据变得有噪音：
# x_t = sqrt(alpha_bar) * x_0 + sqrt(1 - alpha_bar) * eps
x_noisy = self.diffusion.q_sample(x_start, t, noise)
```

### 1.3 损失函数 (MSE Loss 等)
将 `x_noisy`，时间步 `t` 送入双阶段根分类器 `TwoStageDenoiser.forward`。
```python
# 这里的 output_pred 取决于你让模型学的是直接输出无噪 x_0，或者是原始噪声 eps
output_pred = self.denoiser(x_noisy, pad_mask, text_feat, ..., t)

# 基线目标公式：
loss_mse = F.mse_loss(output_pred, noise)
# 网络进行梯度回传：
loss_mse.backward()
optimizer.step()
```

## 2. 二次开发：如何实现一种自己的 `ConstraintSet`？

你可以创建全新的干预方式。比如你想做个“不能低于某高度”的墙贴式动作，只要模仿 `kimodo/constraints.py`。
所有的自定义空间控制最终重写为返回占位向量和索引张量：

```python
from kimodo.constraints import ConstraintSet

class WallHeightConstraintSet(ConstraintSet):
    name = "wall_height"
    
    def __init__(self, skeleton, frame_indices, height_limit):
        # 接收 [K] 维度的一堆帧数表
        self.frame_indices = frame_indices  
        self.height_limit = height_limit    # 假定是个张量 [K, 1]
    
    def update_constraints(self, data_dict: dict, index_dict: dict) -> None:
        # 该函数在生成被调用时，会在对应的骨架端点注入掩码
        data_dict["root_y_pos"].append(self.height_limit)
        index_dict["root_y_pos"].append(self.frame_indices)
```
这就使在 `kimodo_model.py` 构建 `apply_constraints` 得到 `motion_mask` 时，将强行的掩盖条件直接插到神经网络每次的前馈（feed-forward）中，强制 `DDIMSampler` 在求解倒推梯度时沿着该墙体滑行而不违反重力。

---
**结语**

通过张量流动、`nn.Module` 函数签名，以及虚拟的 `train.py` 重建推演，我们成功以 100% 的源码级拆解重构了您从高层 API 到底层张量的所有理解！
