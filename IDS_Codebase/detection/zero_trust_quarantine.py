from __future__ import annotations

from typing import Set, Dict, List

class ZeroTrustQuarantineEngine:
    """
    Automated Zero-Trust Isolation Engine that tracks compromised edge sensor nodes
    and generates firewall block rules (iptables / OpenFlow SDN) to isolate them upon intrusion detection.
    """
    def __init__(self) -> None:
        self.quarantined_sensors: Set[str] = set()
        self.isolation_log: List[Dict[str, str]] = []

    def quarantine_sensor(self, sensor_id: str, reason: str, timestamp: str) -> dict:
        self.quarantined_sensors.add(sensor_id)
        record = {
            "sensor_id": sensor_id,
            "reason": reason,
            "timestamp": timestamp,
            "iptables_rule": f"sudo iptables -A INPUT -s {sensor_id} -j DROP",
            "sdn_action": f"FLOW_MOD: DROP src={sensor_id}"
        }
        self.isolation_log.append(record)
        print(f"🔒 [Zero-Trust Quarantine] Isolated sensor '{sensor_id}' due to {reason}.")
        return record

    def is_quarantined(self, sensor_id: str) -> bool:
        return sensor_id in self.quarantined_sensors

    def release_sensor(self, sensor_id: str) -> bool:
        if sensor_id in self.quarantined_sensors:
            self.quarantined_sensors.remove(sensor_id)
            print(f"🔓 [Zero-Trust Quarantine] Released sensor '{sensor_id}'.")
            return True
        return False
