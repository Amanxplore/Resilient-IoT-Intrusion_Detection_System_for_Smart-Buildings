from __future__ import annotations

import math
import numpy as np
import pandas as pd

class DiurnalBaselineScaler:
    """
    Diurnal Solar Baseline Scaler.
    Models expected daytime heating / nighttime cooling sinusoidal temperature curves
    to dynamically adjust anomaly thresholds based on ambient time-of-day.
    """
    def __init__(self, base_temp: float = 22.0, amplitude: float = 4.0, peak_hour: float = 14.0) -> None:
        self.base_temp = base_temp
        self.amplitude = amplitude
        self.peak_hour = peak_hour

    def compute_expected_ambient(self, timestamp: pd.Timestamp) -> float:
        hour = timestamp.hour + (timestamp.minute / 60.0) + (timestamp.second / 3600.0)
        # Sinusoidal diurnal model peaking at 14:00 (2 PM)
        angle = (hour - self.peak_hour + 6.0) * (2.0 * math.pi / 24.0)
        expected = self.base_temp + self.amplitude * math.sin(angle)
        return float(expected)

    def adjust_threshold(self, base_threshold: float, current_temp: float, timestamp: pd.Timestamp) -> float:
        expected = self.compute_expected_ambient(timestamp)
        deviation = abs(current_temp - expected)
        # Scale threshold dynamically if deviation aligns with expected solar diurnal curve
        if deviation > 5.0:
            return base_threshold * 0.95  # Slightly tighter threshold during high ambient variance
        return base_threshold
