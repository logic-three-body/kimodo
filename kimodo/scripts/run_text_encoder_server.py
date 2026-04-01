# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import argparse
import os
import threading

import gradio as gr
import numpy as np
import torch

from kimodo.model import resolve_target

from .gradio_theme import get_gradio_theme

os.environ["HF_ENABLE_PARALLEL_LOADING"] = "YES"
DEFAULT_TEXT = "A person walks and falls to the ground."
DEFAULT_SERVER_NAME = "0.0.0.0"
DEFAULT_SERVER_PORT = 9550
DEFAULT_TMP_FOLDER = "/tmp/text_encoder/"
DEFAULT_TEXT_ENCODER = "llm2vec"
DEFAULT_TEXT_ENCODER_DEVICE = "auto"
TEXT_ENCODER_PRESETS = {
    "llm2vec": {
        "target": "kimodo.model.LLM2VecEncoder",
        "kwargs": {
            "base_model_name_or_path": "McGill-NLP/LLM2Vec-Meta-Llama-3-8B-Instruct-mntp",
            "peft_model_name_or_path": "McGill-NLP/LLM2Vec-Meta-Llama-3-8B-Instruct-mntp-supervised",
            "dtype": "bfloat16",
            "llm_dim": 4096,
        },
        "display_name": "LLM2Vec",
    }
}


class DemoWrapper:
    def __init__(self, text_encoder, tmp_folder, embedding_dim: int):
        self.text_encoder = text_encoder
        self.tmp_folder = tmp_folder
        self.embedding_dim = embedding_dim

    def __call__(self, text, filename, progress=gr.Progress()):
        if text.strip() == "healthcheck":
            embedding = np.zeros((1, self.embedding_dim), dtype=np.float32)
        else:
            # Compute text embedding
            tensor, length = self.text_encoder(text)
            embedding = tensor[:length].detach().cpu().numpy()

        # Save text embedding
        path = os.path.join(self.tmp_folder, filename)
        np.save(path, embedding)

        output_title = gr.Markdown(visible=True)
        output_text = gr.Markdown(visible=True, value=f"Text: {text}")
        download = gr.DownloadButton(visible=True, value=path)
        return download, output_title, output_text


def _get_env(name: str, default):
    return os.getenv(name, default)


def _build_text_encoder(name: str):
    if name not in TEXT_ENCODER_PRESETS:
        available = ", ".join(sorted(TEXT_ENCODER_PRESETS))
        raise ValueError(f"Unknown TEXT_ENCODER='{name}'. Available: {available}")
    preset = TEXT_ENCODER_PRESETS[name]
    target_cls = resolve_target(preset["target"])
    return target_cls(**preset["kwargs"])


class LazyTextEncoder:
    def __init__(self, name: str, device_name: str):
        self.name = name
        self.device_name = device_name
        self._encoder = None
        self._lock = threading.Lock()

    def _get_encoder(self):
        if self._encoder is not None:
            return self._encoder

        with self._lock:
            if self._encoder is None:
                encoder = _build_text_encoder(self.name)
                if hasattr(encoder, "to"):
                    encoder.to(device=self.device_name)
                if hasattr(encoder, "eval"):
                    encoder.eval()
                self._encoder = encoder
                print(f"Initialized text encoder on device: {self.device_name}")

        return self._encoder

    def __call__(self, text):
        return self._get_encoder()(text)


def _resolve_device(device_name: str) -> str:
    device_name = (device_name or DEFAULT_TEXT_ENCODER_DEVICE).strip().lower()
    if device_name == "auto":
        return "cuda:0" if torch.cuda.is_available() else "cpu"

    try:
        device = torch.device(device_name)
    except (TypeError, RuntimeError, ValueError) as exc:
        raise ValueError(f"Invalid TEXT_ENCODER device {device_name!r}.") from exc

    if device.type == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("TEXT_ENCODER device is CUDA, but torch.cuda.is_available() is False.")
        device_index = 0 if device.index is None else device.index
        if device_index >= torch.cuda.device_count():
            raise ValueError(
                f"CUDA device index {device_index} is out of range for {torch.cuda.device_count()} visible device(s)."
            )
        return f"cuda:{device_index}"

    return str(device)


def parse_args():
    parser = argparse.ArgumentParser(description="Run text encoder Gradio server.")
    parser.add_argument(
        "--text-encoder",
        default=_get_env("TEXT_ENCODER", DEFAULT_TEXT_ENCODER),
        choices=sorted(TEXT_ENCODER_PRESETS.keys()),
        help="Text encoder preset.",
    )
    parser.add_argument(
        "--tmp-folder",
        default=_get_env("TEXT_ENCODER_TMP_FOLDER", DEFAULT_TMP_FOLDER),
    )
    parser.add_argument(
        "--device",
        default=_get_env("TEXT_ENCODER_DEVICE", DEFAULT_TEXT_ENCODER_DEVICE),
        help="Torch device for the text encoder (auto, cpu, cuda:0, ...).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    server_name = _get_env("GRADIO_SERVER_NAME", DEFAULT_SERVER_NAME)
    server_port = int(_get_env("GRADIO_SERVER_PORT", DEFAULT_SERVER_PORT))
    text_encoder_device = _resolve_device(args.device)
    theme, css = get_gradio_theme()
    os.makedirs(args.tmp_folder, exist_ok=True)
    text_encoder = LazyTextEncoder(args.text_encoder, text_encoder_device)
    print(f"Configured text encoder device: {text_encoder_device}")
    display_name = TEXT_ENCODER_PRESETS[args.text_encoder]["display_name"]
    demo_wrapper_fn = DemoWrapper(
        text_encoder,
        args.tmp_folder,
        embedding_dim=TEXT_ENCODER_PRESETS[args.text_encoder]["kwargs"]["llm_dim"],
    )

    with gr.Blocks(title="Text encoder") as demo:
        gr.Markdown(f"# Text encoder: {display_name}")
        gr.Markdown("## Description")
        gr.Markdown("Get a embeddings from a text.")

        gr.Markdown("## Inputs")
        with gr.Row():
            text = gr.Textbox(
                placeholder="Type the motion you want to generate with a sentence",
                show_label=True,
                label="Text prompt",
                value=DEFAULT_TEXT,
                type="text",
            )
        with gr.Row(scale=3):
            with gr.Column(scale=1):
                btn = gr.Button("Encode", variant="primary")
            with gr.Column(scale=1):
                clear = gr.Button("Clear", variant="secondary")
            with gr.Column(scale=3):
                pass

        output_title = gr.Markdown("## Outputs", visible=False)
        output_text = gr.Markdown("", visible=False)
        with gr.Row(scale=3):
            with gr.Column(scale=1):
                download = gr.DownloadButton("Download", variant="primary", visible=False)
            with gr.Column(scale=4):
                pass

        filename = gr.Textbox(
            visible=False,
            value="embedding.npy",
        )

        def clear_fn():
            return [
                gr.DownloadButton(visible=False),
                gr.Markdown(visible=False),
                gr.Markdown(visible=False),
            ]

        outputs = [download, output_title, output_text]

        gr.on(
            triggers=[text.submit, btn.click],
            fn=clear_fn,
            inputs=None,
            outputs=outputs,
        ).then(
            fn=demo_wrapper_fn,
            inputs=[text, filename],
            outputs=outputs,
        )

        def download_file():
            return gr.DownloadButton()

        download.click(
            fn=download_file,
            inputs=None,
            outputs=[download],
        )
        clear.click(fn=clear_fn, inputs=None, outputs=outputs)

    demo.queue(default_concurrency_limit=1)
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        theme=theme,
        css=css,
    )


if __name__ == "__main__":
    main()
