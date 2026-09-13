from __future__ import annotations

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger("SnortRuleGenerator")

class SnortRuleGenerator:
    """
    Dynamic Snort 3 / Suricata Rule Generator.
    Automatically synthesizes network intrusion rules when ML ensembles detect novel attacks.
    """
    def __init__(self, start_sid: int = 3000000) -> None:
        self.current_sid = start_sid
        self.generated_rules: List[Dict[str, Any]] = []

    def generate_rule_from_attack(self, attack_type: str, source_ip: str, target_port: int = 1883) -> dict:
        self.current_sid += 1
        msg = f"[IoT IDS Dynamic Rule] {attack_type} Detected from {source_ip}"
        snort_string = (
            f'alert tcp {source_ip} any -> any {target_port} '
            f'(msg:"{msg}"; sid:{self.current_sid}; rev:1;)'
        )
        record = {
            "sid": self.current_sid,
            "attack_type": attack_type,
            "source_ip": source_ip,
            "target_port": target_port,
            "snort_rule": snort_string
        }
        self.generated_rules.append(record)
        logger.info(f"🛡️ [Snort Rule Generated] SID {self.current_sid}: {snort_string}")
        return record

    def export_rules_file(self, filepath: str = "Snort_Rules/dynamic_generated.rules") -> str:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        lines = [r["snort_rule"] for r in self.generated_rules]
        content = "# Dynamically Generated Snort 3 Rules\n" + "\n".join(lines) + "\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
