from __future__ import annotations

import time
from typing import Dict, Any

class PrometheusMetricsExporter:
    """
    Exposes system detection statistics, reconstruction loss metrics, and alert counts
    formatted according to Prometheus text exposition standards.
    """
    def __init__(self) -> None:
        self.total_windows = 0
        self.attack_counts: Dict[str, int] = {
            "Normal": 0,
            "Drift Attack": 0,
            "Injection Attack": 0,
            "Noise Attack": 0,
            "Replay Attack": 0,
            "Drop Attack": 0
        }
        self.decision_sources: Dict[str, int] = {
            "rule_engine": 0,
            "ensemble_voting_consensus": 0,
            "ensemble_rf": 0,
            "ensemble_gb": 0,
            "feedback_memory": 0,
            "default": 0
        }

    def record_detection(self, label: str, source: str) -> None:
        self.total_windows += 1
        if label in self.attack_counts:
            self.attack_counts[label] += 1
        else:
            self.attack_counts[label] = 1

        if source in self.decision_sources:
            self.decision_sources[source] += 1
        else:
            self.decision_sources[source] = 1

    def generate_prometheus_metrics(self) -> str:
        lines = [
            "# HELP iot_ids_windows_total Total processed sensor window sequences",
            "# TYPE iot_ids_windows_total counter",
            f"iot_ids_windows_total {self.total_windows}",
            "",
            "# HELP iot_ids_attacks_total Total attacks detected by classification label",
            "# TYPE iot_ids_attacks_total counter"
        ]
        for attack_type, count in self.attack_counts.items():
            safe_type = attack_type.lower().replace(" ", "_")
            lines.append(f'iot_ids_attacks_total{{type="{safe_type}"}} {count}')

        lines.extend([
            "",
            "# HELP iot_ids_decision_sources_total Total decisions grouped by engine source",
            "# TYPE iot_ids_decision_sources_total counter"
        ])
        for src, count in self.decision_sources.items():
            lines.append(f'iot_ids_decision_sources_total{{source="{src}"}} {count}')

        lines.append("")
        return "\n".join(lines)
