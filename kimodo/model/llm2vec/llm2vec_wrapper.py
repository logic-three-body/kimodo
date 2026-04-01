# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
"""LLM2Vec encoder wrapper for Kimodo text conditioning."""

import os

import numpy as np
import torch

from .llm2vec import LLM2Vec


class LLM2VecEncoder:
    """LLM2Vec text embeddings."""

    def __init__(
        self,
        base_model_name_or_path: str,
        peft_model_name_or_path: str,
        dtype: str,
        llm_dim: int,
    ) -> None:
        torch_dtype = getattr(torch, dtype)
        self.llm_dim = llm_dim

        cache_dir = os.environ.get("HUGGINGFACE_CACHE_DIR")

        if "TEXT_ENCODERS_DIR" in os.environ:
            base_model_name_or_path = os.path.join(os.environ["TEXT_ENCODERS_DIR"], base_model_name_or_path)
            peft_model_name_or_path = os.path.join(os.environ["TEXT_ENCODERS_DIR"], peft_model_name_or_path)

        self.model = LLM2Vec.from_pretrained(
            base_model_name_or_path=base_model_name_or_path,
            peft_model_name_or_path=peft_model_name_or_path,
            torch_dtype=torch_dtype,
            cache_dir=cache_dir,
        )
        self._target_device = self.model.model.device
        self.model.eval()
        for p in self.model.parameters():
            p.requires_grad = False

    def to(self, device: torch.device | str | None = None, dtype=None, eager: bool = False):
        if device is not None:
            self._target_device = torch.device(device)
        if dtype is not None:
            self.model = self.model.to(dtype=dtype)
        if eager and device is not None:
            self.model = self.model.to(self._target_device)
        return self

    def eval(self):
        self.model.eval()
        return self

    def get_device(self):
        return self._target_device

    def __call__(self, text: list[str] | str):
        is_string = False
        if isinstance(text, str):
            text = [text]
            is_string = True

        target_device = self.get_device()
        with torch.no_grad():
            encoded_text = self.model.encode(
                text,
                batch_size=len(text),
                show_progress_bar=False,
                device=str(target_device),
            )

        assert len(encoded_text.shape)
        assert self.llm_dim == encoded_text.shape[-1]

        encoded_text = encoded_text[:, None]
        lengths = np.ones(len(encoded_text), dtype=int).tolist()

        if is_string:
            encoded_text = encoded_text[0]
            lengths = lengths[0]

        if torch.is_tensor(encoded_text):
            encoded_text = encoded_text.detach().clone()
        else:
            encoded_text = torch.as_tensor(encoded_text)

        encoded_text = encoded_text.to(target_device)
        return encoded_text, lengths
