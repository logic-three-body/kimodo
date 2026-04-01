# Tmux 服务保活指南 (Kimodo Service Keep-Alive)

**适用场景**

- 运行持续的 Kimodo Demo (Gradio 服务) 和文本编码器 (Text Encoder)
- 网络不稳定，SSH 经常自动断开
- 希望服务在后台常驻运行，即使关闭本地终端页面依然可以访问 `localhost:7860`

## 0. 安装 (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y tmux
```

## 1. 核心机制 (The "Why")

> **后台运行，前台直播**
>
> Tmux 将**程序运行**(Server)与**显示界面**(Client)解耦。即使断网、关机、退出 SSH，
> Server 端的 Kimodo 进程依然在内存中运行，直到你下次回来重连画面。

## 2. 标准作业流程 (SOP)

### 第一步: 创建保险箱 (Start)

不要直接跑代码，先新建一个 Tmux 会话:

```bash
tmux new -s kimodo_web
# -s 后面是名字，建议以服务名称标记
```

### 第二步: 启动 Kimodo 服务 (Run)

在 Tmux 窗口内，首先激活运行环境：

```bash
# 激活 conda 和专属环境，并设置防断联环境变量
source /root/miniforge3/etc/profile.d/conda.sh
conda activate kimodo
export HF_HUB_DISABLE_XET=1
```

**运行 Demo 界面**:

```bash
kimodo_demo --model Kimodo-SOMA-RP-v1
```

> **说明**: 初次启动时 `viser` 前端会在后台进行构建，可能需要等待几分钟。启动成功后可以访问 `http://127.0.0.1:7860` 或 `http://localhost:7860`。

### 第三步: 安全撤离 (Detach)

当你想离开时(或网络自动断了)，手动将任务挂起:

1. 按下 **Ctrl + b** (松开)
2. 按下 **d** (Detach)

结果: 你回到普通终端，提示 `[detached]`，但 Kimodo 服务在后台继续运作。

### 第四步: 恢复现场 (Attach)

```bash
# 1. 查看有哪些会话在跑
tmux ls

# 2. 进入指定的会话
tmux attach -t kimodo_web
```

## 3. 常用指令速查表 (Cheat Sheet)

**核心前缀键 (Prefix)**: 所有 Tmux 快捷键都必须先按 **Ctrl + b**，松开后再按后续按键。

| 动作 | 命令/快捷键 | 说明 |
| --- | --- | --- |
| 新建会话 | `tmux` 或 `tmux new -s <名字>` | 开启一个新的工作区 |
| 挂起离开 | Prefix + `d` | 退出当前会话(程序不中断) |
| 查看列表 | `tmux ls` | 查看后台所有活着的会话 |
| 恢复会话 | `tmux attach -t <名字>` | 重新进入某个会话 |
| 杀死会话 | `tmux kill-session -t <名字>` | 彻底关闭某个会话(程序会停止) |
| 左右分屏 | Prefix + `%` | 一边看日志，一边看 `nvtop` |
| 上下分屏 | Prefix + `"` | 同上 |
| 切换面板 | Prefix + 方向键 | 在分屏之间光标跳转 |
| 关闭面板 | Ctrl + `d` (或输入 `exit`) | 关闭当前分屏 |

## 4. Kimodo 进阶运行技巧 (Pro Tips)

### 技巧 A: 查阅加载日志 (滚动模式)

**痛点**: Text Encoder 初次加载模型（15GB）或 `viser` 编译时可能产生很长的日志，默认无法滚动翻看。

**操作**:

1. 按 Prefix + `[` 进入 Copy Mode
2. 用方向键或 PageUp/PageDown 上下翻
3. 按 `q` 退出

### 技巧 B: 剥离显存压力与服务 (分屏启动)

**由于 Llama 和 Kimodo 两边均占用一定系统资源，可以通过分别启动两个组件来解耦管理**。

建议将 Tmux 屏幕切成左右或者上下两部分:

- 左边窗口:
  ```bash
  source /root/miniforge3/etc/profile.d/conda.sh
  conda activate kimodo
  kimodo_textencoder
  ```
- 右边窗口 (等左侧模型加载完成后):
  ```bash
  source /root/miniforge3/etc/profile.d/conda.sh
  conda activate kimodo
  export HF_HUB_DISABLE_XET=1
  kimodo_demo --model Kimodo-SOMA-RP-v1
  ```
另外，你仍可以水平分屏出一个 `watch -n 1 nvidia-smi` 以监控此时的 GPU 显存。

### 技巧 C: 强制结束卡死的生成服务

如果由于 `torch` 或模型 OOM 把 Tmux 卡死了，进不去服务重启:

```bash
tmux kill-session -t kimodo_web
```

## 一句话总结

**进门 `tmux new`，出门 `Ctrl+b d`，回家 `tmux attach`。**
