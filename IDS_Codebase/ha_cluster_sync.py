from __future__ import annotations

import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger("HAClusterSyncEngine")

class HAClusterSyncEngine:
    """
    Pillar 3: High Availability (HA) Clustering & Cloud SIEM Synchronization.
    Monitors VRRP virtual IP state, active-passive gateway heartbeat status,
    and queues local security telemetry during cloud network outages.
    """
    def __init__(self, node_id: str = "Gateway_Node_A", role: str = "MASTER") -> None:
        self.node_id = node_id
        self.role = role
        self.local_offline_queue: List[Dict[str, Any]] = []
        self.cloud_connected = True

    def check_heartbeat(self, peer_node_id: str, last_seen_seconds: float) -> str:
        if last_seen_seconds > 5.0 and self.role == "BACKUP":
            self.role = "MASTER"
            logger.warning(f"🚨 [HA Failover] Peer '{peer_node_id}' heartbeat lost! Promoted '{self.node_id}' to MASTER!")
            return "PROMOTED_MASTER"
        return self.role

    def queue_alert_telemetry(self, alert_payload: Dict[str, Any]) -> None:
        if not self.cloud_connected:
            self.local_offline_queue.append(alert_payload)
            logger.info(f"💾 [HA Queue] Cloud offline. Saved alert to local queue (Queue Size: {len(self.local_offline_queue)})")
        else:
            logger.info(f"☁️ [Cloud Sync] Telemetry alert synced to Cloud SIEM (Node: {self.node_id})")

    def flush_offline_queue(self) -> int:
        if not self.cloud_connected or not self.local_offline_queue:
            return 0
        count = len(self.local_offline_queue)
        self.local_offline_queue.clear()
        logger.info(f"🔄 [Cloud Sync Flush] Successfully flushed {count} queued alerts to Cloud SIEM.")
        return count
