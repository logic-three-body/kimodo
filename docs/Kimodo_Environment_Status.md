# Kimodo Environment Status

Updated: 2026-03-29

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
- Install style: package install for runtime, local clone kept separately for source reading/editing
- Recommended runtime env var on this machine: `HF_HUB_DISABLE_XET=1`

## Important Note About Runtime vs. Clone

The current CLI commands are coming from the installed package in:

`/root/miniforge3/envs/kimodo/lib/python3.10/site-packages/kimodo/__init__.py`

The local git clone under `/root/Project/Kimodo/kimodo` is available for source reading and later development, but it is not the package currently driving `kimodo_gen` / `kimodo_demo`.

If you want the local clone to become the active runtime code later, reinstall from the clone explicitly, for example:

```bash
source /root/miniforge3/etc/profile.d/conda.sh
conda activate kimodo
python -m pip install -e /root/Project/Kimodo/kimodo
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
- `test_walk.npz` contains:
  - `local_rot_mats`: `(150, 77, 3, 3)`
  - `global_rot_mats`: `(150, 77, 3, 3)`
  - `posed_joints`: `(150, 77, 3)`
  - `root_positions`: `(150, 3)`
  - `smooth_root_pos`: `(150, 3)`
  - `foot_contacts`: `(150, 4)`
  - `global_root_heading`: `(150, 2)`
- `kimodo_demo --model Kimodo-SOMA-RP-v1` loads successfully.
- After the first-time `viser` frontend build completes, `http://127.0.0.1:7860/` and `http://localhost:7860/` return `HTTP 200 OK`.

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

To keep the `kimodo_demo` and `kimodo_textencoder` services running in the background persistently (even when SSH disconnects), use `tmux`.

**A. Always Check Existing Sessions First**
Before starting, always check if the environment is already running to avoid port conflicts and OOM errors:
```bash
tmux ls
```
If you see a session named `kimodo_web` listed, simply reattach to it instead of starting a new one:
```bash
tmux attach -t kimodo_web
```

**B. Create a New Session**
If no session exists, create one:
```bash
tmux new -s kimodo_web
```

**C. Start the Services**
Inside the Tmux window, it is recommended to split the screen (press `Ctrl+b` then `%` or `"`) and run each component:

*   **Pane 1 (Text Encoder):**
    ```bash
    source /root/miniforge3/etc/profile.d/conda.sh
    conda activate kimodo
    kimodo_textencoder
    ```
*   **Pane 2 (Demo):** Wait for Pane 1 to finish loading the model, then:
    ```bash
    source /root/miniforge3/etc/profile.d/conda.sh
    conda activate kimodo
    export HF_HUB_DISABLE_XET=1
    kimodo_demo --model Kimodo-SOMA-RP-v1
    ```

**D. Detach**
When everything is running smoothly, press `Ctrl+b` and release, then `d` to detach. The processes will continue safely in the background. If a process hangs, you can forcefully kill the session with `tmux kill-session -t kimodo_web`. 

## Current Artifacts

- CLI output: `/root/Project/Kimodo/output/test_walk.npz`
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
- localhost:7860 reachable: yes
- Model auto-download: success

## Recommended Next Action

If you want the local clone under `/root/Project/Kimodo/kimodo` to become the active runtime code for development, reinstall it in editable mode and then re-run one CLI sanity check:

```bash
source /root/miniforge3/etc/profile.d/conda.sh
conda activate kimodo
python -m pip install -e /root/Project/Kimodo/kimodo
kimodo_gen --help
```
