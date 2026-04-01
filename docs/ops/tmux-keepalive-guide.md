# Tmux 服务保活指南 (Kimodo Service Keep-Alive)

**适用场景**

- 希望 `kimodo_textencoder` 和 `kimodo_demo` 在后台常驻运行
- 关闭本地终端、SSH 断开后，`http://localhost:9550` 和 `http://localhost:7860` 仍然可用
- 不想再手工进入 tmux pane 里逐条敲命令

## 1. 推荐入口

本仓库已经提供了固定的 env 文件和 detached tmux 启动器：

- 环境文件: [scripts/kimodo_web.env](/root/Project/Kimodo/kimodo/scripts/kimodo_web.env)
- 启动器: [scripts/kimodo_web_tmux.sh](/root/Project/Kimodo/kimodo/scripts/kimodo_web_tmux.sh)

当前默认配置：

- tmux session: `kimodo_web`
- text encoder: `0.0.0.0:9550`
- demo: `0.0.0.0:7860`
- model: `Kimodo-G1-RP-v1`

## 2. 一键启动

在仓库根目录执行：

```bash
cd /root/Project/Kimodo/kimodo
./scripts/kimodo_web_tmux.sh start
```

查看状态：

```bash
./scripts/kimodo_web_tmux.sh status
```

成功后应看到：

- tmux session `kimodo_web`
- `9550` 由 `kimodo_textencoder` 监听
- `7860` 由 `kimodo_demo` 监听

然后在浏览器打开：

- `http://localhost:9550`
- `http://localhost:7860`

这套启动方式本身就是 detached 的，所以命令执行完后你可以直接关闭当前终端窗口，不需要先 `attach` 再 `Ctrl+b d`。

## 3. 常用命令

```bash
cd /root/Project/Kimodo/kimodo

# 启动
./scripts/kimodo_web_tmux.sh start

# 查看会话和端口
./scripts/kimodo_web_tmux.sh status

# 进入 tmux 看实时日志
./scripts/kimodo_web_tmux.sh attach

# 重启两项服务
./scripts/kimodo_web_tmux.sh restart

# 停止两项服务
./scripts/kimodo_web_tmux.sh stop
```

## 4. 修改环境配置

如需修改模型、端口或环境变量，只改 env 文件即可：

```bash
vim /root/Project/Kimodo/kimodo/scripts/kimodo_web.env
```

常用配置项：

- `KIMODO_MODEL`: 默认模型，例如 `Kimodo-G1-RP-v1`
- `SERVER_PORT`: demo 端口，默认 `7860`
- `GRADIO_SERVER_PORT`: text encoder 端口，默认 `9550`
- `TEXT_ENCODER_DEVICE`: `auto`、`cpu`、`cuda:0`
- `HF_HUB_DISABLE_XET` / `HF_HUB_OFFLINE`

改完后执行：

```bash
cd /root/Project/Kimodo/kimodo
./scripts/kimodo_web_tmux.sh restart
```

## 5. 日志与排障

进入日志：

```bash
cd /root/Project/Kimodo/kimodo
./scripts/kimodo_web_tmux.sh attach
```

tmux 内部约定：

- window `textencoder`: `kimodo_textencoder`
- window `demo`: `kimodo_demo`

如果页面已经开着但新增 example 或新配置没刷新出来，先刷新浏览器；必要时再执行一次：

```bash
./scripts/kimodo_web_tmux.sh restart
```

## 6. 一句话总结

**以后不要手工 `tmux new` 再进 pane 启服务，统一用 `./scripts/kimodo_web_tmux.sh start`。**
