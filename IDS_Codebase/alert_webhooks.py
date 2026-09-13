from __future__ import annotations

import json
import urllib.request
from typing import Dict, Any, Optional

class AlertWebhookEngine:
    """
    Dispatches automated webhook alerts (Slack, PagerDuty, Discord, Custom Webhooks)
    when high-confidence intrusion events occur.
    """
    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url
        self.alert_history: list[dict] = []

    def trigger_alert(self, attack_type: str, source: str, confidence: str, timestamp: str, metadata: Optional[Dict[str, Any]] = None) -> dict:
        alert_payload = {
            "title": f"🚨 High-Confidence Intrusion Detected: {attack_type}",
            "text": f"*Attack:* {attack_type}\n*Sensor Node:* {source}\n*Confidence:* {confidence}\n*Timestamp:* {timestamp}",
            "attack_type": attack_type,
            "source_sensor": source,
            "confidence": confidence,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        self.alert_history.append(alert_payload)

        if self.webhook_url:
            try:
                data = json.dumps(alert_payload).encode("utf-8")
                req = urllib.request.Request(self.webhook_url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    print(f"Webhook alert dispatched to {self.webhook_url} (HTTP {resp.status})")
            except Exception as e:
                print(f"Warning: Failed to dispatch webhook alert: {e}")

        return alert_payload
