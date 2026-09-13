from __future__ import annotations

import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger("OpenTelemetryExporter")

class OpenTelemetryExporter:
    """
    Pillar 6: SRE Observability & OpenTelemetry (OTel) Metrics Collector.
    Tracks Service Level Indicators (SLIs) including inference latency distributions,
    edge CPU / memory utilization, and active intrusion alerts for Grafana / Datadog dashboards.
    """
    def __init__(self, service_name: str = "iot-ids-edge-engine") -> None:
        self.service_name = service_name
        self.spans: List[Dict[str, Any]] = []
        self.metrics_counter: Dict[str, int] = {}

    def start_span(self, name: str) -> Dict[str, Any]:
        span = {
            "name": name,
            "service": self.service_name,
            "start_time": time.perf_counter(),
            "attributes": {}
        }
        return span

    def end_span(self, span: Dict[str, Any], status: str = "OK") -> float:
        duration_ms = (time.perf_counter() - span["start_time"]) * 1000.0
        span["duration_ms"] = duration_ms
        span["status"] = status
        self.spans.append(span)
        logger.info(f"📊 [OTel Span] {span['name']} completed in {duration_ms:.4f} ms (Status: {status})")
        return duration_ms

    def record_count(self, metric_name: str, count: int = 1) -> None:
        self.metrics_counter[metric_name] = self.metrics_counter.get(metric_name, 0) + count

    def generate_otel_json(self) -> Dict[str, Any]:
        return {
            "resource": {"service.name": self.service_name},
            "metrics": self.metrics_counter,
            "spans_recorded": len(self.spans)
        }
