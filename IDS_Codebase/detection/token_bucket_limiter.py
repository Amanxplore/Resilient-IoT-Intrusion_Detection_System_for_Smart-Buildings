from __future__ import annotations

import time
from typing import Dict

class TokenBucketRateLimiter:
    """
    Token-Bucket Rate Limiter for edge gateway interfaces.
    Throttles high-frequency packet floods and Denial of Service (DoS) attacks per sensor node.
    """
    def __init__(self, capacity: float = 20.0, fill_rate: float = 5.0) -> None:
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens: Dict[str, float] = {}
        self.last_update: Dict[str, float] = {}

    def allow_request(self, sensor_id: str, current_time: float | None = None) -> bool:
        now = current_time if current_time is not None else time.time()
        if sensor_id not in self.tokens:
            self.tokens[sensor_id] = self.capacity
            self.last_update[sensor_id] = now

        elapsed = max(0.0, now - self.last_update[sensor_id])
        self.tokens[sensor_id] = min(self.capacity, self.tokens[sensor_id] + elapsed * self.fill_rate)
        self.last_update[sensor_id] = now

        if self.tokens[sensor_id] >= 1.0:
            self.tokens[sensor_id] -= 1.0
            return True

        return False
