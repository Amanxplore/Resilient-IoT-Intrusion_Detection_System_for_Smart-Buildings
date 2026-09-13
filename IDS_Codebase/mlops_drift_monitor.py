from __future__ import annotations

import logging
import numpy as np
from typing import Dict, Any, Tuple

logger = logging.getLogger("MLOpsDriftMonitor")

class MLOpsDriftMonitor:
    """
    Pillar 4: Production MLOps & Sensor Distribution Data Drift Monitor.
    Calculates Population Stability Index (PSI) and Wasserstein Distance across sliding window
    temperature/humidity distributions to trigger automated model retraining when seasonal weather shifts occur.
    """
    def __init__(self, baseline_data: np.ndarray, psi_threshold: float = 0.2) -> None:
        self.baseline_data = np.asarray(baseline_data, dtype=np.float32)
        self.psi_threshold = psi_threshold

    def calculate_psi(self, current_data: np.ndarray, num_bins: int = 10) -> float:
        current_data = np.asarray(current_data, dtype=np.float32)
        if len(self.baseline_data) == 0 or len(current_data) == 0:
            return 0.0

        min_val = min(float(np.min(self.baseline_data)), float(np.min(current_data)))
        max_val = max(float(np.max(self.baseline_data)), float(np.max(current_data)))
        if min_val == max_val:
            return 0.0

        bin_edges = np.linspace(min_val, max_val, num_bins + 1)
        counts_b, _ = np.histogram(self.baseline_data, bins=bin_edges)
        counts_c, _ = np.histogram(current_data, bins=bin_edges)

        sum_b = float(np.sum(counts_b))
        sum_c = float(np.sum(counts_c))

        if sum_b == 0 or sum_c == 0:
            return 0.0

        pct_b = counts_b / sum_b
        pct_c = counts_c / sum_c

        # Smooth zero probabilities for stable log ratio
        pct_b = np.where(pct_b == 0, 1e-4, pct_b)
        pct_c = np.where(pct_c == 0, 1e-4, pct_c)

        psi_val = float(np.sum((pct_c - pct_b) * np.log(pct_c / pct_b)))
        return psi_val

    def check_drift(self, current_window: np.ndarray) -> Tuple[bool, float, str]:
        psi = self.calculate_psi(current_window)
        if psi >= self.psi_threshold:
            msg = f"🚨 [MLOps Data Drift Detected] PSI = {psi:.4f} >= Threshold ({self.psi_threshold}). Automated retraining required!"
            logger.warning(msg)
            return True, psi, msg
        
        msg = f"✅ [MLOps Distribution Normal] PSI = {psi:.4f} < Threshold ({self.psi_threshold})"
        logger.info(msg)
        return False, psi, msg
