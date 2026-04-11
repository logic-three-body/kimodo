# 01 - 环境搭建与项目概览 (Introduction and Setup)

欢迎阅读 Kimodo 源码级学习指南！本指南将带你从零基础开始，深入理解 Kimodo 的整个技术栈。

**⚠️ 重要声明：本代码库为存粹的推理（Inference-only）代码库。** 
代码库中不包含任何模型训练相关的脚本（没有 `train.py`，没有 PyTorch 的 optimizer 或 loss 函数定义）。官方提供了在海量动作数据上预训练好的模型，代码库的主要功能是加载这些模型并进行前向推理（文本到运动的生成）。

## 项目简介
Kimodo 是一个支持将文本指令转化为高质量 3D 运动序列的系统。它不仅能控制虚拟人物（SOMA、SMPL-X 骨架），还能直接输出机器人（如 Unitree G1）的运动控制指令。

## 核心目录结构分析

理解项目的文件夹结构是阅读源码的第一步：

```text
kimodo/
├── kimodo/               # 核心源码包
│   ├── model/            # 核心模型定义（降噪器、主干网络、扩散采样器、模型加载）
│   ├── demo/             # 交互式 Web UI 的所有代码 (Viser 前端与系统状态)
│   ├── exports/          # 动作格式导出工具 (BVH, MuJoCo CSV, npz)
│   ├── scripts/          # 命令行入口脚本 (生成动作、启动 UI、转换格式等)
│   ├── skeleton/         # 骨架定义文件 (SOMA, G1 等骨骼层级与原始位姿)
│   └── constraints.py    # 空间与运动约束的实现
├── docs/                 # 项目文档（包含本学习指南）
├── pyproject.toml        # Python 依赖与构建配置
└── README.md             # 官方快速入门指南
```

## 环境搭建指南 (0 基础)

由于环境包含复杂的科学计算库与 3D 渲染组件，推荐使用 conda 进行隔离。

### 1. 准备基础环境
```bash
conda create -n kimodo python=3.10
conda activate kimodo
```

### 2. 安装项目
进入 `kimodo` 根目录：
```bash
pip install -e .
```
这会根据 `pyproject.toml` 安装所有的依赖项，例如 `torch`, `viser` (用于UI), `transformers` 等。

这就是全部的准备工作了。当你第一次运行生成任务时，代码会自动从 Hugging Face Hub 下载预训练模型权重。在下一章，我们将深入了解 Kimodo 的模型架构。