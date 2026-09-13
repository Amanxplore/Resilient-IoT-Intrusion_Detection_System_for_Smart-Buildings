from __future__ import annotations

import os
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("TFLiteQuantizer")

class EdgeModelExporter:
    """
    Pillar 1: Edge Model Exporter & Int8 Quantization Pipeline.
    Exports PyTorch LSTM Autoencoder model to ONNX format and prepares
    fake int8 / float16 quantized representations for microcontroller (ESP32 / STM32) compilation.
    """
    def __init__(self, model: nn.Module, timesteps: int, n_features: int) -> None:
        self.model = model
        self.timesteps = timesteps
        self.n_features = n_features

    def export_onnx(self, filepath: str = "models/lstm_autoencoder.onnx") -> str:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.eval()
        dummy_input = torch.randn(1, self.timesteps, self.n_features, dtype=torch.float32)
        try:
            torch.onnx.export(
                self.model,
                dummy_input,
                filepath,
                export_params=True,
                opset_version=14,
                do_constant_folding=True,
                input_names=["sequence_input"],
                output_names=["reconstruction_output"],
                dynamic_axes={"sequence_input": {0: "batch_size"}, "reconstruction_output": {0: "batch_size"}},
            )
            logger.info(f"⚡ [ONNX Export] Successfully exported ONNX model to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export ONNX model: {e}")
            raise

    def quantize_int8_weights(self, scale: float = 0.0039, zero_point: int = 128) -> Dict[str, np.ndarray]:
        """
        Simulates 8-bit integer post-training quantization (PTQ) for microcontrollers.
        Quantizes floating-point weights W_float -> W_int8 = round(W_float / scale) + zero_point.
        """
        quantized_weights: Dict[str, np.ndarray] = {}
        for name, param in self.model.named_parameters():
            tensor = param.detach().cpu().numpy()
            q_tensor = np.clip(np.round(tensor / scale) + zero_point, 0, 255).astype(np.uint8)
            quantized_weights[name] = q_tensor
        logger.info(f"🔬 [Int8 Quantization] Quantized {len(quantized_weights)} model weight tensors for MCU execution.")
        return quantized_weights
