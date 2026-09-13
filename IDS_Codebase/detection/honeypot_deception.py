from __future__ import annotations

from typing import Dict, Any, List

class HoneypotDeceptionEngine:
    """
    Automated Deception Sensor Node Engine.
    Deploys virtual decoy sensor topics (e.g., 'sensor/Decoy_Node_99') to attract,
    log, and flag unauthorized adversary probing and brute-force attempts.
    """
    def __init__(self, decoy_topics: List[str] | None = None) -> None:
        self.decoy_topics = set(decoy_topics or ["sensor/Decoy_Node_99", "sensor/Thermostat_Admin"])
        self.probe_events: List[Dict[str, Any]] = []

    def inspect_topic_access(self, topic: str, source_ip: str, payload: str, timestamp: str) -> dict | None:
        if topic in self.decoy_topics:
            event = {
                "alert": "🚨 Honeypot Deception Probe Detected!",
                "decoy_topic": topic,
                "attacker_ip": source_ip,
                "payload": payload,
                "timestamp": timestamp,
                "action": "FLAGGED_CRITICAL_PROBE"
            }
            self.probe_events.append(event)
            print(f"🪤 [Honeypot Triggered] Attacker '{source_ip}' probed decoy topic '{topic}'!")
            return event
        return None
