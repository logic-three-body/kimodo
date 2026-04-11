# 04 - API 及应用全方位使用指南 (Usage and Examples)

在了解了这套生成逻辑后，这里是如何在你的项目中“开箱即用”它的。

Kimodo 提供了几种常见的使用层（Usage Layer），适应于不同场景：脚本批处理、Python SDK 编程控制、以及交互式 Web UI。

## 1. 命令行界面 (CLI) 使用
对于大多数日常使用和批量生成，直接使用提供的启动脚本即可（入口为 `kimodo/scripts/generate.py` 中注册的 CLI `kimodo_gen` 命令）。

### 基本生成
你想生成一个简单的人走路并且后空翻的动作，保存为 `my_motion.npz`。

```bash
kimodo_gen --text "a person walking then doing a backflip" --out_path output/my_motion.npz
```

### 指定模型与导出格式
你可以指定使用某个变体模型（如默认支持机器人控制的 `Kimodo-G1-RP-v1`）。假设你要给强化学习模拟器生成控制：
```bash
kimodo_gen --text "a humanoid robot walks forward" --model_name Kimodo-G1-RP-v1 --out_path output/test_walk_g1.csv
```
这会在 `output/` 下生成可以导入 MuJoCo 仿真器的 CSV 格式。（参考 `output/` 中的样例文件）。

## 2. 编程式生成 (Python SDK)

如果你想把 Kimodo 嵌入到现成的 Python 项目流水线中（例如结合 ROS 或者强化学习），可使用原生的 Python 类调用：

```python
import torch
from kimodo.model.load_model import load_model
from kimodo.constraints import Root2DConstraintSet
from kimodo.exports.bvh import export_bvh

# 1. 下载并加载 34-joint 机器人控制模型
device = "cuda" if torch.cuda.is_available() else "cpu"
model = load_model("Kimodo-G1-RP-v1").to(device)

# 2. 定制文本和时间轴
texts = ["a person runs fast", "the person jumps high"]

# 3. 添加额外空间约束 (让机器人在特定的坐标点跳跃)
my_constraints = Root2DConstraintSet(...) # (配置 X, Y 行进轨迹点)

# 4. 生成运动 (带防滑步处理)
motion = model.generate(
    text_prompts=texts,
    num_denoising_steps=100,  # 采样步数，越高越平滑
    cfg_weight=2.0,           # 提示词权重
    constraints=[my_constraints]
)

# 5. 导出动作文件（以 BVH 格式为例，这里如果是 G1 请用 CSV 导出，具体请参考 export 包）
export_bvh(motion, "my_run_jump.bvh")
```

## 3. Web UI 交互式系统 (Interactive Demo)

由于动作和约束十分复杂，单纯依赖代码生成往往无法所见即所得。Kimodo 构建了一个基于 `Viser` 的沉浸式 Web 界面。

**源码位置**: `kimodo/demo/app.py` 及其子包 (`state.py`, `generation.py` 等)

### 3.1 启动 Demo
在命令行运行：
```bash
kimodo_demo
```
这将在本地启动一个带有 3D 渲染视图的网页。你可以直观地在这个界面中：
1.  **设置时间线 (Timeline)**：添加不同的 Prompt 块，并为它们的过渡设置 `num_transition_frames`（默认 5 帧插值平滑处理过渡）。
2.  **设置关键帧约束**：鼠标拖拽控制小金人的根骨骼，甚至端点关节。
3.  **多角色渲染**：切换支持的人物如 SOMA 或者 G1。

### 3.2 Demo 架构简析
因为该 Demo 支持在 Hugging Face Spaces 上在线部署，其核心采用了复杂的隔离机制。
*   `embedding_cache.py`: 作为缓冲层。如果你输入相同的 "run"，不需要由于 UI 重绘而频频请求 `LLM2Vec` 编码器。
*   `queue_manager.py`: 面向外网的并发和资源控制模块，设置了例如 15 分钟会话闲置超时的释放策略。
*   `state.py`: （单次请求内的所有暂存组件管理），比如你的进度条加载状态、已经完成的生成批次。

这一章讲清了不同层次的用户（包括无代码偏好者、算法工程师和 Web 体验者）可以如何利用该项目。下一章节，我们将进行二次开发和理论探讨。