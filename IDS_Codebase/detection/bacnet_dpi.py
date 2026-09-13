from __future__ import annotations

from typing import Dict, Any, Tuple

class BACnetDPIParser:
    """
    Deep Packet Inspection (DPI) parser for BACnet/SC (ASHRAE 135) APDUs.
    Validates Property Write requests targeting HVAC temperature and humidity setpoints.
    """
    def __init__(self) -> None:
        self.min_temp_setpoint = 10.0  # °C
        self.max_temp_setpoint = 35.0  # °C
        self.inspected_packets_count = 0

    def inspect_apdu(self, apdu_bytes: bytes) -> Tuple[bool, str]:
        self.inspected_packets_count += 1
        # Simulated BACnet/SC APDU inspection logic
        if len(apdu_bytes) < 4:
            return False, "Malformed APDU header (length < 4)"

        # Check BACnet PDU type (0x00 = Confirmed-Request PDU)
        pdu_type = (apdu_bytes[0] >> 4) & 0x0F
        if pdu_type == 0x00:
            service_choice = apdu_bytes[1]
            # Service Choice 15 = WriteProperty
            if service_choice == 15:
                return True, "Valid WriteProperty APDU"

        return True, "Valid BACnet APDU"

    def validate_setpoint(self, setpoint_value: float) -> Tuple[bool, str]:
        if setpoint_value < self.min_temp_setpoint or setpoint_value > self.max_temp_setpoint:
            return False, f"Malicious HVAC Setpoint Write: {setpoint_value}°C out of bounds ({self.min_temp_setpoint}-{self.max_temp_setpoint}°C)"
        return True, "Setpoint within safe operational bounds"
