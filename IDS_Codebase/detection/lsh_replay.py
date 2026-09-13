from __future__ import annotations

import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple

class LSHReplayDetector:
    """
    Locality-Sensitive Hashing (LSH) Replay Detector for $O(1)$ time-series signature lookup.
    Quantizes temporal window signals into discrete hash buckets to identify historical replay attacks.
    """
    def __init__(self, num_bands: int = 4, num_features: int = 30, bin_size: float = 0.5) -> None:
        self.num_bands = num_bands
        self.num_features = num_features
        self.bin_size = bin_size
        self.buckets: Dict[str, List[Tuple[int, np.ndarray]]] = {}

    def _quantize_sequence(self, sequence: np.ndarray) -> np.ndarray:
        flattened = np.asarray(sequence, dtype=np.float32).reshape(-1)
        return np.floor(flattened / self.bin_size).astype(int)

    def _get_band_hashes(self, quantized: np.ndarray) -> List[str]:
        hashes = []
        chunks = np.array_split(quantized, self.num_bands)
        for chunk in chunks:
            h = hashlib.sha256(chunk.tobytes()).hexdigest()[:16]
            hashes.append(h)
        return hashes

    def insert(self, history_index: int, sequence: np.ndarray) -> None:
        quantized = self._quantize_sequence(sequence)
        hashes = self._get_band_hashes(quantized)
        for band_idx, h in enumerate(hashes):
            key = f"{band_idx}_{h}"
            if key not in self.buckets:
                self.buckets[key] = []
            self.buckets[key].append((history_index, sequence.copy()))

    def query(self, sequence: np.ndarray, similarity_threshold: float = 0.9) -> Tuple[bool, Optional[float], Optional[int]]:
        quantized = self._quantize_sequence(sequence)
        hashes = self._get_band_hashes(quantized)
        candidates: List[Tuple[int, np.ndarray]] = []
        
        for band_idx, h in enumerate(hashes):
            key = f"{band_idx}_{h}"
            if key in self.buckets:
                candidates.extend(self.buckets[key])
                
        if not candidates:
            return False, None, None

        s1 = np.asarray(sequence, dtype=np.float32).reshape(-1)
        s1_std = np.std(s1)
        if s1_std == 0:
            return False, None, None
        s1_norm = (s1 - np.mean(s1)) / s1_std

        best_sim = -1.0
        best_index = None

        for hist_idx, candidate_seq in candidates:
            s2 = candidate_seq.reshape(-1)
            s2_std = np.std(s2)
            if s2_std == 0:
                continue
            s2_norm = (s2 - np.mean(s2)) / s2_std
            sim = float(np.corrcoef(s1_norm, s2_norm)[0, 1])
            if sim > best_sim:
                best_sim = sim
                best_index = hist_idx

        if best_sim >= similarity_threshold:
            return True, best_sim, best_index

        return False, float(best_sim) if best_sim >= 0 else None, None
