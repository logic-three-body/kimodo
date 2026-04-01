# Kimodo Environment Status

Updated: 2026-04-01

## Current State

- Host: WSL2 Ubuntu 20.04.3 LTS
- Working directory: `/root/Project/Kimodo`
- Local source clone: `/root/Project/Kimodo/kimodo`
- Local clone commit: `3b98f78` (`2026-03-27 Bug fix for foot contact visualization in demo`)
- Runtime environment: `Miniforge + conda`
- Conda env name: `kimodo`
- Python: `3.10.20`
- PyTorch: `2.11.0+cu128`
- CUDA runtime reported by torch: `12.8`
- CUDA available: `True`
- Primary GPU: `NVIDIA GeForce RTX 4090`
- Hugging Face auth: configured and `hf auth whoami` succeeds
- Hugging Face user: `michaelcarter1997`
- Install style: editable install from the local clone
- Recommended runtime env var on this machine: `HF_HUB_DISABLE_XET=1`
- Persistent service launcher: `/root/Project/Kimodo/kimodo/scripts/kimodo_web_tmux.sh`
- Persistent service env file: `/root/Project/Kimodo/kimodo/scripts/kimodo_web.env`

## Important Note About Runtime vs. Clone

The active runtime code now comes from the local editable clone.

Runtime import check:

```bash
source /root/miniforge3/etc/profile.d/conda.sh
conda activate kimodo
python -c "import inspect, kimodo; print(inspect.getfile(kimodo))"
```

Expected output:

```text
/root/Project/Kimodo/kimodo/kimodo/__init__.py
```

## What Has Been Verified

- `kimodo_gen`, `kimodo_demo`, and `kimodo_textencoder` are installed and on `PATH`.
- `import kimodo` works.
- Hugging Face gated access to `meta-llama/Meta-Llama-3-8B-Instruct` now works.
- Public Kimodo checkpoint cache exists at `~/.cache/huggingface/hub/models--nvidia--Kimodo-SOMA-RP-v1` and is about `1.1G`.
- The Meta-Llama text encoder cache exists at `~/.cache/huggingface/hub/models--meta-llama--Meta-Llama-3-8B-Instruct` and is about `15G`.
- CLI generation succeeded with:

```bash
kimodo_gen "A person walks forward." --model Kimodo-SOMA-RP-v1 --duration 5.0 --output /root/Project/Kimodo/output/test_walk
```

- Generated file exists at `/root/Project/Kimodo/output/test_walk.npz`.
- G1 CLI generation also succeeded with:

```bash
kimodo_gen "A person walks forward." --model Kimodo-G1-RP-v1 --duration 2.0 --output /root/Project/Kimodo/output/test_walk_g1
```

- Generated files exist at:
  - `/root/Project/Kimodo/output/test_walk_g1.npz`
  - `/root/Project/Kimodo/output/test_walk_g1.csv`
- `test_walk.npz` contains:
  - `local_rot_mats`: `(150, 77, 3, 3)`
  - `global_rot_mats`: `(150, 77, 3, 3)`
  - `posed_joints`: `(150, 77, 3)`
  - `root_positions`: `(150, 3)`
  - `smooth_root_pos`: `(150, 3)`
  - `foot_contacts`: `(150, 4)`
  - `global_root_heading`: `(150, 2)`
- `kimodo_demo --model Kimodo-SOMA-RP-v1` loads successfully.
- `kimodo_textencoder` returns embeddings successfully for:

```text
A single person rolls on the ground while repeatedly and comically slapping their own cheeks.
```

- After the first-time `viser` frontend build completes, `http://127.0.0.1:7860/` and `http://localhost:7860/` return `HTTP 200 OK`.
- `http://127.0.0.1:9550/` also returns `HTTP 200 OK` after the text encoder service is started.

## Closed-Loop Result

This machine has now passed the local inference closure target:

- Hugging Face auth works.
- Required gated model access works.
- GPU PyTorch works.
- Kimodo CLI works.
- Model auto-download works.
- Demo startup works.
- `localhost:7860` is reachable once the demo has finished its first frontend build.

## Known First-Run Behavior

- The first download of `meta-llama/Meta-Llama-3-8B-Instruct` is large and may take a while.
- On this machine/network, Hugging Face `xet` downloads were unstable with `416` and TLS EOF errors. Setting `HF_HUB_DISABLE_XET=1` made the downloads reliable enough to finish.
- The first `kimodo_demo` launch performs a `viser` client build and may spend several minutes on `npm` / `vite` output before `7860` starts listening.
- `curl -I` may trigger websocket handshake noise because `viser` expects `GET`; use `curl http://127.0.0.1:7860/` for a cleaner health check.

## How To Use

### 1. Activate the environment

```bash
source /root/miniforge3/etc/profile.d/conda.sh
conda activate kimodo
export HF_HUB_DISABLE_XET=1
```

### 2. Optional quick sanity checks

```bash
hf auth whoami
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
which kimodo_gen
which kimodo_demo
```

### 3. Run CLI generation

```bash
mkdir -p /root/Project/Kimodo/output
kimodo_gen "A person walks forward." --model Kimodo-SOMA-RP-v1 --duration 5.0 --output /root/Project/Kimodo/output/test_walk
```

Notes:

- The required caches are already present, so repeat runs are much faster than the first successful run.
- Success means you get `/root/Project/Kimodo/output/test_walk.npz`.

### 4. Launch the demo

```bash
kimodo_demo --model Kimodo-SOMA-RP-v1
```

Then open:

```text
http://localhost:7860
```

If WSL localhost forwarding behaves oddly, try:

```text
http://127.0.0.1:7860
```

Notes:

- The first demo launch on this machine builds the `viser` frontend locally before the page becomes available.
- After that build is complete, later starts should be faster.

### 5. Optional: run the text encoder service separately

```bash
kimodo_textencoder
```

Then start the demo in another shell:

```bash
kimodo_demo --model Kimodo-SOMA-RP-v1
```

### 6. Persistence and Keep-Alive (Tmux)

Use the detached tmux launcher instead of creating panes manually:

```bash
cd /root/Project/Kimodo/kimodo
./scripts/kimodo_web_tmux.sh start
./scripts/kimodo_web_tmux.sh status
```

This launcher reads:

- `/root/Project/Kimodo/kimodo/scripts/kimodo_web.env`

and creates one detached tmux session:

- `kimodo_web`

with two windows:

- `textencoder`
- `demo`

Useful follow-up commands:

```bash
cd /root/Project/Kimodo/kimodo
./scripts/kimodo_web_tmux.sh attach
./scripts/kimodo_web_tmux.sh restart
./scripts/kimodo_web_tmux.sh stop
```

## Current Artifacts

- CLI output: `/root/Project/Kimodo/output/test_walk.npz`
- G1 CLI output: `/root/Project/Kimodo/output/test_walk_g1.npz`
- Detached tmux launcher: `/root/Project/Kimodo/kimodo/scripts/kimodo_web_tmux.sh`
- Detached tmux env file: `/root/Project/Kimodo/kimodo/scripts/kimodo_web.env`
- Local source clone: `/root/Project/Kimodo/kimodo`
- Runtime package environment: `/root/miniforge3/envs/kimodo`

## Current Environment Summary

- OS: Ubuntu 20.04.3 LTS (WSL2)
- Python: 3.10.20
- PyTorch: 2.11.0+cu128
- CUDA available: yes
- Install route: Miniforge + conda
- HF token configured: yes
- Demo launch: success
- Text encoder launch: success
- localhost:7860 reachable: yes
- localhost:9550 reachable: yes
- Model auto-download: success

## Recommended Next Action

Use the detached tmux launcher for all future service starts:

```bash
cd /root/Project/Kimodo/kimodo
./scripts/kimodo_web_tmux.sh start
```
