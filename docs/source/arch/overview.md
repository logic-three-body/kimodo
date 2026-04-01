# Kimodo Architecture Overview

## Introduction

Kimodo is a system for scaling controllable human motion generation. The architecture is designed to support text-conditioned generation, interactive constraint-based control, and robust high-quality motion representation along with evaluation metrics and multiple export targets. 

## High-Level System Architecture

- **Model Framework:** A diffusion-based generative model using a two-stage denoising architecture with a transformer encoder backbone. It leverages a dedicated text encoder for natural language conditioning.
- **Motion Representation & Kinematics:** Abstracted skeleton definitions, forward kinematics, and customized motion representations that handle features such as foot contact smoothing and constraint condition integration.
- **Visualization & UI:** An interactive web demo built with Gradio and integrated with Viser for 3D timeline and playback rendering. It supports various skinning targets (SOMA, SMPL-X, G1 robot).
- **Post-Processing:** Options for motion correction logic (via a dedicated C++ module) to correct artifacts such as foot skate and ensure constraint satisfaction.

## Core Modules (`kimodo/`)

The main Python package (`kimodo/kimodo/`) is organized into the following functional domains:

- **`model/`**: Contains the model architectures, including the Kimodo diffusion wrapper, the two-stage denoiser, checking point loading, registry handling, and the LLM-based text encoder hook (`llm2vec`).
- **`motion_rep/`**: Handles the representation of skeletal motion. Provides logic for text and constraint conditioning, feature extraction, tracking footprint smoothing (`feet.py`), and computing normalization statistics.
- **`skeleton/`**: Centralized definitions for skeleton topologies, joint structures, basic forward kinematics operations, rotation/transform utilities, and BVH I/O processing.
- **`viz/`**: Provides rich 3D visualization and graphical user interfaces. Integrates `viser` for rendering 3D scenes, motion playback, coordinate frames, constraint editing, and various skinning forms (`soma_skin`, `smplx_skin`).
- **`demo/`**: Implements the user-facing interactive web application. It handles UI layout, application state, request queuing, and generation pipelines for the demo interface.
- **`exports/`**: Modules specifically for taking generated internal motion data and outputting to standard formats including BVH, MuJoCo routines, and SMPL-X parameterization.
- **`metrics/`**: Evaluation utilities primarily focusing on checking physical realism (like `foot_skate.py`) and constraint tracking methodologies.
- **`scripts/`**: Houses utility scripts and CLI runners, including text encoder server management and Docker entry points.
- **Root Utilities:** Scripts like `constraints.py`, `geometry.py`, `postprocess.py`, and `sanitize.py` handle generalized systemic tasks such as parsing structural constraints and geometry calculations.

## Auxiliary Components

- **`MotionCorrection/`**: A separately compiled sub-module containing C++ source code and Python bindings used for accelerated post-processing motion corrections to enhance the generated motion's physical validity.
- **Assets & Data**: Stored in `assets/` directories both at the repository root and package level, consisting of skeleton properties, demo configurations, and UI visuals.

## Entry Points

The system exposes several command-line tools (via `pyproject.toml`) for different pipelines:

1. **`kimodo_gen`** (`kimodo.scripts.generate:main`): A CLI tool for direct motion synthesis.
2. **`kimodo_demo`** (`kimodo.demo:main`): Launches the interactive Gradio/Viser-backed web demo.
3. **`kimodo_textencoder`** (`kimodo.scripts.run_text_encoder_server:main`): Starts the local LLM-based text encoder server for processing textual prompts.
