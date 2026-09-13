from __future__ import annotations

import math
import numpy as np
from typing import Dict, Any

class FastFeatureExtractor:
    """
    Pillar 1: High-Performance Zero-Copy Feature Extractor.
    Extracts statistical metrics (slope, std, range, entropy, jump, zscore)
    directly from raw NumPy arrays for sub-microsecond edge pipeline execution.
    """
    @staticmethod
    def extract_vector_features(temperatures: np.ndarray, humidities: np.ndarray) -> Dict[str, float]:
        n = len(temperatures)
        if n == 0:
            return {}

        # Temperature stats
        temp_mean = float(np.mean(temperatures))
        temp_std = float(np.std(temperatures))
        temp_min = float(np.min(temperatures))
        temp_max = float(np.max(temperatures))
        temp_range = temp_max - temp_min

        # Linear slope computation
        x = np.arange(n, dtype=np.float32)
        x_mean = (n - 1) / 2.0
        denom = float(np.sum((x - x_mean) ** 2))
        if denom > 0:
            temp_slope = float(np.sum((x - x_mean) * (temperatures - temp_mean)) / denom)
        else:
            temp_slope = 0.0

        # Max jump and Z-score
        deltas = np.abs(np.diff(temperatures)) if n > 1 else np.array([0.0])
        max_jump = float(np.max(deltas)) if len(deltas) > 0 else 0.0
        zscores = np.abs(temperatures - temp_mean) / (temp_std + 1e-6)
        zscore_max = float(np.max(zscores))

        # Fast Shannon entropy calculation
        hist, _ = np.histogram(temperatures, bins=min(10, max(2, n // 3)))
        probs = hist / np.sum(hist)
        probs = probs[probs > 0]
        temp_entropy = float(-np.sum(probs * np.log2(probs))) if len(probs) > 0 else 0.0

        # Humidity stats
        hum_mean = float(np.mean(humidities))
        hum_std = float(np.std(humidities))
        ratio = temp_mean / (hum_mean + 1e-5)

        return {
            "temp_30_slope": temp_slope,
            "temp_30_std": temp_std,
            "temp_30_range": temp_range,
            "temp_30_entropy": temp_entropy,
            "temp_10_max_jump": max_jump,
            "temp_10_zscore_max": zscore_max,
            "temp_hum_ratio": ratio,
        }
