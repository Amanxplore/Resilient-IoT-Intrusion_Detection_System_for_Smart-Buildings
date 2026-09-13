from __future__ import annotations

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("ModbusDPIParser")

class ModbusDPIParser:
    """
    Pillar 2: Industrial Modbus TCP Deep Packet Inspector (DPI).
    Inspects Modbus TCP MBAP headers and PDU function codes (FC03 Read Holding Registers,
    FC06 Write Single Register, FC16 Write Multiple Registers) to detect out-of-bounds register tampering.
    """
    FUNCTION_CODES = {
        3: "Read Holding Registers",
        6: "Write Single Register",
        16: "Write Multiple Registers"
    }

    # Safe physical boundaries for HVAC damper registers
    SAFE_REGISTER_RANGES = {
        40001: (15.0, 30.0), # Temperature Setpoint Register (°C)
        40002: (20.0, 80.0), # Humidity Threshold Register (%)
        40003: (0.0, 100.0)  # VAV Damper Position (%)
    }

    def inspect_modbus_frame(
        self,
        unit_id: int,
        function_code: int,
        register_address: int,
        register_value: float
    ) -> Tuple[bool, str]:
        if function_code not in self.FUNCTION_CODES:
            msg = f"⚠️ [Modbus DPI Alert] Unsupported/Anomalous Function Code FC{function_code} targeting Unit {unit_id}!"
            logger.warning(msg)
            return False, msg

        if register_address in self.SAFE_REGISTER_RANGES:
            min_val, max_val = self.SAFE_REGISTER_RANGES[register_address]
            if not (min_val <= register_value <= max_val):
                msg = (
                    f"🚨 [Modbus DPI Intrusion] Out-of-bounds Register Write! "
                    f"Unit {unit_id} Register {register_address} = {register_value} "
                    f"(Safe Range: [{min_val}, {max_val}])"
                )
                logger.warning(msg)
                return False, msg

        logger.info(f"✅ [Modbus DPI Pass] Valid FC{function_code} ({self.FUNCTION_CODES[function_code]}) targeting Unit {unit_id}")
        return True, "Valid Modbus Payload"
